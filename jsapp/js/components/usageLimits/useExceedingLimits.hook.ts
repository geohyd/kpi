import {useState, useReducer, useContext, useEffect} from 'react';
import type {BaseSubscription, BasePrice} from '../../account/stripe.api';
import {getAccountLimits, getProducts} from '../../account/stripe.api';
import type {FreeTierThresholds} from 'js/envStore';
import envStore from 'js/envStore';
import {USAGE_WARNING_RATIO} from 'js/constants';
import useWhenStripeIsEnabled from 'js/hooks/useWhenStripeIsEnabled.hook';
import {when} from 'mobx';
import subscriptionStore from 'js/account/subscriptionStore';
import {UsageContext} from 'js/account/useUsage.hook';

interface SubscribedState {
  subscribedProduct: null | BaseSubscription;
}

const initialState = {
  subscribedProduct: null,
};

function subscriptionReducer(state: SubscribedState, action: {prodData: any}) {
  return {...state, subscribedProduct: action.prodData};
}

export const useExceedingLimits = () => {
  const [state, dispatch] = useReducer(subscriptionReducer, initialState);
  const usage = useContext(UsageContext);

  const [exceedList, setExceedList] = useState<string[]>([]);
  const [warningList, setWarningList] = useState<string[]>([]);

  const [subscribedStorageLimit, setSubscribedStorageLimit] = useState<
    number | string
  >();
  const [subscribedSubmissionLimit, setSubscribedSubmissionLimit] = useState<
    number | string
  >();
  const [subscribedTranscriptionMinutes, setTranscriptionMinutes] = useState<
    number | string
  >();
  const [subscribedTranslationChars, setTranslationChars] = useState<
    number | string
  >();
  const [areLimitsLoaded, setAreLimitsLoaded] = useState(false);

  // Get products and get default limits for community plan
  useWhenStripeIsEnabled(() => {
    getAccountLimits().then((limits) => {
      setSubscribedSubmissionLimit(limits.submission_limit);
      setSubscribedStorageLimit(limits.storage_bytes_limit);
      setTranscriptionMinutes(Number(limits.nlp_seconds_limit));
      setTranslationChars(Number(limits.nlp_character_limit));
      setAreLimitsLoaded(true);
    });
  }, []);

  // Get subscription data
  useWhenStripeIsEnabled(
    () =>
      when(
        () => subscriptionStore.isInitialised,
        () => {
          dispatch({
            prodData: subscriptionStore.planResponse,
          });
        }
      ),
    []
  );

  function isOverLimit(
    subscribedLimit: number | string | undefined,
    currentUsage: number | undefined,
    listString: string
  ) {
    if (
      subscribedLimit &&
      typeof subscribedLimit === 'number' &&
      typeof currentUsage === 'number'
    ) {
      if (currentUsage >= subscribedLimit) {
        setExceedList((prevState) => prevState.concat([listString]));
      } else if (currentUsage >= subscribedLimit * USAGE_WARNING_RATIO) {
        setWarningList((prevState) => prevState.concat([listString]));
      }
    }
  }

  // Check if usage is more than limit
  useEffect(() => {
    if (!usage.isLoaded || !areLimitsLoaded) {
      return;
    }
    isOverLimit(subscribedStorageLimit, usage.storage, 'storage');
    isOverLimit(subscribedSubmissionLimit, usage.submissions, 'submission');
    isOverLimit(
      subscribedTranscriptionMinutes,
      usage.transcriptionMinutes,
      'automated transcription'
    );
    isOverLimit(
      subscribedTranslationChars,
      usage.translationChars,
      'machine translation'
    );
  }, [usage.isLoaded, areLimitsLoaded]);

  return {exceedList, warningList};
};
