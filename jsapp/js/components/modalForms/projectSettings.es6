import React from 'react';
import PropTypes from 'prop-types';
import reactMixin from 'react-mixin';
import autoBind from 'react-autobind';
import {when} from 'mobx';
import Reflux from 'reflux';
import Dropzone from 'react-dropzone';
import Button from 'js/components/common/button';
import clonedeep from 'lodash.clonedeep';
import TextBox from 'js/components/common/textBox';
import WrappedSelect from 'js/components/common/wrappedSelect';
import bem from 'js/bem';
import LoadingSpinner from 'js/components/common/loadingSpinner';
import assetUtils from 'js/assetUtils';
import {stores} from 'js/stores';
import sessionStore from 'js/stores/session';
import mixins from 'js/mixins';
import TemplatesList from 'js/components/templatesList';
import {actions} from 'js/actions';
import {dataInterface} from 'js/dataInterface';
import {
  addRequiredToLabel,
  escapeHtml,
  isAValidUrl,
  validFileTypes,
  notify,
  join,
} from 'utils';
import {
  NAME_MAX_LENGTH,
  PROJECT_SETTINGS_CONTEXTS,
} from 'js/constants';
import {ROUTES} from 'js/router/routerConstants';
import {LOCKING_RESTRICTIONS} from 'js/components/locking/lockingConstants';
import {hasAssetRestriction} from 'js/components/locking/lockingUtils';
import envStore from 'js/envStore';
import {router} from 'js/router/legacy';
import {withRouter} from 'js/router/legacy';
import {userCan} from 'js/components/permissions/utils';

const VIA_URL_SUPPORT_URL = 'xls_url.html';

/**
 * This is used for multiple different purposes:
 *
 * 1. When creating new project
 * 2. When replacing project with new one
 * 3. When editing project in /settings
 * 4. When editing or creating asset in Form Builder
 *
 * Identifying the purpose is done by checking `context` and `formAsset`.
 *
 * You can listen to field changes by `onProjectDetailsChange` prop function.
 *
 * NOTE: We have multiple components with similar form:
 * - ProjectSettings
 * - AccountSettingsRoute
 * - LibraryAssetForm
 */
class ProjectSettings extends React.Component {
  constructor(props) {
    super(props);

    this.STEPS = {
      FORM_SOURCE: 'form-source',
      CHOOSE_TEMPLATE: 'choose-template',
      UPLOAD_FILE: 'upload-file',
      IMPORT_URL: 'import-url',
      PROJECT_DETAILS: 'project-details',
    };

    this.unlisteners = [];

    this.state = {
      isSessionLoaded: !!sessionStore.isLoggedIn,
      isSubmitPending: false,
      formAsset: this.props.formAsset,
      // project details
      fields: this.getInitialFieldsFromAsset(this.props.formAsset),
      fieldsWithErrors: [],
      // steps
      currentStep: null,
      previousStep: null,
      // importing url
      isImportFromURLPending: false,
      importUrl: '',
      importUrlButtonEnabled: false,
      importUrlButton: t('Import'),
      // template
      isApplyTemplatePending: false,
      applyTemplateButton: t('Next'),
      chosenTemplateUid: null,
      // upload files
      isUploadFilePending: false,
      // archive flow
      isAwaitingArchiveCompleted: false,
      isAwaitingUnarchiveCompleted: false,
    };

    autoBind(this);
  }

  /*
   * setup
   */

  componentDidMount() {
    this.setInitialStep();
    when(() => sessionStore.isInitialLoadComplete, () => {
      this.setState({isSessionLoaded: true});
    });
    this.unlisteners.push(
      actions.resources.loadAsset.completed.listen(this.onLoadAssetCompleted.bind(this)),
      actions.resources.updateAsset.completed.listen(this.onUpdateAssetCompleted.bind(this)),
      actions.resources.updateAsset.failed.listen(this.onUpdateAssetFailed.bind(this)),
      actions.resources.cloneAsset.completed.listen(this.onCloneAssetCompleted.bind(this)),
      actions.resources.cloneAsset.failed.listen(this.onCloneAssetFailed.bind(this)),
      actions.resources.setDeploymentActive.failed.listen(this.onSetDeploymentActiveFailed.bind(this)),
      actions.resources.setDeploymentActive.completed.listen(this.onSetDeploymentActiveCompleted.bind(this)),
      router.subscribe(this.onRouteChange.bind(this))
    );
  }

