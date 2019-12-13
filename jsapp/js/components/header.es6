import $ from 'jquery';
import React from 'react';
import PropTypes from 'prop-types';
import reactMixin from 'react-mixin';
import autoBind from 'react-autobind';
import { hashHistory } from 'react-router';
import ui from '../ui';
import {stores} from '../stores';
import Reflux from 'reflux';
import {bem} from '../bem';
import {actions} from '../actions';
import mixins from '../mixins';
import {dataInterface} from '../dataInterface';
import {
  t,
  assign,
  currentLang,
  stringToColor,
} from 'js/utils';
import {getAssetIcon} from 'js/assetUtils';
import {COMMON_QUERIES} from 'js/constants';
import {searches} from '../searches';
import {ListSearch} from '../components/list';
import HeaderTitleEditor from 'js/components/header/headerTitleEditor';
import SearchBox from 'js/components/header/searchBox';
import myLibraryStore from 'js/components/library/myLibraryStore';

class MainHeader extends Reflux.Component {
  constructor(props){
    super(props);
    this.state = assign({
      asset: false,
      currentLang: currentLang(),
      isLanguageSelectorVisible: false,
      isSearchBoxDisabled: this.getIsSearchBoxDisabled(),
      libraryFiltersContext: searches.getSearchContext('library', {
        filterParams: {
          assetType: COMMON_QUERIES.get('qbt'),
        },
        filterTags: COMMON_QUERIES.get('qbt'),
      }),
      formFiltersContext: searches.getSearchContext('forms', {
        filterParams: {
          assetType: COMMON_QUERIES.get('s'),
        },
        filterTags: COMMON_QUERIES.get('s'),
      })
    }, stores.pageState.state);
    this.stores = [
      stores.session,
      stores.pageState
    ];
    autoBind(this);
  }
  componentDidMount() {
    document.body.classList.add('hide-edge');
    this.listenTo(stores.asset, this.assetLoad);
    this.listenTo(myLibraryStore, this.myLibraryStoreChanged);
  }
  componentWillUpdate(newProps) {
    if (this.props.assetid !== newProps.assetid) {
      this.setState({asset: false});
    }
  }
  myLibraryStoreChanged() {
    this.setState({
      isSearchBoxDisabled: this.getIsSearchBoxDisabled()
    });
  }
  getIsSearchBoxDisabled() {
    return myLibraryStore.data.totalUserAssets === null;
  }
  assetLoad(data) {
    const asset = data[this.props.assetid];
    this.setState(assign({asset: asset}));
  }
  logout () {
    actions.auth.logout();
  }
  toggleLanguageSelector() {
    this.setState({isLanguageSelectorVisible: !this.state.isLanguageSelectorVisible});
  }
  accountSettings () {
    // verifyLogin also refreshes stored profile data
    actions.auth.verifyLogin.triggerAsync().then(() => {
      hashHistory.push('account-settings');
    });
  }
  languageChange (evt) {
    evt.preventDefault();
    let langCode = $(evt.target).data('key');
    if (langCode) {
      // use .always (instead of .done) here since Django 1.8 redirects the request
      dataInterface.setLanguage({language: langCode}).always(() => {
        if ('reload' in window.location) {
          window.location.reload();
        } else {
          window.alert(t('Please refresh the page'));
        }
      });
    }
  }
  renderLangItem(lang) {
    return (
      <bem.AccountBox__menuLI key={lang.value}>
        <bem.AccountBox__menuLink onClick={this.languageChange} data-key={lang.value}>
          {lang.label}
        </bem.AccountBox__menuLink>
      </bem.AccountBox__menuLI>
    );
  }
  renderAccountNavMenu () {
    let langs = [];
    if (stores.session.environment) {
      langs = stores.session.environment.interface_languages;
    }
    if (stores.session.currentAccount) {
      var accountName = stores.session.currentAccount.username;
      var accountEmail = stores.session.currentAccount.email;

      var initialsStyle = {background: `#${stringToColor(accountName)}`};
      var accountMenuLabel = <bem.AccountBox__initials style={initialsStyle}>{accountName.charAt(0)}</bem.AccountBox__initials>;

      return (
        <bem.AccountBox>
          {/*<bem.AccountBox__notifications className="is-edge">
            <i className="fa fa-bell"></i>
            <bem.AccountBox__notifications__count> 2 </bem.AccountBox__notifications__count>
          </bem.AccountBox__notifications>*/}
          <ui.PopoverMenu type='account-menu'
                          triggerLabel={accountMenuLabel}
                          buttonType='text'>
              <bem.AccountBox__menu>
                <bem.AccountBox__menuLI key='1'>
                  <bem.AccountBox__menuItem m={'avatar'}>
                    {accountMenuLabel}
                  </bem.AccountBox__menuItem>
                  <bem.AccountBox__menuItem m={'mini-profile'}>
                    <span className='account-username'>{accountName}</span>
                    <span className='account-email'>{accountEmail}</span>
                  </bem.AccountBox__menuItem>
                  <bem.AccountBox__menuItem m={'settings'}>
                    <button onClick={this.accountSettings} className='mdl-button mdl-button--raised mdl-button--colored'>
                      {t('Account Settings')}
                    </button>
                  </bem.AccountBox__menuItem>
                </bem.AccountBox__menuLI>
                {stores.session && stores.session.environment &&
                  <bem.AccountBox__menuLI key='2' className='environment-links'>
                    <a href={stores.session.environment.terms_of_service_url} target='_blank'>
                      {t('Terms of Service')}
                    </a>
                    <a href={stores.session.environment.privacy_policy_url} target='_blank'>
                      {t('Privacy Policy')}
                    </a>
                  </bem.AccountBox__menuLI>
                }
                <bem.AccountBox__menuLI m={'lang'} key='3'>
                  <bem.AccountBox__menuLink onClick={this.toggleLanguageSelector} data-popover-menu-stop-blur tabIndex='0'>
                    <i className='k-icon-language' />
                    {t('Language')}
                  </bem.AccountBox__menuLink>

                  {this.state.isLanguageSelectorVisible &&
                    <ul>
                      {langs.map(this.renderLangItem)}
                    </ul>
                  }
                </bem.AccountBox__menuLI>
                <bem.AccountBox__menuLI m={'logout'} key='4'>
                  <bem.AccountBox__menuLink onClick={this.logout}>
                    <i className='k-icon-logout' />
                    {t('Logout')}
                  </bem.AccountBox__menuLink>
                </bem.AccountBox__menuLI>
              </bem.AccountBox__menu>
          </ui.PopoverMenu>
        </bem.AccountBox>
        );
    }

    return (
          <span>{t('n/a')}</span>
    );
  }
  renderGitRevInfo () {
    if (stores.session.currentAccount && stores.session.currentAccount.git_rev) {
      var gitRev = stores.session.currentAccount.git_rev;
      return (
        <bem.GitRev>
          <bem.GitRev__item>
            branch: {gitRev.branch}
          </bem.GitRev__item>
          <bem.GitRev__item>
            commit: {gitRev.short}
          </bem.GitRev__item>
        </bem.GitRev>
      );
    }

    return false;
  }
  toggleFixedDrawer() {
    stores.pageState.toggleFixedDrawer();
  }

