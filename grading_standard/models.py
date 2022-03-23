# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.db import models
from django.core.exceptions import ValidationError
import json


class GradingStandardManager(models.Manager):
    def find_by_login(self, login_id, id=None, name=None):
        kwargs = {'created_by': login_id, 'is_deleted__isnull': True}
        if id is not None:
            kwargs['id'] = id
        if name is not None:
            kwargs['name'] = name

        return super(GradingStandardManager, self).get_queryset().filter(
            **kwargs).order_by('created_date')


class GradingStandard(models.Model):
    """ Represents a grading standard.
    """
    UNDERGRADUATE_SCALE = "ug"
    GRADUATE_SCALE = "gr"

    SCALE_CHOICES = (
        (UNDERGRADUATE_SCALE, "Undergraduate Scale (4.0-0.7)"),
        (GRADUATE_SCALE, "Graduate Scale (4.0-1.7)"),
    )

    name = models.CharField(max_length=80)
    scale = models.CharField(max_length=5, choices=SCALE_CHOICES)
    scheme = models.TextField()
    created_by = models.CharField(max_length=32)
    created_date = models.DateTimeField(auto_now_add=True)
    provisioned_date = models.DateTimeField(null=True)
    is_deleted = models.NullBooleanField()
    deleted_date = models.DateTimeField(null=True)

    objects = GradingStandardManager()

    def json_data(self):
        try:
            scheme_data = json.loads(self.scheme)
        except Exception as ex:
            scheme_data = []

        course_ids = list(GradingStandardCourse.objects.filter(
            standard=self).values_list("course_id", flat=True))

        return {"id": self.pk,
                "name": self.name,
                "scale": self.scale,
                "scheme": scheme_data,
                "course_ids": course_ids,
                "created_by": self.created_by,
                "created_date": self.created_date.isoformat(),
                "provisioned_date": self.provisioned_date.isoformat() if (
                    self.provisioned_date is not None) else None,
                "is_deleted": self.is_deleted,
                "deleted_date": self.deleted_date.isoformat() if (
                    self.deleted_date is not None) else None,
                }

    @staticmethod
    def valid_scheme_name(name):
        if name is not None:
            name = name.strip()
            if len(name):
                return name
        raise ValidationError('Name is required')

    @staticmethod
    def valid_scale(scale):
        if scale is not None:
            scale = scale.lower()
            for choice in GradingStandard.SCALE_CHOICES:
                if scale == choice[0]:
                    return scale
        raise ValidationError('Invalid scale: {}'.format(scale))

    @staticmethod
    def valid_grading_scheme(scheme):
        if type(scheme) is list and len(scheme):
            return scheme
        raise ValidationError('Scheme is required')

    @staticmethod
    def valid_course_id(sis_course_id):
        if sis_course_id is not None:
            sis_course_id = sis_course_id.strip()
            if len(sis_course_id):
                return sis_course_id
        raise ValidationError('Course SIS ID is required')


class GradingStandardCourse(models.Model):
    """ Represents a grading standard.
    """
    standard = models.ForeignKey(GradingStandard, on_delete=models.CASCADE)
    course_id = models.CharField(max_length=80)
    grading_standard_id = models.CharField(max_length=30, null=True)
    provisioned_date = models.DateTimeField(auto_now_add=True)