  componentWillUnmount() {
    this.unlisteners.forEach((clb) => {clb();});
  }

  getInitialFieldsFromAsset(asset) {
    const fields = {};

    fields.name = asset ? asset.name : '';
    fields.description = asset?.settings ? asset.settings.description : '';

    fields.sector = asset?.settings?.sector?.value ? asset.settings.sector : null;
    fields.country = asset?.settings ? asset.settings.country : null;
    fields.operational_purpose = asset?.settings ? asset.settings.operational_purpose : null;
    fields.collects_pii = asset?.settings ? asset.settings.collects_pii : null;

    return fields;
  }

  /**
   * Function used whenever some endpoint calls return an asset.
   */
  applyAssetToState(asset) {
    this.setState({
      fields: this.getInitialFieldsFromAsset(asset),
      isUploadFilePending: false,
      isImportFromURLPending: false,
      formAsset: asset,
    });
  }

  setInitialStep() {
    switch (this.props.context) {
      case PROJECT_SETTINGS_CONTEXTS.NEW:
      case PROJECT_SETTINGS_CONTEXTS.REPLACE:
        return this.displayStep(this.STEPS.FORM_SOURCE);
      case PROJECT_SETTINGS_CONTEXTS.EXISTING:
      case PROJECT_SETTINGS_CONTEXTS.BUILDER:
        return this.displayStep(this.STEPS.PROJECT_DETAILS);
      default:
        throw new Error(`Unknown context: ${this.props.context}!`);
    }
  }

  getBaseTitle() {
    switch (this.props.context) {
      case PROJECT_SETTINGS_CONTEXTS.NEW:
        return t('Create project');
      case PROJECT_SETTINGS_CONTEXTS.REPLACE:
        return t('Replace form');
      case PROJECT_SETTINGS_CONTEXTS.EXISTING:
      case PROJECT_SETTINGS_CONTEXTS.BUILDER:
      default:
        return t('Project settings');
    }
  }

  getStepTitle(step) {
    switch (step) {
      case this.STEPS.FORM_SOURCE: return t('Choose a source');
      case this.STEPS.CHOOSE_TEMPLATE: return t('Choose template');
      case this.STEPS.UPLOAD_FILE: return t('Upload XLSForm');
      case this.STEPS.IMPORT_URL: return t('Import XLSForm');
      case this.STEPS.PROJECT_DETAILS: return t('Project details');
      default: return '';
    }
  }

  getFilenameFromURI(url) {
    return decodeURIComponent(new URL(url).pathname.split('/').pop().split('.')[0]);
  }

  isLoading() {
    return (
      !this.state.isSessionLoaded ||
      !this.state.currentStep ||
      (
        // this checks if the modal is about existing asset
        // that is not fully loaded yet
        this.props.context !== PROJECT_SETTINGS_CONTEXTS.NEW &&
        typeof this.state.formAsset?.content === 'undefined'
      )
    );
  }

  isReplacingFormLocked() {
    return (
      this.props.context === PROJECT_SETTINGS_CONTEXTS.REPLACE &&
      this.state.formAsset.content &&
      hasAssetRestriction(this.state.formAsset.content, LOCKING_RESTRICTIONS.form_replace.name)
    );
  }

  /*
   * handling user input
   */

  onAnyFieldChange(fieldName, newFieldValue) {
    let newStateObj = clonedeep(this.state);

    // Set Value
    newStateObj.fields[fieldName] = newFieldValue;

    // If given field has error and user starts to edit it, we can remove
    // the error and wait for `handleSubmit` to add new ones if necessary.
    if (this.hasFieldError(fieldName)) {
      newStateObj.fieldsWithErrors = newStateObj.fieldsWithErrors.filter(
        (fieldWithErrorName) => (fieldWithErrorName !== fieldName)
      );
    }

    this.setState(newStateObj);

    if (typeof this.props.onProjectDetailsChange === 'function') {
      this.props.onProjectDetailsChange({
        fieldName: fieldName,
        fieldValue: newFieldValue,
      });
    }
  }

  onNameChange(newValue) {
    this.onAnyFieldChange('name', assetUtils.removeInvalidChars(newValue).slice(0, NAME_MAX_LENGTH));
  }

  onDescriptionChange(newValue) {
    this.onAnyFieldChange('description', assetUtils.removeInvalidChars(newValue));
  }

  onImportUrlChange(value) {
    this.setState({
      importUrl: value,
      importUrlButtonEnabled: isAValidUrl(value),
      importUrlButton: t('Import'),
    });
  }

