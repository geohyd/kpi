interface FailResponse {
  responseJSON: {
    detail: string
  }
  responseText: string
  status: number
  statusText: string
}

interface AssignablePermission {
  url: string
  label: string
}

interface AssignablePermissionPartial extends AssignablePermission {
  label: {
    default: string
    view_submissions: string
    change_submissions: string
    delete_submissions: string
    validate_submissions: string
  }
}

/**
 * A single permission instance for a given user.
 */
interface Permission {
  url: string
  user: string
  permission: string
  label: string
}

/**
 * A saved export settings instance.
 */
interface ExportSetting {
  uid: string
  url: string
  name: string
  date_modified: string
  export_settings: {
    lang: string
    type: string
    fields: string[]
    group_sep: string
    xls_types: boolean
    multiple_select: string
    hierarchy_in_labels: boolean
    fields_from_all_versions: boolean
  }
}

interface SurveyRow {
  $autoname: string
  $kuid: string
  calculation?: string
  label?: string[]
  hint?: string[]
  name?: string
  required?: boolean
  // We use dynamic import to avoid changing this ambient module to a normal
  // module: see https://stackoverflow.com/a/51114250/2311247
  type: import('js/constants').QuestionTypeName
  _isRepeat?: boolean
  appearance?: string
  parameters?: string
  'kobo--matrix_list'?: string
  'kobo--rank-constraint-message'?: string
  'kobo--rank-items'?: string
  'kobo--score-choices'?: string
  'kobo--locking-profile'?: string
}

interface SurveyChoice {
  $autovalue: string
  $kuid: string
  label: string[]
  list_name: string
  name: string
}

interface AssetContentSettings {
  name?: string
  version?: string
  id_string?: string
  style?: string
  form_id?: string
  title?: string
}

/**
 * Represents parsed form (i.e. the spreadsheet file) contents.
 * It is quite crucial for multiple places of UI, but is not always
 * present in backend responses (performance reasons).
 */
interface AssetContent {
  schema?: string
  survey?: SurveyRow[]
  choices?: SurveyChoice[]
  settings?: AssetContentSettings | AssetContentSettings[]
  translated?: string[]
  translations?: Array<string|null>
}

interface AssetReportStylesSpecified {
  [name: string]: {}
}

interface AssetReportStylesKuidNames {
  [name: string]: {}
}

/**
 * This is the backend's asset.
 */
interface AssetResponse {
  url: string
  owner: string
  owner__username: string
  parent: string | null
  settings: {
    sector?: {
      label: string
      value: string
    }
    country?: {
      label: string
      value: string
    }
    description?: string
    'share-metadata'?: boolean
    'data-table'?: {
      'frozen-column'?: string
      'show-hxl-tags'?: boolean
      'show-group-name'?: boolean
      'translation-index'?: number
    }
    organization?: string
  }
  asset_type: string
  date_created: string
  summary: {
    geo?: boolean
    labels?: string[]
    columns?: string[]
    lock_all?: boolean
    lock_any?: boolean
    languages?: Array<string|null>
    row_count?: number
    default_translation?: string|null
  }
  date_modified: string
  version_id: string|null
  version__content_hash: string|null
  version_count: number
  has_deployment: boolean
  deployed_version_id: string|null
  deployed_versions: {
    count: number
    next: null | string
    previous: null | string
    results: {
      uid: string
      url: string
      content_hash: string
      date_deployed: string
      date_modified: string
    }[]
  }
  deployment__identifier: string|null
  deployment__links: {
    url?: string
    single_url?: string
    single_once_url?: string
    offline_url?: string
    preview_url?: string
    iframe_url?: string
    single_iframe_url?: string
    single_once_iframe_url?: string
  }
  deployment__active: boolean
  deployment__data_download_links: {
    xls_legacy?: string
    csv_legacy?: string
    zip_legacy?: string
    kml_legacy?: string
    xls?: string
    csv?: string
  }
  deployment__submission_count: number
  report_styles: {
    default?: {}
    specified?: AssetReportStylesSpecified
    kuid_names?: AssetReportStylesKuidNames
  }
  report_custom: {
    [reportName: string]: {
      crid: string
      name: string
      questions: string[]
      reportStyle: {
        groupDataBy: string
        report_type: string
        report_colors: string[]
        translationIndex: number
      }
    }
  }
  map_styles: {}
  map_custom: {}
  content?: AssetContent
  downloads: {
    format: string
    url: string
  }[]
  embeds: {
    format: string
    url: string
  }[]
  koboform_link: string
  xform_link: string
  hooks_link: string
  tag_string: string
  uid: string
  kind: string
  xls_link: string
  name: string
  assignable_permissions: Array<AssignablePermission|AssignablePermissionPartial>
  permissions: Permission[]
  exports: string
  export_settings: ExportSetting[]
  data: string
  children: {
    count: number
  }
  subscribers_count: number
  status: string
  access_types: string[]|null
  data_sharing: {}
  paired_data: string

  // TODO: think about creating a new interface for asset that is being extended
  // on frontend. Here are some properties we add to the response:
  tags?: string[]
  unparsed__settings?: AssetContentSettings
  settings__style?: string
  settings__form_id?: string
  settings__title?: string
}
