import React, {useEffect, useState} from 'react';
import KoboModal from '../modals/koboModal';
import KoboModalHeader from 'js/components/modals/koboModalHeader';
import KoboModalContent from 'js/components/modals/koboModalContent';
import KoboModalFooter from 'js/components/modals/koboModalFooter';
import Button from 'js/components/common/button';
import sessionStore from 'js/stores/session';
import {ACCOUNT_ROUTES} from 'js/account/routes';
import {useNavigate} from 'react-router-dom';
import styles from './overLimitModal.module.scss';
import Icon from 'js/components/common/icon';
import {limitBannerContainer} from './overLimitBanner.module.scss';
import cx from 'classnames';

interface OverLimitModalProps {
  show: boolean;
  limits: string[];
  dismissed: () => void;
  interval: 'month' | 'year';
}

function OverLimitModal(props: OverLimitModalProps) {
  const [isModalOpen, setIsModalOpen] = useState(true);
  const accountName = sessionStore.currentAccount.username;
  const navigate = useNavigate();
  const [show, setShow] = useState(props.show);
  const toggleModal = () => {
    setIsModalOpen(!isModalOpen);
  };

  const handleClose = () => {
    toggleModal();
    setShow(false);
    props.dismissed();
  };

  useEffect(() => {
    setShow(props.show);
  }, [props.show]);

  return (
    <div>
      <KoboModal isOpen={show} onRequestClose={toggleModal} size='medium'>
        <KoboModalHeader>
          {t('You have reached your plan limit')}
        </KoboModalHeader>

        <KoboModalContent>
          <div>
            <p>
              {t('Dear')} {accountName},
            </p>
            <div>
              {t('You have reached the')}{' '}
              {props.limits.map((limit, i) => (
                <span key={i}>
                  {i > 0 && props.limits.length > 2 && ','}
                  {i === props.limits.length - 1 && i > 0 && ' and '}
                  {limit}
                </span>
              ))}{' '}
              {t('limit')} {props.limits.length > 1 && 's'}{' '}
              {t('included with your current plan.')}
            </div>
            <div>
              {t('Please')}{' '}
              <a href={`#${ACCOUNT_ROUTES.PLAN}`} className={styles.link}>
                {t('upgrade your plan')}
              </a>{' '}
              {'as soon as possible or ' /* tone down the language for now */}
              <a
                href='https://support.anteagroup.fr'
                target='_blank'
                className={styles.link}
              >
                {'contact us'}
              </a>
              {' to speak with our team. You can '}
              <a href={`#${ACCOUNT_ROUTES.USAGE}`} className={styles.link}>
                {t('review your usage in account settings')}
              </a>
              {'.'}
            </div>
            {
              // removed to make the message less scary
              /* <p className={cx(limitBannerContainer, styles.consequences)}>
              <Icon
                name='warning'
                size='m'
                color='red'
                classNames={[styles.warningIcon]}
              />
              <span>
                {t(
                  'Users who have exceeded their submission or storage limits may be temporarily blocked from collecting data. Repeatedly exceeding usage limits may result in account suspension.'
                )}
              </span>
            </p> */
            }
          </div>
        </KoboModalContent>

        <KoboModalFooter alignment='end'>
          <Button
            type='frame'
            color='dark-blue'
            size='l'
            onClick={handleClose}
            label={t('remind me later')}
            classNames={[styles.button, styles.frame]}
          />

          <Button
            type='full'
            color='blue'
            size='l'
            onClick={() => navigate(ACCOUNT_ROUTES.PLAN)}
            label={t('upgrade now')}
            classNames={[styles.button, styles.full]}
          />
        </KoboModalFooter>
      </KoboModal>
    </div>
  );
}

export default OverLimitModal;