  onTemplateChange(templateUid) {
    this.setState({
      chosenTemplateUid: templateUid,
    });
  }

  resetApplyTemplateButton() {
    this.setState({
      isApplyTemplatePending: false,
      applyTemplateButton: t('Choose'),
    });
  }

  resetImportUrlButton() {
    this.setState({
      isImportFromURLPending: false,
      importUrlButtonEnabled: false,
      importUrlButton: t('Import'),
    });
  }

  deleteProject(evt) {
    evt.preventDefault();

    this.deleteAsset(
      this.state.formAsset.uid,
      this.state.formAsset.name,
      this.goToProjectsList.bind(this)
    );
  }

  // archive flow

  isArchivable() {
    return this.state.formAsset.deployment_status === 'deployed';
  }

  isArchived() {
    return this.state.formAsset.deployment_status === 'archived';
  }

  archiveProject(evt) {
    evt.preventDefault();
    this.archiveAsset(this.state.formAsset.uid);
    this.setState({isAwaitingArchiveCompleted: true});
  }

  unarchiveProject(evt) {
    evt.preventDefault();
    this.unarchiveAsset(this.state.formAsset.uid);
    this.setState({isAwaitingUnarchiveCompleted: true});
  }

  onSetDeploymentActiveFailed() {
    this.setState({
      isAwaitingArchiveCompleted: false,
      isAwaitingUnarchiveCompleted: false,
    });
  }

  // when archiving/unarchiving finishes, take user to a route that makes sense
  // unless user navigates by themselves before that happens
  onSetDeploymentActiveCompleted() {
    if (this.state.isAwaitingArchiveCompleted) {
      this.goToProjectsList();
    }
    if (this.state.isAwaitingUnarchiveCompleted) {
      this.goToFormLanding();
    }
    this.setState({
      isAwaitingArchiveCompleted: false,
      isAwaitingUnarchiveCompleted: false,
    });
  }

  onRouteChange() {
    this.setState({
      isAwaitingArchiveCompleted: false,
      isAwaitingUnarchiveCompleted: false,
    });
  }

  /*
   * routes navigation
   */

  goToFormBuilder(assetUid) {
    stores.pageState.hideModal();
    this.props.router.navigate(`/forms/${assetUid}/edit`);
  }

  goToFormLanding() {
    stores.pageState.hideModal();

    let targetUid;
    if (this.state.formAsset) {
      targetUid = this.state.formAsset.uid;
    } else if (this.context.router && this.context.router.params.assetid) {
      targetUid = this.context.router.params.assetid;
    } else if (this.context.router && this.context.router.params.uid) {
      targetUid = this.context.router.params.uid;
    }

    if (!targetUid) {
      throw new Error('Unknown uid!');
    }

    this.props.router.navigate(ROUTES.FORM_LANDING.replace(':uid', targetUid));
  }

  goToProjectsList() {
    stores.pageState.hideModal();
    this.props.router.navigate(ROUTES.FORMS);
  }

  /*
   * modal steps navigation
   */

  displayStep(targetStep) {
    const currentStep = this.state.currentStep;
    const previousStep = this.state.previousStep;

    if (targetStep === currentStep) {
      return;
    } else if (targetStep === previousStep) {
      this.setState({
        currentStep: previousStep,
        previousStep: null,
      });
    } else {
      this.setState({
        currentStep: targetStep,
        previousStep: currentStep,
      });
    }

    if (this.props.onSetModalTitle) {
      const stepTitle = this.getStepTitle(targetStep);
      const baseTitle = this.getBaseTitle();
      this.props.onSetModalTitle(`${baseTitle}: ${stepTitle}`);
    }
  }

  displayPreviousStep() {
    if (this.state.previousStep) {
      this.displayStep(this.state.previousStep);
    }
  }

  /*
   * handling asset creation
   */

  onLoadAssetCompleted(response) {
    if (this.state.formAsset?.uid === response.uid) {
      this.setState({formAsset: response});
    }
  }

  onUpdateAssetCompleted(response) {
    if (
      this.props.context === PROJECT_SETTINGS_CONTEXTS.REPLACE ||
      this.props.context === PROJECT_SETTINGS_CONTEXTS.NEW
    ) {
      this.goToFormLanding();
    }

    // This handles the case when the asset was edited outside the Settings,
    // e.g. the title editor in the header.
    if (
      this.props.context === PROJECT_SETTINGS_CONTEXTS.EXISTING &&
      response.uid === this.state.formAsset?.uid
    ) {
      this.setState({
        formAsset: response,
        fields: this.getInitialFieldsFromAsset(response),
      });
    }
  }

