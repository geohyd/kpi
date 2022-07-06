# coding: utf-8
import json
import re

from ..constants import SUBMISSION_PLACEHOLDER
from ..models.service_definition_interface import ServiceDefinitionInterface


class ServiceDefinition(ServiceDefinitionInterface):
    id = 'json'

    def __add_payload_template(self, submission):
        if not self._hook.payload_template:
            return submission

        custom_payload = self._hook.payload_template.replace(
            SUBMISSION_PLACEHOLDER, json.dumps(submission))

        return json.loads(custom_payload)
    # ANTEA METHOD
    def antea_parse(self, submission):
        # This method transform the submission from KC to a kpi formpack JSON : 
        # "header_lang" : "_xml" (the XLSForm key)
        # "lang": "_default" (the XLSForm name)
        try:
            print("ANTEA PARSE")
            from kobo.apps.reports.report_data import build_formpack
            pack, submission_stream = build_formpack(
                self._hook.asset, submission, False)
            options = {
                'versions': [submission["__version__"]],
                'group_sep': '/',
                'multiple_select': 'both',
                'lang': None,
                'hierarchy_in_labels': False,
                'copy_fields': ('_id', '_uuid', '_submission_time' , '_notes', '_status', '_submitted_by', '_tags', '_geolocation', '_xform_id_string', '__version__', 'formhub/uuid'),
                'force_index': True,
                'tag_cols_for_header': ['hxl'],
                'filter_fields': [],
                'header_lang': False
            }
            # TODO JDU : si je met "lang": "_default" & "header_lang" : "_xml", ca marche pas comme on veut. Erreur dans Formpack ?
            # Ultra nécessaire, sinon formpack ne retrouve pas la version
            submission["__inferred_version__"] = submission["__version__"]
            export = pack.export(**options)
            # on avait transformé en tableau juste pour formPack, mais ici on n'a que la dernière soumission
            # On recupère le 1er index du coup
            kpi_json_data = export.to_json([submission])[0]
            # Why this field is not copy ?
            kpi_json_data['formhub/uuid'] = submission['formhub/uuid']
            print("END OF ANTEA PARSE")
            return kpi_json_data
        except Exception as e:
            print("Error in antea parse hook : ", e)
            return submission

    def _parse_data(self, submission, fields):
        # ANTEA CALL METHOD
        print("ANTEA PARSE DISABLE")
        #submission = self.antea_parse(submission)
        if len(fields) > 0:
            parsed_submission = {}
            submission_keys = submission.keys()

            for field_ in fields:
                pattern = r'^{}$' if '/' in field_ else r'(^|/){}(/|$)'
                for key_ in submission_keys:
                    if re.search(pattern.format(field_), key_):
                        parsed_submission.update({
                            key_: submission[key_]
                        })

            return self.__add_payload_template(parsed_submission)

        return self.__add_payload_template(submission)

    def _prepare_request_kwargs(self):
        return {
            'headers': {'Content-Type': 'application/json'},
            'json': self._data
        }
