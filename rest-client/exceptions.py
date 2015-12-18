# -*- coding: utf-8 -*-


class APIClientException(Exception):
    pass


class APIForbidden(APIClientException):
    pass


class APINotAuthorized(APIClientException):
    pass


class APIInvalidData(APIClientException):
    pass


class APIDuplicateObject(APIClientException):

    def __init__(self, msg, duplicate_id, *args, **kwargs):
        self.duplicate_id = duplicate_id
        super().__init__(msg, *args, **kwargs)