  onUpdateAssetFailed() {
    if (
      this.props.context === PROJECT_SETTINGS_CONTEXTS.REPLACE ||
      this.props.context === PROJECT_SETTINGS_CONTEXTS.NEW
    ) {
      this.resetApplyTemplateButton();
    }
  }

  onCloneAssetCompleted(asset) {
    if (
      (this.props.context === PROJECT_SETTINGS_CONTEXTS.REPLACE || this.props.context === PROJECT_SETTINGS_CONTEXTS.NEW) &&
      this.state.currentStep === this.STEPS.CHOOSE_TEMPLATE
    ) {
      this.setState({
        formAsset: asset,
        fields: this.getInitialFieldsFromAsset(asset),
      });
      this.resetApplyTemplateButton();
      this.displayStep(this.STEPS.PROJECT_DETAILS);
    }
  }

  onCloneAssetFailed() {
    if (
      this.props.context === PROJECT_SETTINGS_CONTEXTS.REPLACE ||
      this.props.context === PROJECT_SETTINGS_CONTEXTS.NEW
    ) {
      this.resetApplyTemplateButton();
    }
  }

  getOrCreateFormAsset() {
    const assetPromise = new Promise((resolve, reject) => {
      if (this.state.formAsset) {
        resolve(this.state.formAsset);
      } else {
        dataInterface.createResource({
          asset_type: 'empty',
        }).done((asset) => {
          resolve(asset);
        }).fail((r) => {
          reject(t('Error: asset could not be created.') + ` (code: ${r.statusText})`);
        });
      }
    });
    return assetPromise;
  }

  getSettingsForEndpoint() {
    return JSON.stringify({
      description: this.state.fields.description,
      sector: this.state.fields.sector,
      country: this.state.fields.country,
      operational_purpose: this.state.fields.operational_purpose,
      collects_pii: this.state.fields.collects_pii,
    });
  }

  createAssetAndOpenInBuilder() {
    dataInterface.createResource({
      name: this.state.fields.name,
      settings: this.getSettingsForEndpoint(),
      asset_type: 'survey',
    }).done((asset) => {
      this.goToFormBuilder(asset.uid);
    }).fail((r) => {
      notify.error(t('Error: new project could not be created.') + ` (code: ${r.statusText})`);
    });
  }

  updateAndOpenAsset() {
    actions.resources.updateAsset(
      this.state.formAsset.uid,
      {
        name: this.state.fields.name,
        settings: this.getSettingsForEndpoint(),
      }
    );
  }

  applyTemplate(evt) {
    evt.preventDefault();

    this.setState({
      isApplyTemplatePending: true,
      applyTemplateButton: t('Please wait…'),
    });

    if (this.props.context === PROJECT_SETTINGS_CONTEXTS.REPLACE) {
      actions.resources.updateAsset(
        this.state.formAsset.uid,
        {
          clone_from: this.state.chosenTemplateUid,
          name: this.state.formAsset.name,
        }
      );
    } else {
      actions.resources.cloneAsset({
        uid: this.state.chosenTemplateUid,
        new_asset_type: 'survey',
      });
    }
  }

  importFromURL(evt) {
    evt.preventDefault();

    if (isAValidUrl(this.state.importUrl)) {
      this.setState({
        isImportFromURLPending: true,
        importUrlButtonEnabled: false,
        importUrlButton: t('Retrieving form, please wait...'),
      });

      this.getOrCreateFormAsset().then(
        (asset) => {
          this.setState({formAsset: asset});
          const importUrl = this.state.importUrl;

          this.applyUrlToAsset(importUrl, asset).then(
            (data) => {
              dataInterface.getAsset({id: data.uid}).done((finalAsset) => {
                if (this.props.context === PROJECT_SETTINGS_CONTEXTS.REPLACE) {
                  // when replacing, we omit PROJECT_DETAILS step
                  this.goToFormLanding();
                } else {
                  this.applyAssetToState(finalAsset);
                  this.displayStep(this.STEPS.PROJECT_DETAILS);
                }
              }).fail(() => {
                this.resetImportUrlButton();
                notify.error(t('Failed to reload project after import!'));
              });
            },
            (response) => {
              this.resetImportUrlButton();
              const errLines = [];
              errLines.push(t('Import Failed!'));
              if (importUrl) {
                errLines.push(<code>Name: {this.getFilenameFromURI(importUrl)}</code>);
              }
              if (response.messages.error) {
                errLines.push(<code>{response.messages.error_type}: {response.messages.error}</code>);
              }
              notify.error(join(errLines, <br/>));
            }
          );
        },
        () => {
          notify.error(t('Could not initialize XLSForm import!'));
        }
      );
    }
  }

