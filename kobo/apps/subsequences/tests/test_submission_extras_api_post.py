from copy import deepcopy
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

from constance.test import override_config
from jsonschema import validate
from rest_framework.test import APITestCase

from kobo.apps.languages.models.language import Language, LanguageRegion
from kobo.apps.languages.models.transcription import (
    TranscriptionService, TranscriptionServiceLanguageM2M)
from kpi.utils.fuzzy_int import FuzzyInt
from ..constants import GOOGLETS, make_async_cache_key
from ..models import SubmissionExtras
from .test_submission_extras_content import sample_asset


class ValidateSubmissionTest(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username='someuser', email='user@example.com')

        self.asset = sample_asset(advanced_features={})
        self.asset.owner = user
        self.asset.save()
        self.asset.deploy(backend='mock', active=True)
        self.asset_uid = self.asset.uid
        self.asset_url = f'/api/v2/assets/{self.asset.uid}/?format=json'
        self.client.force_login(user)

    def set_asset_advanced_features(self, features):
        self.asset.advanced_features = features
        self.asset.save()

    def test_asset_post_submission_extra_with_transcript(self):
        self.set_asset_advanced_features({'transcript': {'values': ['q1']}})
        resp = self.client.get(self.asset_url)
        schema = resp.json()['advanced_submission_schema']
        package = {
            'submission': 'abc123-def456',
            'q1': {
              'transcript': {
                'value': 'they said hello',
              }
            }
        }

        validate(package, schema)
        rr = self.client.post(schema['url'], package, format='json')

        package['q1']['transcript'] = {'value': 'they said goodbye'}
        validate(package, schema)
        rr = self.client.post(schema['url'], package, format='json')
        q1transcript = rr.json()['q1']['transcript']
        assert q1transcript['value'] == 'they said goodbye'

    def test_translation_revisions_stored_properly(self):
        self.set_asset_advanced_features({
            'translation': {
                'values': ['q1'],
                'languages': ['tx1', 'tx2'],
            }
        })
        tx_instance = next(self.asset.get_advanced_feature_instances())
        first_post = {
            'q1': {
                'translation': {
                    'tx1': {
                        'value': 'VAL1'
                    }
                }
            }
        }
        summ = tx_instance.compile_revised_record({}, edits=first_post)
        assert summ['q1']['translation']['tx1']['value'] == 'VAL1'
        assert len(summ['q1']['translation']['tx1']['revisions']) == 0
        summ1 = deepcopy(summ)
        second_post = {
            'q1': {
                'translation': {
                    'tx1': {
                        'value': 'VAL2',
                    }
                }
            }
        }


class TranscriptFieldRevisionsOnlyTests(ValidateSubmissionTest):
    def setUp(self):
        ValidateSubmissionTest.setUp(self)
        self.set_asset_advanced_features({
            'transcript': {
                'values': ['q1'],
            }
        })
        self.act1 = next(self.asset.get_advanced_feature_instances())

    def test_simplest(self):
        field = self.act1.revise_field({
            'value': 'V1',
            'revisions': [],
            'dateCreated': '1',
            'dateModified': '1',
        }, {
            'value': 'V2',
        })
        assert field['value'] == 'V2'

    def test_send_delete_character(self):
        field = self.act1.revise_field({
            'value': 'V1',
            'revisions': [],
            'dateCreated': '1',
            'dateModified': '1',
        }, {
            'value': self.act1.DELETE,
        })
        assert field == {}


class TranslatedFieldRevisionsOnlyTests(ValidateSubmissionTest):
    def setUp(self):
        ValidateSubmissionTest.setUp(self)
        self.set_asset_advanced_features({
            'translation': {
                'values': ['q1'],
                'languages': ['tx1', 'tx2'],
            }
        })
        self.txi = next(self.asset.get_advanced_feature_instances())

    def test_simplest(self):
        field = self.txi.revise_field({
            'tx1': {
                'value': 'V1',
                'revisions': [],
                'dateCreated': '1',
                'dateModified': '1',
            }
        }, {
            'tx1': {
                'value': 'V2',
            }
        })

        assert 'tx1' in field
        assert field['tx1']['value'] == 'V2'
        assert len(field['tx1']['revisions']) == 1
        assert field['tx1']['dateCreated'] == '1'
        assert 'dateCreated' not in field['tx1']['revisions'][0]
        assert 'dateModified' in field['tx1']
        assert field['tx1']['dateCreated'] == '1'

    def test_append_empty_string(self):
        field = self.txi.revise_field({
            'tx1': {
                'value': 'V1',
                'revisions': [],
                'dateCreated': '1',
                'dateModified': '1',
            }
        }, {
            'tx1': {
                'value': '',
            }
        })

        assert 'tx1' in field
        assert field['tx1']['value'] == ''

    def test_send_delete_character(self):
        field = self.txi.revise_field({
            'tx1': {
                'value': 'V1',
                'revisions': [],
                'dateCreated': '1',
                'dateModified': '1',
            }
        }, {
            'tx1': {
                'value': self.txi.DELETE,
            }
        })
        assert 'tx1' not in field

    def test_date_created_is_pulled_from_last_revision(self):
        field = self.txi.revise_field({
            'tx1': {
                'value': 'V3',
                'revisions': [
                    {'value': 'V2', 'dateModified': 'B'},
                    {'value': 'V1', 'dateModified': 'A'},
                ]
            }
        }, {
            'tx1': {
                'value': 'V4',
            }
        })
        for revision in field['tx1']['revisions']:
            assert 'revisions' not in revision
        assert field['tx1']['dateCreated'] == 'A'

    def test_second_translation_comes_in(self):
        field = self.txi.revise_field({
            'tx1': {
                'value': 'T1',
                'dateModified': 'A',
                'dateCreated': 'A',
                'revisions': []
            }
        }, {
            'tx2': {
                'value': 'T2',
            }
        })
        for tx in ['tx1', 'tx2']:
            fx = field[tx]
            assert 'dateCreated' in fx
            assert 'dateModified' in fx
            assert 'revisions' in fx
        assert field['tx1']['dateCreated'] == 'A'

    def test_change_language_list(self):
        field = self.txi.revise_field({
            'tx1': {
                'value': 'T1',
                'dateModified': 'A',
                'dateCreated': 'A',
                'revisions': []
            }
        }, {
            'tx2': {
                'value': 'T2',
            }
        })
        self.set_asset_advanced_features({
            'translation': {
                'languages': [
                    'tx1', 'tx3'
                ]
            }
        })
        resp = self.client.get(self.asset_url)
        schema = resp.json()['advanced_submission_schema']
        package = {'submission': 'abc123-def456'}
        package['q1'] = {
            'transcript': {
                'value': 'they said hello',
            },
        }
        # validate(package, schema)


class GoogleTranscriptionSubmissionTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='someuser', email='user@example.com')
        self.asset = sample_asset(advanced_features={'transcript': {'values': ['q1']}})
        self.asset.owner = self.user
        self.asset.save()
        self.asset.deploy(backend='mock', active=True)
        self.asset_url = f'/api/v2/assets/{self.asset.uid}/?format=json'
        self.client.force_login(self.user)
        service = TranscriptionService.objects.create(code='goog')
        language = Language.objects.create(name='', code='')
        language_region = LanguageRegion.objects.create(language=language, name='', code='')
        TranscriptionServiceLanguageM2M.objects.create(
            language=language,
            region=language_region,
            service=service
        )

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    @override_config(ASR_MT_INVITEE_USERNAMES='*')
    @patch('google.cloud.speech.SpeechClient')
    @patch('google.cloud.storage.Client')
    def test_google_transcript_post(self, m1, m2):
        url = reverse('advanced-submission-post', args=[self.asset.uid])
        submission_id = 'abc123-def456'
        submission = {
            '__version__': self.asset.latest_deployed_version.uid,
            'q1': 'audio_conversion_test_clip.mp4',
            '_uuid': submission_id,
            '_attachments': [
                {
                    'id': 1,
                    'filename': 'someuser/audio_conversion_test_clip.mp4',
                    'mimetype': 'video/mp4',
                },
            ],
            '_submitted_by': self.user.username
        }
        self.asset.deployment.mock_submissions([submission])

        data = {
            'submission': submission_id,
            'q1': {GOOGLETS: {'status': 'requested', 'languageCode': ''}}
        }
        with self.assertNumQueries(FuzzyInt(51, 55)):
            res = self.client.post(url, data, format='json')
        self.assertContains(res, 'complete')
        with self.assertNumQueries(FuzzyInt(20, 24)):
            self.client.post(url, data, format='json')

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
    @override_config(ASR_MT_INVITEE_USERNAMES='*')
    @patch('google.cloud.storage.Client')
    @patch('googleapiclient.discovery.build')
    def test_google_transcript_slow_post(self, m1, m2):
        """Tests when slow running operation has already started"""
        url = reverse('advanced-submission-post', args=[self.asset.uid])
        submission_id = 'abc123-def456'
        xpath = 'q1'
        source = ''
        operation_name = 'testop'
        cache.set(make_async_cache_key(self.user.pk, submission_id, xpath, source), operation_name)
        submission = {
            '__version__': self.asset.latest_deployed_version.uid,
            'q1': 'audio_conversion_test_clip.mp4',
            '_uuid': submission_id,
            '_attachments': [],
            '_submitted_by': self.user.username
        }
        self.asset.deployment.mock_submissions([submission])

        data = {
            'submission': submission_id,
            'q1': {GOOGLETS: {'status': 'requested', 'languageCode': ''}}
        }
        res = self.client.post(url, data, format='json')
        self.assertContains(res, 'complete')


    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    def test_google_transcript_permissions(self):
        url = reverse('advanced-submission-post', args=[self.asset.uid])
        submission_id = 'abc123-def456'
        submission = {
            '__version__': self.asset.latest_deployed_version.uid,
            'q1': 'audio_conversion_test_clip.mp4',
            '_uuid': submission_id,
            '_attachments': [],
            '_submitted_by': self.user.username
        }
        self.asset.deployment.mock_submissions([submission])
        SubmissionExtras.objects.create(
            submission_uuid=submission_id,
            content={'q1': {'transcript': {'value': 'hello'}}},
            asset=self.asset
        )

        with override_config(ASR_MT_INVITEE_USERNAMES='*'):
            res = self.client.post(url, {}, format='json')
            self.assertEqual(res.status_code, 400)

        self.asset.permissions.all().delete()
        self.asset.owner = None
        self.asset.save()
        res = self.client.get(url + '?submission=' + submission_id, format='json')
        self.assertEqual(res.status_code, 404)
