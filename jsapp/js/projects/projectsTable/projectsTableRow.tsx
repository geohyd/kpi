import React from 'react';
import {Link} from 'react-router-dom';
import {ROUTES} from 'js/router/routerConstants';
import {PROJECT_FIELDS} from 'js/projects/projectViews/constants';
import type {
  ProjectFieldName,
  ProjectFieldDefinition,
} from 'js/projects/projectViews/constants';
import Badge from 'js/components/common/badge';
import Avatar from 'js/components/common/avatar';
import AssetName from 'js/components/common/assetName';
import AssetStatusBadge from 'js/components/common/assetStatusBadge';
import {formatTime} from 'js/utils';
import type {AssetResponse, ProjectViewAsset} from 'js/dataInterface';
import assetUtils, {isSelfOwned} from 'js/assetUtils';
import styles from './projectsTableRow.module.scss';
import classNames from 'classnames';
import Checkbox from 'js/components/common/checkbox';

interface ProjectsTableRowProps {
  asset: AssetResponse | ProjectViewAsset;
  highlightedFields: ProjectFieldName[];
  visibleFields: ProjectFieldName[];
  isSelected: boolean;
  onSelectRequested: (isSelected: boolean) => void;
}

export default function ProjectsTableRow(props: ProjectsTableRowProps) {
  const toggleCheckbox = () => {
    props.onSelectRequested(!props.isSelected);
  };

  const renderColumnContent = (field: ProjectFieldDefinition) => {
    switch (field.name) {
      case 'name':
        return (
          <Link to={ROUTES.FORM_SUMMARY.replace(':uid', props.asset.uid)}>
            <AssetName asset={props.asset} />
          </Link>
        );
      case 'description':
        return props.asset.settings.description;
      case 'status':
        return <AssetStatusBadge asset={props.asset} />;
      case 'ownerUsername':
        if (isSelfOwned(props.asset)) {
          return t('me');
        } else {
          return <Avatar username={props.asset.owner__username} />;
        }
      case 'ownerFullName':
        return 'owner__name' in props.asset ? props.asset.owner__name : null;
      case 'ownerEmail':
        return 'owner__email' in props.asset ? props.asset.owner__email : null;
      case 'ownerOrganization':
        return 'owner__organization' in props.asset
          ? props.asset.owner__organization
          : null;
      case 'dateModified':
        return formatTime(props.asset.date_modified);
      case 'dateDeployed':
        if (
          'date_deployed' in props.asset &&
          props.asset.date_deployed !== null
        ) {
          return formatTime(props.asset.date_deployed);
        }
        return null;
      case 'sector':
        return assetUtils.getSectorDisplayString(props.asset);
      case 'countries':
        if (Array.isArray(props.asset.settings.country)) {
          return props.asset.settings.country.map((country) => (
            <Badge
              key={country.value}
              color='cloud'
              size='m'
              label={country.label}
            />
          ));
        } else if (typeof props.asset.settings.country === 'string') {
          <Badge color='cloud' size='m' label={props.asset.settings.country} />;
        }
        return null;
      case 'languages':
        return assetUtils.getLanguagesDisplayString(props.asset);
      case 'submissions':
        return (
          <Badge
            color='cloud'
            size='m'
            label={props.asset.deployment__submission_count}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className={classNames(styles.row, styles.rowTypeProject)}>
      {/* First column is always visible and displays a checkbox. */}
      <div
        className={styles.cell}
        data-field='checkbox'
        onClick={toggleCheckbox} // Treat whole cell as checkbox
      >
        <Checkbox
          checked={props.isSelected}
          onChange={props.onSelectRequested}
        />
      </div>

      {Object.values(PROJECT_FIELDS).map((field: ProjectFieldDefinition) => {
        // Hide not visible fields.
        if (!props.visibleFields.includes(field.name)) {
          return null;
        }

        return (
          <div
            className={classNames({
              [styles.cell]: true,
              [styles.cellHighlighted]: props.highlightedFields.includes(
                field.name
              ),
            })}
            onClick={() => {if (field.name !== PROJECT_FIELDS.name.name) {toggleCheckbox();}}
            }
            // This attribute is being used for styling and for ColumnResizer
            data-field={field.name}
            key={field.name}
          >
            {renderColumnContent(field)}
          </div>
        );
      })}
    </div>
  );
}