  onFileDrop(files) {
    if (files.length >= 1) {
      this.setState({isUploadFilePending: true});

      this.getOrCreateFormAsset().then(
        (asset) => {
          this.applyFileToAsset(files[0], asset).then(
            (data) => {
              dataInterface.getAsset({id: data.uid}).done((finalAsset) => {
                // TODO: Getting asset outside of actions.resources.loadAsset
                // is not going to notify all the listeners, causing some hard
                // to identify bugs.
                // Until we switch this code to use actions we HACK it so other
                // places are notified.
                // See: https://github.com/kobotoolbox/kpi/issues/3919
                actions.resources.loadAsset.completed(finalAsset);

                if (this.props.context === PROJECT_SETTINGS_CONTEXTS.REPLACE) {
                  // when replacing, we omit PROJECT_DETAILS step
                  this.goToFormLanding();
                } else {
                  this.applyAssetToState(finalAsset);
                  this.displayStep(this.STEPS.PROJECT_DETAILS);
                }
              }).fail(() => {
                this.setState({isUploadFilePending: false});
                notify.error(t('Failed to reload project after upload!'));
              });
            },
            (response) => {
              this.setState({isUploadFilePending: false});
              const errLines = [];
              errLines.push(t('Import Failed!'));
              if (files[0].name) {
                errLines.push(<code>Name: ${files[0].name}</code>);
              }
              if (response.messages.error) {
                errLines.push(<code>{response.messages.error_type}: {escapeHtml(response.messages.error)}</code>);
              }
              notify.error(join(errLines, <br/>));
            }
          );
        },
        () => {
          this.setState({isUploadFilePending: false});
          notify.error(t('Could not import XLSForm!'));
        }
      );
    }
  }

  hasFieldError(fieldName) {
    return this.state.fieldsWithErrors.includes(fieldName);
  }

  handleSubmit(evt) {
    evt.preventDefault();

    const fieldsWithErrors = [];

    // simple non-empty name validation
    if (!this.state.fields.name.trim()) {
      fieldsWithErrors.push('name');
    }

    // superuser-configured metadata
    if (
      envStore.data.getProjectMetadataField('description').required &&
      !this.state.fields.description.trim()
    ) {
      fieldsWithErrors.push('description');
    }
    if (
      envStore.data.getProjectMetadataField('sector').required &&
      !this.state.fields.sector
    ) {
      fieldsWithErrors.push('sector');
    }
    if (
      envStore.data.getProjectMetadataField('country').required &&
      !this.state.fields.country?.length
    ) {
      fieldsWithErrors.push('country');
    }
    if (
      envStore.data.getProjectMetadataField('operational_purpose').required &&
      !this.state.fields.operational_purpose
    ) {
      fieldsWithErrors.push('operational_purpose');
    }
    if (
      envStore.data.getProjectMetadataField('collects_pii').required &&
      !this.state.fields.collects_pii
    ) {
      fieldsWithErrors.push('collects_pii');
    }

    // Will set either an empty array (no errors) or a list of fieldNames.
    this.setState({fieldsWithErrors: fieldsWithErrors});

    if (fieldsWithErrors.length >= 1) {
      notify.error(t('Some fields contain errors!'));
      return;
    }

    this.setState({isSubmitPending: true});

    if (this.state.formAsset) {
      this.updateAndOpenAsset();
    } else {
      this.createAssetAndOpenInBuilder();
    }
  }

  /*
   * rendering
   */

  getNameInputLabel(nameVal) {
    let label = t('Project Name');
    if (nameVal.length >= NAME_MAX_LENGTH - 99) {
      label += ` (${t('##count## characters left').replace('##count##', NAME_MAX_LENGTH - nameVal.length)})`;
    }
    return label;
  }

  renderChooseTemplateButton() {
    return (
      <button onClick={this.displayStep.bind(this, this.STEPS.CHOOSE_TEMPLATE)}>
        <i className='k-icon k-icon-template' />
        {t('Use a template')}
      </button>
    );
  }

