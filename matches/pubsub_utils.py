# -*- coding: utf-8 -*-

'''
utility module for Pub/Sub, based on
https://github.com/GoogleCloudPlatform/cloud-pubsub-samples-python/
    blob/master/appengine-push/pubsub_utils.py
'''

from __future__ import absolute_import, unicode_literals

import json
import logging

from base64 import b64encode

import httplib2
import six

# pylint: disable=import-error
from apiclient import discovery
from django.conf import settings
# pylint: disable=import-error
from google.appengine.api import app_identity
# pylint: disable=import-error
from google.appengine.api import memcache
# pylint: disable=import-error
from oauth2client.client import GoogleCredentials

LOGGER = logging.getLogger(__name__)
PUBSUB_SCOPES = ['https://www.googleapis.com/auth/pubsub']

def get_client_from_credentials(credentials):
    if credentials.create_scoped_required():
        credentials = credentials.create_scoped(PUBSUB_SCOPES)

    http = httplib2.Http(memcache)
    credentials.authorize(http)

    return discovery.build('pubsub', 'v1', http=http)

class PubSubSender(object):
    def __init__(self, project_id=None, topic_name=None):
        try:
            self.client = get_client_from_credentials(GoogleCredentials.get_application_default())

            project_id = project_id or app_identity.get_application_id()
            topic_name = topic_name or settings.PUBSUB_NOTIFICATIONS_TOPIC
            self.full_topic_name = 'projects/{}/topics/{}'.format(project_id, topic_name)
        except Exception as exc:
            LOGGER.warning(exc)
            self.client = None
            self.full_topic_name = None

    def send_message(self, data=None, attributes=None):
        if not (self.client and self.full_topic_name):
            return

        data = data or ''
        if not isinstance(data, six.string_types):
            data = json.dumps(data)

        attributes = attributes or {}

        body = {
            'messages': [{
                'data': b64encode(data.encode('utf-8')),
                'attributes': attributes,
            }]
        }

        LOGGER.info('publish message; topic: %s; data: %s; attributes: %s',
                    self.full_topic_name, data, attributes)

        try:
            response = self.client.projects().topics().publish(
                topic=self.full_topic_name,
                body=body,
            ).execute()
        except Exception as exc:
            LOGGER.warning(exc)
            response = None

        return response
