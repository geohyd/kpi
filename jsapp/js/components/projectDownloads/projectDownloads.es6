import React from 'react';
import autoBind from 'react-autobind';
import {bem} from 'js/bem';
import {stores} from 'js/stores';
import DocumentTitle from 'react-document-title';
import ProjectExportsCreator from 'js/components/projectDownloads/projectExportsCreator';
import ProjectExportsList from 'js/components/projectDownloads/projectExportsList';
import LegacyExports from 'js/components/projectDownloads/legacyExports';
import ExportTypeSelector from 'js/components/projectDownloads/exportTypeSelector';
import exportsStore from 'js/components/projectDownloads/exportsStore';

/**
 * @prop {object} asset
 */
export default class ProjectDownloads extends React.Component {
  constructor(props){
    super(props);
    this.state = {selectedExportType: exportsStore.getExportType()};
    this.unlisteners = [];
    autoBind(this);
  }

  componentDidMount() {
    this.unlisteners.push(
      exportsStore.listen(this.onExportsStoreChange),
    );
  }

  componentWillUnmount() {
    this.unlisteners.forEach((clb) => {clb();});
  }

  onExportsStoreChange() {
    this.setState({selectedExportType: exportsStore.getExportType()});
  }

  renderLegacy() {
    return (
      <React.Fragment>
        <LegacyExports asset={this.props.asset} />
      </React.Fragment>
    );
  }

  renderNonLegacy() {
    if (stores.session.isLoggedIn) {
      return (
        <React.Fragment>
          <ProjectExportsCreator asset={this.props.asset} />
          <ProjectExportsList asset={this.props.asset} hideWhenEmpty/>
        </React.Fragment>
      );
    } else {
      return (
        <React.Fragment>
          <bem.ProjectDownloads__selectorRow>
            <ExportTypeSelector/>
          </bem.ProjectDownloads__selectorRow>
          <ProjectExportsList asset={this.props.asset}/>
        </React.Fragment>
      );
    }
  }

  render() {
    var docTitle = this.props.asset.name || t('Untitled');
    return (
      <DocumentTitle title={`${docTitle} | KoboToolbox`}>
        <bem.FormView className='project-downloads'>
          <bem.FormView__row>
            <bem.FormView__cell m={['page-title']}>
              {t('Downloads')}
            </bem.FormView__cell>

            {this.state.selectedExportType.isLegacy &&
              this.renderLegacy()
            }

            {!this.state.selectedExportType.isLegacy &&
              this.renderNonLegacy()
            }
          </bem.FormView__row>
        </bem.FormView>
      </DocumentTitle>
    );
  }
}
