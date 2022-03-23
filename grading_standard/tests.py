# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


# -*- coding:utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from grading_standard.dao.canvas import *
from grading_standard.models import GradingStandard
from datetime import datetime
import mock


class GradingStandardTest(TestCase):
    @mock.patch.object(QuerySet, 'filter')
    def test_find_by_login(self, mock_method):
        r = GradingStandard.objects.find_by_login('javerage')
        mock_method.assert_called_with(
            created_by='javerage', is_deleted__isnull=True)

        r = GradingStandard.objects.find_by_login('javerage', id='123')
        mock_method.assert_called_with(
            created_by='javerage', is_deleted__isnull=True, id='123')

        r = GradingStandard.objects.find_by_login('javerage', name='abc')
        mock_method.assert_called_with(
            created_by='javerage', is_deleted__isnull=True, name='abc')

    def test_valid_scheme_name(self):
        self.assertEquals(
            GradingStandard.valid_scheme_name('valid'), 'valid')
        self.assertEquals(
            GradingStandard.valid_scheme_name(' valid   '), 'valid')
        self.assertEquals(
            GradingStandard.valid_scheme_name(u'valid'), 'valid')
        self.assertEquals(
            GradingStandard.valid_scheme_name('名称'), '名称')
        self.assertEquals(
            GradingStandard.valid_scheme_name('123'), '123')
        self.assertRaises(
            ValidationError, GradingStandard.valid_scheme_name, '  ')
        self.assertRaises(
            ValidationError, GradingStandard.valid_scheme_name, None)

    def test_valid_scale(self):
        self.assertEquals(GradingStandard.valid_scale('ug'), 'ug')
        self.assertEquals(GradingStandard.valid_scale('gr'), 'gr')
        self.assertEquals(GradingStandard.valid_scale('UG'), 'ug')
        self.assertRaises(ValidationError, GradingStandard.valid_scale, '')
        self.assertRaises(ValidationError, GradingStandard.valid_scale, None)
        self.assertRaises(ValidationError, GradingStandard.valid_scale, 'abc')
        self.assertRaises(ValidationError, GradingStandard.valid_scale, '3')

    def test_valid_grading_scheme(self):
        scheme = [1, 2, 3]
        self.assertEquals(GradingStandard.valid_grading_scheme(scheme), scheme)
        self.assertRaises(
            ValidationError, GradingStandard.valid_grading_scheme, None)
        self.assertRaises(
            ValidationError, GradingStandard.valid_grading_scheme, 'abc')
        self.assertRaises(
            ValidationError, GradingStandard.valid_grading_scheme, {'a': True})
        self.assertRaises(
            ValidationError, GradingStandard.valid_grading_scheme, [])

    def test_valid_course_id(self):
        self.assertEquals(GradingStandard.valid_course_id('abc'), 'abc')
        self.assertEquals(GradingStandard.valid_course_id('ABC'), 'ABC')
        self.assertEquals(GradingStandard.valid_course_id('34'), '34')
        self.assertRaises(
            ValidationError, GradingStandard.valid_course_id, '')
        self.assertRaises(
            ValidationError, GradingStandard.valid_course_id, '   ')
        self.assertRaises(
            ValidationError, GradingStandard.valid_course_id, None)

    def test_json_data(self):
        json_data = GradingStandard(
            name='abc', scheme='[1, 2, 3]', created_by='j',
            created_date=datetime.now()).json_data()

        self.assertEqual(json_data['created_by'], 'j')
        self.assertEqual(json_data['name'], 'abc')
        self.assertEqual(json_data['scheme'], [1, 2, 3])


class CanvasDAOTest(TestCase):
    @mock.patch.object(GradingStandards, 'create_grading_standard_for_course')
    def test_create_grading_standard(self, mock_method):
        course_id = '123'
        name = 'abc'
        scheme = []
        sis_user_id = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'

        r = create_grading_standard(course_id, name, scheme, sis_user_id)
        mock_method.assert_called_with(
            course_id, name, [{'name': '0.0', 'value': 0}],
            'sis_user_id:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')

        scheme = scheme = [{'grade': '4.0', 'min_percentage': 95}]

        r = create_grading_standard(course_id, name, scheme, sis_user_id)
        mock_method.assert_called_with(
            course_id, name,
            [{'name': '4.0', 'value': 95}, {'name': '0.0', 'value': 0}],
            'sis_user_id:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
