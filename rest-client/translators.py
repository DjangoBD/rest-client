class BaseAPITranslator(object):
    model = None
    endpoint = '/'

    def get_object(self, **kwargs):
        return self.model(**kwargs)

    def to_api(self, obj):
        '''
        Serializes model for sending to API.
        '''
        raise NotImplementedError

    def from_api(self, obj, data):
        '''
        Deserializes data from API and saves to model.
        '''
        raise NotImplementedError


class APITranslator(BaseAPITranslator):
    direct_keys = []

    def to_api(self, obj):
        return self.get_object_dict(obj, self.direct_keys)

    def from_api(self, obj, data):
        self.set_direct_values(obj, data)

    def isoformat_date(self, date):
        '''
        Returns an iso formatted string of the date or None
        '''
        if date:
            return date.isoformat()

    def get_object_dict(self, obj, keys=None):
        return {
            k: v
            for k, v in obj.__dict__.items()
            if not k.startswith('_')
            and k in (keys or [k])
        }

    def set_direct_values(self, obj, data):
        for key in self.direct_keys:
            if key in data:
                setattr(obj, key, data[key])
