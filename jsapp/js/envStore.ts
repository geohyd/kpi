import {actions} from 'js/actions';
import type {
  LabelValuePair,
  TransxLanguages,
  EnvironmentResponse,
} from 'js/dataInterface';
import {makeAutoObservable} from 'mobx';

/*
 * NOTE: This store is written to use MobX, but its imports do not need to be
 * exported with `observer()`. We also do not need to add this to a root store.
 *
 * This is because this store's value does not actually change as they store
 * constant environment variables that are set by the docker container. Thus it
 * JustWorks™ given our frontend architecture.
 */

export interface EnvStoreFieldItem {
  name: string;
  required: boolean;
  label: string;
}

export interface SocialApp {
  name: string;
  provider: string;
  client_id: string;
}

export interface FreeTierThresholds {
  storage: number | null;
  data: number | null;
  transcription_minutes: number | null;
  translation_chars: number | null;
}

export interface FreeTierDisplay {
  name: string | null;
  feature_list: [string] | [];
}

type ProjectMetadataFieldKey =
  | 'description'
  | 'sector'
  | 'country'
  | 'operational_purpose'
  | 'collects_pii';

class EnvStoreData {
  public terms_of_service_url = '';
  public privacy_policy_url = '';
  public source_code_url = '';
  public support_email = '';
  public support_url = '';
  public community_url = '';
  public min_retry_time = 4; // seconds
  public max_retry_time: number = 4 * 60; // seconds
  public project_metadata_fields: EnvStoreFieldItem[] = [];
  public user_metadata_fields: EnvStoreFieldItem[] = [];
  public sector_choices: LabelValuePair[] = [];
  public operational_purpose_choices: LabelValuePair[] = [];
  public country_choices: LabelValuePair[] = [];
  public interface_languages: LabelValuePair[] = [];
  public transcription_languages: TransxLanguages = {};
  public translation_languages: TransxLanguages = {};
  public submission_placeholder = '';
  public asr_mt_features_enabled = false;
  public mfa_localized_help_text = '';
  public mfa_enabled = false;
  public mfa_per_user_availability = false;
  public mfa_has_availability_list = false;
  public mfa_code_length = 6;
  public stripe_public_key: string | null = null;
  public social_apps: SocialApp[] = [];
  public free_tier_thresholds: FreeTierThresholds = {
    storage: null,
    data: null,
    transcription_minutes: null,
    translation_chars: null
  };
  public free_tier_display: FreeTierDisplay = {name: null, feature_list: []};
  public enable_custom_password_guidance_text = false;
  public custom_password_localized_help_text = '';
  public enable_password_entropy_meter = false;

  getProjectMetadataField(
    fieldName: ProjectMetadataFieldKey
  ): EnvStoreFieldItem | boolean {
    for (const f of this.project_metadata_fields) {
      if (f.name === fieldName) {
        return f;
      }
    }
    return false;
  }

  public getProjectMetadataFieldsAsSimpleDict() {
    // dict[name] => {name, required, label}
    const dict: Partial<{
      [fieldName in ProjectMetadataFieldKey]: EnvStoreFieldItem;
    }> = {};
    for (const field of this.project_metadata_fields) {
      dict[field.name as keyof typeof dict] = field;
    }
    return dict;
  }

  public getUserMetadataFieldsAsSimpleDict() {
    // dict[name] => {name, required, label}
    const dict: {[fieldName: string]: EnvStoreFieldItem} = {};
    for (const field of this.user_metadata_fields) {
      dict[field.name] = field;
    }
    return dict;
  }
}

class EnvStore {
  data: EnvStoreData;
  isReady = false;

  constructor() {
    makeAutoObservable(this);
    this.data = new EnvStoreData();

    actions.auth.getEnvironment.completed.listen(this.onGetEnvCompleted.bind(this));
    actions.auth.getEnvironment();
  }

  /**
   * A DRY utility function that turns an array of two items into an object with
   * 'value' and 'label' properties.
   */
  private nestedArrToChoiceObjs = (i: string[]): LabelValuePair => {
    return {
      value: i[0],
      label: i[1],
    };
  };

  private onGetEnvCompleted(response: EnvironmentResponse) {
    this.data.terms_of_service_url = response.terms_of_service_url;
    this.data.privacy_policy_url = response.privacy_policy_url;
    this.data.source_code_url = response.source_code_url;
    this.data.support_email = response.support_email;
    this.data.support_url = response.support_url;
    this.data.community_url = response.community_url;
    this.data.min_retry_time = response.frontend_min_retry_time;
    this.data.max_retry_time = response.frontend_max_retry_time;
    this.data.project_metadata_fields = response.project_metadata_fields;
    this.data.user_metadata_fields = response.user_metadata_fields;
    this.data.submission_placeholder = response.submission_placeholder;
    this.data.mfa_localized_help_text = response.mfa_localized_help_text;
    this.data.mfa_enabled = response.mfa_enabled;
    this.data.mfa_per_user_availability = response.mfa_per_user_availability;
    this.data.mfa_has_availability_list = response.mfa_has_availability_list;
    this.data.mfa_code_length = response.mfa_code_length;
    this.data.stripe_public_key = response.stripe_public_key;
    this.data.social_apps = response.social_apps;
    this.data.free_tier_thresholds = response.free_tier_thresholds;
    this.data.free_tier_display = response.free_tier_display;

    if (response.sector_choices) {
      this.data.sector_choices = response.sector_choices.map(this.nestedArrToChoiceObjs);
    }
    if (response.operational_purpose_choices) {
      this.data.operational_purpose_choices = response.operational_purpose_choices.map(this.nestedArrToChoiceObjs);
    }
    if (response.country_choices) {
      this.data.country_choices = response.country_choices.map(this.nestedArrToChoiceObjs);
    }
    if (response.interface_languages) {
      this.data.interface_languages = response.interface_languages.map(this.nestedArrToChoiceObjs);
    }

    this.data.asr_mt_features_enabled = response.asr_mt_features_enabled;

    this.data.enable_custom_password_guidance_text = response.enable_custom_password_guidance_text;
    this.data.custom_password_localized_help_text = response.custom_password_localized_help_text;
    this.data.enable_password_entropy_meter = response.enable_password_entropy_meter;

    this.isReady = true;
  }

  public getSectorLabel(sectorName: string): string | undefined {
    const foundSector = this.data.sector_choices.find(
      (item: LabelValuePair) => item.value === sectorName
    );
    if (foundSector) {
      return foundSector.label;
    }
    return undefined;
  }

  public getCountryLabel(code: string): string | undefined {
    const foundCountry = this.data.country_choices.find(
      (item: LabelValuePair) => item.value === code
    );
    if (foundCountry) {
      return foundCountry.label;
    }
    return undefined;
  }
}

/**
 * This store keeps all environment data (constants) like languages, countries,
 * external urls…
 */
export default new EnvStore;
