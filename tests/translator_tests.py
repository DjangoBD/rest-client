# -*- coding: utf-8 -*-

from datetime import datetime
from unittest import TestCase

import fudge

from sync_client.translators import BaseAPITranslator, APITranslator


class BaseAPITranslatorTest(TestCase):
    def setUp(self):
        self.translator = BaseAPITranslator()

    def test_attrs(self):
        self.assertIsNone(self.translator.model)

    @fudge.test
    def test_get_object_not_exists(self):
        self.translator.model = fudge.Fake().is_a_stub()
        self.translator.model.expects_call().returns('initialized object')

        obj = self.translator.get_object(stuff='things')

        self.assertEqual(obj, 'initialized object')

    def test_to_api(self):
        self.assertRaises(
            NotImplementedError, self.translator.to_api, None)

    def test_from_api(self):
        self.assertRaises(
            NotImplementedError, self.translator.from_api, None, None)


class APITranslatorTest(TestCase):
    def setUp(self):
        self.translator = APITranslator()

    def test_attrs(self):
        self.assertIsInstance(self.translator, BaseAPITranslator)
        self.assertSequenceEqual(self.translator.direct_keys, [])

    @fudge.test
    def test_to_api(self):
        self.translator.direct_keys = ['id', 'name']
        obj = fudge.Fake()
        mock_obj_dict = fudge.Fake().expects_call().with_args(
            obj, ['id', 'name']).returns({'id': 123, 'name': 'Western'})

        with fudge.patched_context(
                self.translator, 'get_object_dict', mock_obj_dict):
            data = self.translator.to_api(obj)

        self.assertEqual(data, {'id': 123, 'name': 'Western'})

    @fudge.test
    def test_from_api(self):
        data = {'id': 123, 'name': 'Western'}
        obj = fudge.Fake()
        mock_set_direct = fudge.Fake().expects_call().with_args(obj, data)

        with fudge.patched_context(
                self.translator, 'set_direct_values', mock_set_direct):
            self.translator.from_api(obj, data)

    def test_isoformat_date(self):
        fmt_date = self.translator.isoformat_date(datetime(2015, 4, 5, 3, 2, 1))
        self.assertEqual(fmt_date, '2015-04-05T03:02:01')

    def test_isoformat_date_wo_date(self):
        fmt_date = self.translator.isoformat_date(None)
        self.assertIsNone(fmt_date)

    def test_get_object_dict(self):
        obj = fudge.Fake()
        obj.test = 123
        obj.more = 'yes'
        obj._shh = 'quiet'
        obj_dict = self.translator.get_object_dict(obj)
        self.assertDictEqual(obj_dict, {'test': 123, 'more': 'yes'})

    def test_get_object_dict_w_keys(self):
        obj = fudge.Fake()
        obj.test = 123
        obj.more = 'yes'
        obj._shh = 'quiet'
        obj_dict = self.translator.get_object_dict(obj, keys=['more'])
        self.assertDictEqual(obj_dict, {'more': 'yes'})

    def test_set_direct_values(self):
        self.translator.direct_keys = ['test', 'stuff', 'more']
        obj = fudge.Fake()
        obj.test = 123
        data = {'test': 456, 'stuff': 'blah', 'things': 666}

        self.translator.set_direct_values(obj, data)

        self.assertEqual(obj.test, 456)
        self.assertEqual(obj.stuff, 'blah')
        self.assertFalse(hasattr(obj, 'things'))
        self.assertFalse(hasattr(obj, 'more'))
