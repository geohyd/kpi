# -*- coding: utf-8 -*-
from importlib import import_module
import logging

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _
from jsonbfield.fields import JSONField as JSONBField
from rest_framework import status
from rest_framework.reverse import reverse
import requests


class HookLog(models.Model):

    hook = models.ForeignKey("Hook", related_name="logs", on_delete=models.CASCADE)
    uid = models.CharField(unique=True, max_length=36)  # Unique ID provided by submitted data
    instance_id = models.IntegerField(default=0)  # `kc.logger.Instance.id`. Useful to retrieve data on retry
    tries = models.IntegerField(default=0)
    success = models.BooleanField(default=True)  # Could use status_code, but will speed-up queries.
    status_code = models.IntegerField(default=200)
    message = models.TextField(default="")
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date_modified"]

    def retry(self, data):
        """
        Retry to send data to external service
        only if it has failed before this try.
        :param data: mixed.
        :return: tuple. status_code, response dict
        """
        if self.success is not True:
            if data:
                try:
                    ServiceDefinition = self.hook.get_service_definition()
                    service_definition = ServiceDefinition(self.hook, data, self.uid)
                    success = service_definition.send()
                    self.refresh_from_db()
                    return status.HTTP_200_OK, {
                        "success": success,
                        "message": self.message,
                        "status_code": self.status_code
                    }
                except Exception as e:
                    logger = logging.getLogger("console_logger")
                    logger.error("HookLog.retry - {}".format(str(e)), exc_info=True)
                    return status.HTTP_500_INTERNAL_SERVER_ERROR, {
                        "detail": _("An error has occurred when sending the data. Please try again later.")
                    }

            return status.HTTP_500_INTERNAL_SERVER_ERROR, {
                "detail": _("Could not retrieve data.")
            }

        return status.HTTP_400_BAD_REQUEST, {
            "detail": _("Instance has already been sent to external endpoint successfully.")
        }

    def save(self, *args, **kwargs):
        # Update date_modified each time object is saved
        self.date_modified = timezone.now()
        self.tries += 1
        self.hook.reset_totals()
        super(HookLog, self).save(*args, **kwargs)

    def __unicode__(self):
        return "<HookLog {uid}>".format(uid=self.uid)