  renderStepFormSource() {
    return (
      <bem.FormModal__form className='project-settings project-settings--form-source'>
        {this.props.context !== PROJECT_SETTINGS_CONTEXTS.REPLACE &&
          <bem.Modal__subheader>
            {t('Choose one of the options below to continue. You will be prompted to enter name and other details in further steps.')}
          </bem.Modal__subheader>
        }

        <bem.FormModal__item m='form-source-buttons'>
          {this.props.context === PROJECT_SETTINGS_CONTEXTS.NEW &&
            <button onClick={this.displayStep.bind(this, this.STEPS.PROJECT_DETAILS)}>
              <i className='k-icon k-icon-edit' />
              {t('Build from scratch')}
            </button>
          }

          {this.props.context === PROJECT_SETTINGS_CONTEXTS.NEW &&
            this.renderChooseTemplateButton()
          }

          <button onClick={this.displayStep.bind(this, this.STEPS.UPLOAD_FILE)}>
            <i className='k-icon k-icon-upload' />
            {t('Upload an XLSForm')}
          </button>

          <button onClick={this.displayStep.bind(this, this.STEPS.IMPORT_URL)}>
            <i className='k-icon k-icon-link' />
            {t('Import an XLSForm via URL')}
          </button>

          {this.props.context !== PROJECT_SETTINGS_CONTEXTS.NEW &&
            this.renderChooseTemplateButton()
          }
        </bem.FormModal__item>
      </bem.FormModal__form>
    );
  }

  renderStepChooseTemplate() {
    return (
      <bem.FormModal__form className='project-settings project-settings--choose-template'>
        <TemplatesList onSelectTemplate={this.onTemplateChange}/>

        <bem.Modal__footer>
          {this.renderBackButton()}

          <bem.KoboButton
            m='blue'
            type='submit'
            onClick={this.applyTemplate}
            disabled={!this.state.chosenTemplateUid || this.state.isApplyTemplatePending}
          >
            {this.state.applyTemplateButton}
          </bem.KoboButton>
        </bem.Modal__footer>
      </bem.FormModal__form>
    );
  }

  renderStepUploadFile() {
    return (
      <bem.FormModal__form className='project-settings'>
        <bem.Modal__subheader>
          {t('Import an XLSForm from your computer.')}
        </bem.Modal__subheader>

        {!this.state.isUploadFilePending &&
          <Dropzone
            onDrop={this.onFileDrop.bind(this)}
            multiple={false}
            className='kobo-dropzone'
            activeClassName='dropzone-active'
            rejectClassName='dropzone-reject'
            accept={validFileTypes()}
          >
            <i className='k-icon k-icon-file-xls' />
            {t(' Drag and drop the XLSForm file here or click to browse')}
          </Dropzone>
        }
        {this.state.isUploadFilePending &&
          <div className='dropzone'>
            <LoadingSpinner message={t('Uploading file…')}/>
          </div>
        }

        <bem.Modal__footer>
          {this.renderBackButton()}
        </bem.Modal__footer>
      </bem.FormModal__form>
    );
  }

  renderStepImportUrl() {
    return (
      <bem.FormModal__form className='project-settings project-settings--import-url'>
        <div className='intro'>
          {t('Enter a valid XLSForm URL in the field below.')}<br/>

          { envStore.isReady &&
            envStore.data.support_url &&
            <a href={envStore.data.support_url + VIA_URL_SUPPORT_URL} target='_blank'>
              {t('Having issues? See this help article.')}
            </a>
          }
        </div>

        <bem.FormModal__item>
          <TextBox
            type='url'
            label={t('URL')}
            placeholder='https://'
            value={this.state.importUrl}
            onChange={this.onImportUrlChange}
          />
        </bem.FormModal__item>

        <bem.Modal__footer>
          {this.renderBackButton()}

          <bem.KoboButton
            m='blue'
            type='submit'
            onClick={this.importFromURL}
            disabled={!this.state.importUrlButtonEnabled}
          >
            {this.state.importUrlButton}
          </bem.KoboButton>
        </bem.Modal__footer>
      </bem.FormModal__form>
    );
  }

