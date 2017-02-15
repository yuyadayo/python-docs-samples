# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START app]
import logging

from flask import Flask

import google.auth
import google.auth.transport.requests
from google.oauth2 import service_account
import google.oauth2._client
import google.oauth2.id_token
import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()


app = Flask(__name__)


def get_open_id_connect_id_token():
    credentials = service_account.Credentials.from_service_account_file(
        'service-account.json',
        additional_claims={
            'target_audience': 'https://msachs-staging.appspot.com'
        })

    grant_assertion = credentials._make_authorization_grant_assertion()

    request = google.auth.transport.requests.Request()

    # oauth2._client.jwt_grant (rightfully) expects an access token
    # in the response, but the target_audience claim doesn't return one.
    # so use the underlying _token_endpoint_request instead.

    body = {
        'assertion': grant_assertion,
        'grant_type': google.oauth2._client._JWT_GRANT_TYPE,
    }

    token_response = google.oauth2._client._token_endpoint_request(
        request, credentials._token_uri, body)

    return token_response['id_token']


def verify_open_id_connect_id_token(id_token):
    certs_url = 'https://www.googleapis.com/oauth2/v1/certs'
    request = google.auth.transport.requests.Request()

    claims = google.oauth2.id_token.verify_token(
        id_token, request, certs_url=certs_url)

    return claims


@app.route('/')
def hello():
    id_token = get_open_id_connect_id_token()
    claims = verify_open_id_connect_id_token(id_token)
    return 'Token: {}, Claims: {}'.format(id_token, claims)


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
# [END app]
