import React, {useState} from 'react';
import type {AssetResponse, ProjectViewAsset} from 'js/dataInterface';
import Button from 'js/components/common/button';
import actionsStyles from './projectActions.module.scss';
import BulkDeletePrompt from './bulkActions/bulkDeletePrompt';
import {userCan} from 'js/components/permissions/utils';

interface ProjectBulkActionsProps {
  /** A list of selected assets for bulk operations. */
  assets: Array<AssetResponse | ProjectViewAsset>;
}

function userCanDeleteAssets(assets: Array<AssetResponse | ProjectViewAsset>) {
  return assets.every((asset) => userCan('manage_asset', asset));
}

/**
 * "Bulk" Quick Actions buttons. Use these when two or more projects are
 * selected in the Project Table.
 */
export default function ProjectBulkActions(props: ProjectBulkActionsProps) {
  const [isDeletePromptOpen, setIsDeletePromptOpen] = useState(false);
  const canBulkDelete = userCanDeleteAssets(props.assets);

  let tooltipForDelete = t('Delete projects');
  if (canBulkDelete) {
    tooltipForDelete = t('Delete ##count## projects').replace(
      '##count##',
      String(props.assets.length)
    );
  }

  return (
    <div className={actionsStyles.root}>
      {/* Archive / Unarchive - Bulk action not supported yet */}
      <span data-tip={t('Archive/Unarchive')} className='right-tooltip'>
        <Button
          isDisabled
          type='bare'
          color='storm'
          size='s'
          startIcon='archived'
        />
      </span>

      {/* Share - Bulk action not supported yet */}
      <span data-tip={t('Share projects')} className='right-tooltip'>
        <Button
          isDisabled
          type='bare'
          color='storm'
          size='s'
          startIcon='user-share'
        />
      </span>

      {/* Delete */}
      <span data-tip={tooltipForDelete} className='right-tooltip'>
        <Button
          isDisabled={!canBulkDelete}
          type='bare'
          color='storm'
          size='s'
          startIcon='trash'
          onClick={() => setIsDeletePromptOpen(true)}
        />
      </span>

      {isDeletePromptOpen && (
        <BulkDeletePrompt
          assetUids={props.assets.map((asset) => asset.uid)}
          onRequestClose={() => setIsDeletePromptOpen(false)}
        />
      )}
    </div>
  );
}