  renderStepProjectDetails() {
    const sectorField = envStore.data.getProjectMetadataField('sector');
    const sectors = envStore.data.sector_choices;
    const countryField = envStore.data.getProjectMetadataField('country');
    const countries = envStore.data.country_choices;
    const bothCountryAndSector = sectorField && countryField;
    const operationalPurposeField = envStore.data.getProjectMetadataField('operational_purpose');
    const operationalPurposes = envStore.data.operational_purpose_choices;
    const collectsPiiField = envStore.data.getProjectMetadataField('collects_pii');
    const isSelfOwned = assetUtils.isSelfOwned(this.state.formAsset);
    const descriptionField = envStore.data.getProjectMetadataField('description');

    return (
      <bem.FormModal__form
        onSubmit={this.handleSubmit}
        onChange={this.onProjectDetailsFormChange}
        className={[
          'project-settings',
          'project-settings--project-details',
          this.props.context === PROJECT_SETTINGS_CONTEXTS.BUILDER ? 'project-settings--narrow' : null,
        ].join(' ')}
      >
        {this.props.context === PROJECT_SETTINGS_CONTEXTS.EXISTING &&
          <bem.Modal__footer>
            <bem.KoboButton
              type='submit'
              m='blue'
              onClick={this.handleSubmit}
            >
              {t('Save Changes')}
            </bem.KoboButton>
          </bem.Modal__footer>
        }

        {/* Project Name */}
        <bem.FormModal__item m='wrapper'>
          {/* form builder displays name in different place */}
          {this.props.context !== PROJECT_SETTINGS_CONTEXTS.BUILDER &&
            <bem.FormModal__item>
              <TextBox
                value={this.state.fields.name}
                onChange={this.onNameChange.bind(this)}
                errors={this.hasFieldError('name') ? t('Please enter a title for your project!') : false}
                label={addRequiredToLabel(this.getNameInputLabel(this.state.fields.name))}
                placeholder={t('Enter title of project here')}
                data-cy='title'
              />
            </bem.FormModal__item>
          }

          {/* Description */}
          {descriptionField &&
          <bem.FormModal__item>
            <TextBox
              type='text-multiline'
              value={this.state.fields.description}
              onChange={this.onDescriptionChange.bind(this)}
              errors={this.hasFieldError('description') ? t('Please enter a description for your project') : false}
              label={addRequiredToLabel(descriptionField.label, descriptionField.required)}
              placeholder={t('Enter short description here')}
              data-cy='description'
            />
          </bem.FormModal__item>
          }

          {/* Sector */}
          {sectorField &&
            <bem.FormModal__item m={bothCountryAndSector ? 'sector' : null}>
              <WrappedSelect
                label={addRequiredToLabel(sectorField.label, sectorField.required)}
                value={this.state.fields.sector}
                onChange={this.onAnyFieldChange.bind(this, 'sector')}
                options={sectors}
                isLimitedHeight
                menuPlacement='top'
                isClearable
                error={this.hasFieldError('sector') ? t('Please choose a sector') : false}
                data-cy='sector'
              />
            </bem.FormModal__item>
          }

          {/* Country */}
          {countryField &&
            <bem.FormModal__item m={bothCountryAndSector ? 'country' : null}>
              <WrappedSelect
                label={addRequiredToLabel(countryField.label, countryField.required)}
                isMulti
                value={this.state.fields.country}
                onChange={this.onAnyFieldChange.bind(this, 'country')}
                options={countries}
                isLimitedHeight
                menuPlacement='top'
                isClearable
                error={this.hasFieldError('country') ? t('Please select at least one country') : false}
                data-cy='country'
              />
            </bem.FormModal__item>
          }

          {/* Operational Purpose of Data */}
          {operationalPurposeField &&
            <bem.FormModal__item>
              <WrappedSelect
                label={addRequiredToLabel(operationalPurposeField.label, operationalPurposeField.required)}
                value={this.state.fields.operational_purpose}
                onChange={this.onAnyFieldChange.bind(this, 'operational_purpose')}
                options={operationalPurposes}
                isLimitedHeight
                isClearable
                error={this.hasFieldError('operational_purpose') ? t('Please specify the operational purpose of your project') : false}
              />
            </bem.FormModal__item>
          }

          {/* Does this project collect personally identifiable information? */}
          {collectsPiiField &&
            <bem.FormModal__item>
              <WrappedSelect
                label={addRequiredToLabel(collectsPiiField.label, collectsPiiField.required)}
                value={this.state.fields.collects_pii}
                onChange={this.onAnyFieldChange.bind(this, 'collects_pii')}
                options={[
                  {value: 'Yes', label: t('Yes')},
                  {value: 'No', label: t('No')},
                ]}
                isClearable
                error={this.hasFieldError('collects_pii') ? t('Please indicate whether or not your project collects personally identifiable information') : false}
              />
            </bem.FormModal__item>
          }

          {(this.props.context === PROJECT_SETTINGS_CONTEXTS.NEW || this.props.context === PROJECT_SETTINGS_CONTEXTS.REPLACE) &&
            <bem.Modal__footer>
              {/* Don't allow going back if asset already exist */}
              {!this.state.formAsset &&
                this.renderBackButton()
              }

              <bem.KoboButton
                m='blue'
                type='submit'
                onClick={this.handleSubmit}
                disabled={this.state.isSubmitPending}
              >
                {this.state.isSubmitPending && t('Please wait…')}
                {!this.state.isSubmitPending && this.props.context === PROJECT_SETTINGS_CONTEXTS.NEW && t('Create project')}
                {!this.state.isSubmitPending && this.props.context === PROJECT_SETTINGS_CONTEXTS.REPLACE && t('Save')}
              </bem.KoboButton>
            </bem.Modal__footer>
          }

          {userCan('manage_asset', this.state.formAsset) && this.props.context === PROJECT_SETTINGS_CONTEXTS.EXISTING &&
            <bem.FormModal__item>
              <bem.FormModal__item m='inline'>
                {this.isArchived() &&
                  <Button
                    type='frame'
                    color='blue'
                    size='l'
                    label={t('Unarchive Project')}
                    onClick={this.unarchiveProject}
                  />
                }

                {this.isArchivable() &&
                  <Button
                    type='frame'
                    color='red'
                    size='l'
                    label={t('Archive Project')}
                    onClick={this.archiveProject}
                  />
                }
              </bem.FormModal__item>

              {this.isArchivable() &&
                <bem.FormModal__item m='inline'>
                  {t('Archive project to stop accepting submissions.')}
                </bem.FormModal__item>
              }
              {this.isArchived() &&
                <bem.FormModal__item m='inline'>
                  {t('Unarchive project to resume accepting submissions.')}
                </bem.FormModal__item>
              }

            </bem.FormModal__item>
          }

          {isSelfOwned && this.props.context === PROJECT_SETTINGS_CONTEXTS.EXISTING &&
            <bem.FormModal__item>
              <Button
                type='full'
                color='red'
                size='l'
                label={t('Delete Project and Data')}
                onClick={this.deleteProject}
              />
            </bem.FormModal__item>
          }
        </bem.FormModal__item>
      </bem.FormModal__form>
    );
  }

