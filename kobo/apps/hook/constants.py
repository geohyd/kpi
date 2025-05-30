# coding: utf-8
from enum import Enum


HOOK_LOG_FAILED = 0
HOOK_LOG_PENDING = 1
HOOK_LOG_SUCCESS = 2

class HookLogStatus(Enum):
    FAILED = HOOK_LOG_FAILED
    PENDING = HOOK_LOG_PENDING
    SUCCESS = HOOK_LOG_SUCCESS

HOOK_EVENT_SUBMIT = 'on_submit'
HOOK_EVENT_EDIT = 'on_edit'
HOOK_EVENT_DELETE = 'on_delete'
HOOK_EVENT_VALIDATION = 'on_validation_status_change'

class HookEvent(Enum):
    ON_SUBMIT = HOOK_EVENT_SUBMIT,
    ON_EDIT = HOOK_EVENT_EDIT,
    ON_DELETE = HOOK_EVENT_DELETE,
    ON_VALIDATION_STATUS_CHANGE = HOOK_EVENT_VALIDATION,

KOBO_INTERNAL_ERROR_STATUS_CODE = None

SUBMISSION_PLACEHOLDER = '%SUBMISSION%'