  render() {
    let userCanEditAsset = false;
    if (this.state.asset) {
      userCanEditAsset = this.userCan('change_asset', this.state.asset);
    }

    let iconClassName = '';
    if (this.state.asset) {
      iconClassName = getAssetIcon(this.state.asset);
    }

    return (
        <bem.MainHeader className='mdl-layout__header'>
          <div className='mdl-layout__header-row'>
            <button className='mdl-button mdl-button--icon' onClick={this.toggleFixedDrawer}>
              <i className='fa fa-bars' />
            </button>
            <span className='mdl-layout-title'>
              <a href='/'>
                <bem.Header__logo />
              </a>
            </span>
            { this.isFormList() &&
              <div className='mdl-layout__header-searchers'>
                <ListSearch searchContext={this.state.formFiltersContext} placeholderText={t('Search Projects')} />
              </div>
            }
            { this.isLibraryList() &&
              <div className='mdl-layout__header-searchers'>
                <SearchBox
                  placeholder={t('Search Library')}
                  disabled={this.state.isSearchBoxDisabled}
                />
              </div>
            }
            { this.isLibrarySingle() && this.state.asset &&
              <React.Fragment>
                <bem.MainHeader__icon className={iconClassName} />

                <HeaderTitleEditor
                  uid={this.state.asset.uid}
                  type={this.state.asset.asset_type}
                  name={this.state.asset.name}
                  isEditable={userCanEditAsset}
                />
              </React.Fragment>
            }
            { this.isFormSingle() && this.state.asset &&
              <React.Fragment>
                <bem.MainHeader__icon className={iconClassName} />

                <HeaderTitleEditor
                  uid={this.state.asset.uid}
                  type={this.state.asset.asset_type}
                  name={this.state.asset.name}
                  isEditable={userCanEditAsset}
                />

                { this.state.asset.has_deployment &&
                  <bem.MainHeader__counter>
                    {this.state.asset.deployment__submission_count} {t('submissions')}
                  </bem.MainHeader__counter>
                }
              </React.Fragment>
            }
            {this.renderAccountNavMenu()}
          </div>
          {this.renderGitRevInfo()}
        </bem.MainHeader>
      );
  }
  componentWillReceiveProps(nextProps) {
    if (this.props.assetid !== nextProps.assetid && nextProps.assetid !== null) {
      actions.resources.loadAsset({id: nextProps.assetid});
    }
  }
}

reactMixin(MainHeader.prototype, Reflux.ListenerMixin);
reactMixin(MainHeader.prototype, mixins.contextRouter);
reactMixin(MainHeader.prototype, mixins.permissions);

MainHeader.contextTypes = {
  router: PropTypes.object
};

export default MainHeader;