  renderBackButton() {
    if (this.state.previousStep) {
      const isBackButtonDisabled = (
        this.state.isSubmitPending ||
        this.state.isApplyTemplatePending ||
        this.state.isImportFromURLPending ||
        this.state.isUploadFilePending
      );
      return (
        <bem.KoboButton
          m='whitegray'
          type='button'
          onClick={this.displayPreviousStep}
          disabled={isBackButtonDisabled}
        >
          {t('Back')}
        </bem.KoboButton>
      );
    } else {
      return false;
    }
  }

  render() {
    if (this.isLoading()) {
      return (<LoadingSpinner/>);
    }

    if (this.isReplacingFormLocked()) {
      return (
        <bem.Loading>
          <bem.Loading__inner>
            <i className='k-icon k-icon-alert'/>
            {t("Form replacing is not available due to form's Locking Profile restrictions.")}
          </bem.Loading__inner>
        </bem.Loading>
      );
    }

    switch (this.state.currentStep) {
      case this.STEPS.FORM_SOURCE: return this.renderStepFormSource();
      case this.STEPS.CHOOSE_TEMPLATE: return this.renderStepChooseTemplate();
      case this.STEPS.UPLOAD_FILE: return this.renderStepUploadFile();
      case this.STEPS.IMPORT_URL: return this.renderStepImportUrl();
      case this.STEPS.PROJECT_DETAILS: return this.renderStepProjectDetails();
      default:
        throw new Error(`Unknown step: ${this.state.currentStep}!`);
    }
  }
}

reactMixin(ProjectSettings.prototype, Reflux.ListenerMixin);
reactMixin(ProjectSettings.prototype, mixins.droppable);
// NOTE: dmix mixin is causing a full asset load after component mounts
reactMixin(ProjectSettings.prototype, mixins.dmix);

ProjectSettings.contextTypes = {router: PropTypes.object};

export default withRouter(ProjectSettings);
