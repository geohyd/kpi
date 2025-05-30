import React, {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import PopoverMenu from 'js/popoverMenu';
import sessionStore from 'js/stores/session';
import bem from 'js/bem';
import {currentLang, stringToColor} from 'js/utils';
import envStore from 'js/envStore';
import type {LabelValuePair} from 'js/dataInterface';
import {dataInterface} from 'js/dataInterface';
import {actions} from 'js/actions';
import {ACCOUNT_ROUTES} from 'jsapp/js/account/routes';

/**
 * UI element that display things only for logged-in user. An avatar that gives
 * access to a menu that allows language change, logging out and few other
 * things.
 *
 * Note: this displays a simplified content for user with invalidated password.
 */
export default function AccountMenu() {
  const navigate = useNavigate();

  const [isLanguageSelectorVisible, setIsLanguageSelectorVisible] =
    useState<boolean>(false);
  const toggleLanguageSelector = () => {
    setIsLanguageSelectorVisible(!isLanguageSelectorVisible);
  };

  const shouldDisplayUrls =
    (typeof envStore.data.terms_of_service_url === 'string' &&
      envStore.data.terms_of_service_url !== '') ||
    (typeof envStore.data.privacy_policy_url === 'string' &&
      envStore.data.privacy_policy_url !== '');

  let langs: LabelValuePair[] = [];
  if (envStore.isReady && envStore.data.interface_languages) {
    langs = envStore.data.interface_languages;
  }

  const onLanguageChange = (langCode: string) => {
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
  };

  const renderLangItem = (lang: LabelValuePair) => {
    const currentLanguage = currentLang();
    return (
      <bem.AccountBox__menuLI key={lang.value}>
        <bem.AccountBox__menuLink onClick={() => onLanguageChange(lang.value)}>
          {lang.value === currentLanguage && <strong>{lang.label}</strong>}
          {lang.value !== currentLanguage && lang.label}
        </bem.AccountBox__menuLink>
      </bem.AccountBox__menuLI>
    );
  };

  const openAccountSettings = () => {
    navigate(ACCOUNT_ROUTES.ACCOUNT_SETTINGS);
  };

  if (!sessionStore.isLoggedIn) {
    return null;
  }

  const accountName = sessionStore.currentAccount.username;
  const accountEmail =
    'email' in sessionStore.currentAccount
      ? sessionStore.currentAccount.email
      : '';

  const initialsStyle = {background: `#${stringToColor(accountName)}`};
  const accountMenuLabel = (
    <bem.AccountBox__initials style={initialsStyle}>
      {accountName.charAt(0)}
    </bem.AccountBox__initials>
  );

  const isInvalidatedPasswordUser = (
    'validated_password' in sessionStore.currentAccount &&
    sessionStore.currentAccount.validated_password === false
  );

  return (
    <bem.AccountBox>
      <PopoverMenu type='account-menu' triggerLabel={accountMenuLabel}>
        <bem.AccountBox__menu>
          <bem.AccountBox__menuLI key='1'>
            <bem.AccountBox__menuItem m={'avatar'}>
              {accountMenuLabel}
            </bem.AccountBox__menuItem>

            <bem.AccountBox__menuItem m={'mini-profile'}>
              <span className='account-username'>{accountName}</span>
              <span className='account-email'>{accountEmail}</span>
            </bem.AccountBox__menuItem>

            {/*
              There is no UI we can show to a user with invalidated password, so
              we don't allow any in-app navigation.
            */}
            {!isInvalidatedPasswordUser &&
              <bem.AccountBox__menuItem m={'settings'}>
                <bem.KoboButton
                  onClick={openAccountSettings}
                  m={['blue', 'fullwidth']}
                >
                  {t('Account Settings')}
                </bem.KoboButton>
              </bem.AccountBox__menuItem>
            }
          </bem.AccountBox__menuLI>

          {shouldDisplayUrls && (
            <bem.AccountBox__menuLI key='2' className='environment-links'>
              {envStore.data.terms_of_service_url && (
                <a href={envStore.data.terms_of_service_url} target='_blank'>
                  {t('Terms of Service')}
                </a>
              )}
              {envStore.data.privacy_policy_url && (
                <a href={envStore.data.privacy_policy_url} target='_blank'>
                  {t('Privacy Policy')}
                </a>
              )}
            </bem.AccountBox__menuLI>
          )}

          <bem.AccountBox__menuLI m={'lang'} key='3'>
            <bem.AccountBox__menuLink
              onClick={toggleLanguageSelector}
              data-popover-menu-stop-blur
              tabIndex='0'
            >
              <i className='k-icon k-icon-language' />
              {t('Language')}
            </bem.AccountBox__menuLink>

            {isLanguageSelectorVisible && <ul>{langs.map(renderLangItem)}</ul>}
          </bem.AccountBox__menuLI>

          <bem.AccountBox__menuLI m={'logout'} key='4'>
            <bem.AccountBox__menuLink onClick={actions.auth.logout}>
              <i className='k-icon k-icon-logout' />
              {t('Logout')}
            </bem.AccountBox__menuLink>
          </bem.AccountBox__menuLI>
        </bem.AccountBox__menu>
      </PopoverMenu>
    </bem.AccountBox>
  );
}
