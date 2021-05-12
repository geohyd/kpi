import React from 'react';
import PropTypes from 'prop-types';
import reactMixin from 'react-mixin';
import autoBind from 'react-autobind';
import Reflux from 'reflux';
import {bem} from '../bem';
import {stores} from '../stores';
import { Link, hashHistory } from 'react-router';
import mixins from '../mixins';
import assetUtils from 'js/assetUtils';
import {
  PERMISSIONS_CODENAMES,
  ROUTES,
} from 'js/constants';
import {assign} from 'utils';

class FormViewTabs extends Reflux.Component {
  constructor(props){
    super(props);
    this.state = {};
    autoBind(this);
  }
  componentDidMount() {
    this.listenTo(stores.asset, this.assetLoad);
  }
  assetLoad(data) {
    var assetid = this.currentAssetID();
    var asset = data[assetid];
    this.setState(assign({
        asset: asset,
        assetid: assetid
      }
    ));
  }
  triggerRefresh (evt) {
    if ($(evt.target).hasClass('active')) {
      hashHistory.push(`/forms/${this.state.assetid}/reset`);

      var path = evt.target.getAttribute('data-path');
      window.setTimeout(function(){
        hashHistory.push(path);
      }, 50);

      evt.preventDefault();
    }
  }

  isDataTabEnabled() {
    console.log({
      dep_id: this.state.asset.deployment__identifier,
      has_dep: this.state.asset.has_deployment,
      count: this.state.asset.deployment__submission_count,
      can_view: this.userCan('view_submissions', this.state.asset),
      can_part: this.userCan('partial_submissions', this.state.asset),
    });
    return (
      this.state.asset.deployment__identifier != undefined &&
      this.state.asset.has_deployment &&
      this.state.asset.deployment__submission_count > 0 &&
      (
        this.userCan('view_submissions', this.state.asset) ||
        this.userCan('partial_submissions', this.state.asset)
      )
    );
  }

  renderTopTabs() {
    if (this.state.asset === undefined) {
      return false;
    }

    let dataTabClassNames = 'form-view__tab';
    if (!this.isDataTabEnabled()) {
      dataTabClassNames += ' form-view__tab--disabled';
    }

    return (
      <bem.FormView__toptabs>
        <Link
          to={ROUTES.FORM_SUMMARY.replace(':uid', this.state.assetid)}
          className='form-view__tab'
          activeClassName='active'
        >
          {t('Summary')}
        </Link>

        <Link
          to={ROUTES.FORM_LANDING.replace(':uid', this.state.assetid)}
          className='form-view__tab'
          activeClassName='active'>
          {t('Form')}
        </Link>

        <Link
          to={ROUTES.FORM_DATA.replace(':uid', this.state.assetid)}
          className={dataTabClassNames}
          activeClassName='active'
        >
          {t('Data')}
        </Link>

        <Link
          to={ROUTES.FORM_SETTINGS.replace(':uid', this.state.assetid)}
          className='form-view__tab'
          activeClassName='active'
          disabled={!this.userCan('change_asset', this.state.asset)}
        >
          {t('Settings')}
        </Link>

        <Link
          to={ROUTES.FORMS}
          className='form-view__link form-view__link--close'>
          <i className='k-icon-close' />
        </Link>

      </bem.FormView__toptabs>
    );
  }
  renderFormSideTabs() {
    var sideTabs = [];

    if (this.state.asset && this.state.asset.has_deployment && this.isActiveRoute(`/forms/${this.state.assetid}/data`)) {
      sideTabs = [
        {label: t('Reports'), icon: 'k-icon-report', path: `/forms/${this.state.assetid}/data/report`},
        {label: t('Table'), icon: 'k-icon-table', path: `/forms/${this.state.assetid}/data/table`},
        {label: t('Gallery'), icon: 'k-icon-photo-gallery', path: `/forms/${this.state.assetid}/data/gallery`},
        {label: t('Downloads'), icon: 'k-icon-download', path: `/forms/${this.state.assetid}/data/downloads`},
        {label: t('Map'), icon: 'k-icon-map-view', path: `/forms/${this.state.assetid}/data/map`},
      ];
    }

    if (this.state.asset && this.isActiveRoute(`/forms/${this.state.assetid}/settings`)) {
      sideTabs = [];

      sideTabs.push({label: t('General'), icon: 'k-icon-settings', path: `/forms/${this.state.assetid}/settings`});

      //TODO:Remove owner only access to settings/media after we remove KC iframe: https://github.com/kobotoolbox/kpi/issues/2647#issuecomment-624301693
      if (this.state.asset.deployment__active && assetUtils.isSelfOwned(this.state.asset)) {
        sideTabs.push({label: t('Media'), icon: 'k-icon-photo-gallery', path: `/forms/${this.state.assetid}/settings/media`});
      }

      sideTabs.push({label: t('Sharing'), icon: 'k-icon-user-share', path: `/forms/${this.state.assetid}/settings/sharing`});

      if (
        this.state.asset.deployment__active &&
        mixins.permissions.userCan(PERMISSIONS_CODENAMES.view_submissions, this.state.asset) &&
        mixins.permissions.userCan(PERMISSIONS_CODENAMES.change_asset, this.state.asset)
      ) {
        sideTabs.push({label: t('REST Services'), icon: 'k-icon-data-sync', path: `/forms/${this.state.assetid}/settings/rest`});
      }
    }

    if (sideTabs.length > 0) {
      return (
        <bem.FormView__sidetabs>
          { sideTabs.map((item, ind) =>
            <Link
              to={item.path}
              key={ind}
              activeClassName='active'
              onlyActiveOnIndex
              className='form-view__tab'
              data-path={item.path}
              onClick={this.triggerRefresh}>
                <i className={`k-icon ${item.icon}`} />
                {item.label}
            </Link>
          )}
        </bem.FormView__sidetabs>
      );
    }

    return false;
  }
  render() {
    if (!this.props.show)
      return false;
    if (this.props.type == 'top') {
      return (
        this.renderTopTabs()
      );
    }
    if (this.props.type == 'side') {
      return (
        this.renderFormSideTabs()
      );
    }
  }

};

reactMixin(FormViewTabs.prototype, Reflux.ListenerMixin);
reactMixin(FormViewTabs.prototype, mixins.contextRouter);
reactMixin(FormViewTabs.prototype, mixins.permissions);

FormViewTabs.contextTypes = {
  router: PropTypes.object
};

export default FormViewTabs;
