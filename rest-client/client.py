from decimal import Decimal
from urllib.parse import parse_qs, urlparse
import json
import logging

import requests

from . import exceptions


logger = logging.getLogger(__name__)


class ApiJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return obj


class APIClient(object):
    def __init__(self, api_token, api_url):
        self.api_token = api_token
        self.api_url = api_url

    def make_request(self, method, endpoint, params=None, payload=None):
        data = payload and json.dumps(payload, cls=ApiJsonEncoder)
        url = '{}{}'.format(self.api_url, endpoint)
        headers = self.get_headers()
        cookies = self.get_cookies()
        logger.debug('APIClient request url: %s', url)
        logger.debug('APIClient request method: %s', method)
        logger.debug('APIClient request params: %s', params)
        logger.debug('APIClient request data: %s', data)
        logger.debug('APIClient request headers: %s', headers)
        logger.debug('APIClient request cookies: %s', cookies)

        req = requests.request(
            method, url, params=params, data=data, headers=headers,
            cookies=cookies)

        logger.debug('APIClient response status: %s', req.status_code)
        logger.debug('APIClient response time: %s',
                     req.elapsed.total_seconds())
        logger.debug('APIClient response content: %s', req.content)

        try:
            result = req.json()
        except ValueError as e:  # error decoding json
            result = {'detail': '{}: {}'.format(e, req.content)}

        if req.status_code in [200, 201, 202, 204]:
            return result, req

        elif req.status_code == 403:
            raise exceptions.APIForbidden(result['detail'])

        elif req.status_code == 401:
            raise exceptions.APINotAuthorized(result['detail'])

        elif req.status_code == 400 and (
                result.get('error_type', '') == ['duplicate_object']):
            raise exceptions.APIDuplicateObject(
                result['detail'][0], result['id'][0])

        elif req.status_code == 400 and 'detail' not in result:
            raise exceptions.APIInvalidData('; '.join(self.parse_error(result)))
        else:
            raise exceptions.APIClientException(result.get('detail'))

    def get_headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def get_cookies(self):
        return {}

    def retrieve_object(self, endpoint, remote_id):
        endpoint = '{}{}/'.format(endpoint, remote_id)
        result, _ = self.make_request('GET', endpoint)
        return result

    def retrieve_multiple_objects(self, endpoint, params=None):
        params = params or {}
        response = None
        next_url = ''

        while next_url or response is None:
            response, _ = self.make_request('GET', endpoint, params=params)
            if isinstance(response, dict):
                next_url = response.get('next')
                params = next_url and parse_qs(urlparse(next_url).query)
                results = response.get('results', [])
            else:
                results = response

            for result in results:
                yield result

    def create_object(self, endpoint, payload):
        result, _ = self.make_request('POST', endpoint, payload=payload)
        return result

    def update_object(self, endpoint, remote_id, payload):
        endpoint = '{}{}/'.format(endpoint, remote_id)
        result, _ = self.make_request('PATCH', endpoint, payload=payload)
        return result

    def delete_object(self, endpoint, remote_id):
        raise NotImplementedError

    def parse_error(self, results):
        msgs = []
        for field, msg in results.items():
            if isinstance(msg, dict):
                msg = self.parse_error(msg)
            msgs.append('{}: {}'.format(field, msg))
        return msgs


class TokenAPIClient(APIClient):
    def get_headers(self):
        headers = super(TokenAPIClient, self).get_headers()
        headers['Authorization'] = 'Token {}'.format(self.api_token)
        return headers


# example client usage

# def api_update(model, pk):
    # translator = get_translator(model)
    # obj = translator.get_object(pk)
    # data = translator.to_api(obj)
    # client = APIClient()
    # client.update_object(model, obj.id, data)


# def api_create(model, pk):
    # translator = get_translator(model)
    # obj = translator.get_object(pk)

    # # sync related objects first
    # for related_model, related_id in translator.get_unsynced_related(obj):
        # api_create(related_model, related_id)

    # data = translator.to_api(obj)
    # client = APIClient()
    # try:
        # resp_data = client.create_object(model, data)
    # except exceptions.APIDuplicateObject as e:
        # obj.id = e.duplicate_id
        # obj.save(update_fields=['id'])
        # api_update(model, obj.id)
    # else:
        # obj.id = resp_data['id']
        # obj.save(update_fields=['id'])
