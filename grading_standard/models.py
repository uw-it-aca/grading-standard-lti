from django.db import models
import logging
import json


logger = logging.getLogger(__name__)


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


class GradingStandardCourse(models.Model):
    """ Represents a grading standard.
    """
    standard = models.ForeignKey(GradingStandard)
    course_id = models.CharField(max_length=80)
    grading_standard_id = models.CharField(max_length=30, null=True)
    provisioned_date = models.DateTimeField(auto_now_add=True)
