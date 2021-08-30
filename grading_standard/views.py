# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from blti.views import BLTILaunchView, RESTDispatch
from grading_standard.models import GradingStandard, GradingStandardCourse
from grading_standard.dao.canvas import create_grading_standard
from restclients_core.exceptions import DataFailureException
import logging
import json

logger = logging.getLogger(__name__)


class LaunchView(BLTILaunchView):
    template_name = 'grading_standard/standard.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        login_id = self.blti.user_login_id
        course_id = self.blti.canvas_course_id

        grading_standards = GradingStandard.objects.find_by_login(login_id)

        if self.blti.course_sis_id:
            course_sis_id = self.blti.course_sis_id
        else:
            course_sis_id = 'course_{}'.format(course_id)

        return {
            'session_id': self.request.session.session_key,
            'grading_standards': grading_standards,
            'sis_course_id': course_sis_id,
            'canvas_course_id': course_id,
            'course_title': self.blti.course_long_name,
            'course_name': self.blti.course_short_name,
            'launch_presentation_return_url': self.blti.return_url,
            'documentation_url': getattr(settings, 'DOCUMENTATION_URL'),
        }


class GradingStandardView(RESTDispatch):
    authorized_role = 'admin'

    def get(self, request, *args, **kwargs):
        try:
            name = request.GET.get('name', '')
            if 'grading_standard_id' in kwargs:
                kwargs['id'] = kwargs['grading_standard_id']
            else:
                kwargs['name'] = GradingStandard.valid_scheme_name(name)

            grading_standard = GradingStandard.objects.find_by_login(
                self.blti.user_login_id, **kwargs)[0]

            if 'grading_standard' not in locals():
                return self.error_response(400, "Unspecified grading standard")

            return self.json_response({
                "grading_standard": grading_standard.json_data()
            })

        except ValidationError as err:
            return self.error_response(
                400, "Invalid grading scheme: {}".format(err))
        except IndexError as err:
            return self.error_response(404, "Grading Standard not found")

    def post(self, request, *args, **kwargs):
        login_id = self.blti.user_login_id
        sis_user_id = self.blti.user_sis_id
        course_id = self.blti.canvas_course_id
        try:
            data = json.loads(request.body).get("grading_standard", {})
            name = GradingStandard.valid_scheme_name(data.get("name", ""))
            course_sis_id = GradingStandard.valid_course_id(
                data.get("course_id", "").strip())
            scale = GradingStandard.valid_scale(data.get("scale", "").strip())
            scheme_data = GradingStandard.valid_grading_scheme(
                data.get("scheme", []))
        except ValidationError as err:
            return self.error_response(
                400, "Invalid grading scheme: {}".format(err))

        try:
            grading_standard = GradingStandard.objects.find_by_login(
                login_id, name=name)[0]
            grading_standard.is_deleted = None
            grading_standard.deleted_date = None

        except IndexError:
            grading_standard = GradingStandard()
            grading_standard.created_by = login_id
            grading_standard.name = name
            grading_standard.scale = scale

        grading_standard.scheme = json.dumps(scheme_data)

        try:
            canvas_gs = create_grading_standard(
                course_id, name, json.loads(grading_standard.scheme),
                sis_user_id)

        except DataFailureException as ex:
            grading_standard.save()
            return self.error_response(
                500,
                "There was a problem saving this scale in Canvas: {}".format(
                    ex.msg))

        grading_standard.name = canvas_gs.title
        grading_standard.provisioned_date = timezone.now()
        grading_standard.save()

        try:
            course = GradingStandardCourse.objects.get(
                standard=grading_standard, course_id=course_id)

        except GradingStandardCourse.DoesNotExist:
            course = GradingStandardCourse(
                standard=grading_standard, course_id=course_id)

            course.grading_standard_id = canvas_gs.grading_standard_id
            course.save()

        return self.json_response({
            "grading_standard": grading_standard.json_data()
        })

    def delete(self, request, *args, **kwargs):
        gs_id = kwargs.get("grading_standard_id", None)
        if gs_id is None:
            return self.error_response(404, "Invalid grading standard")

        try:
            grading_standard = GradingStandard.objects.get(pk=gs_id)
        except GradingStandard.DoesNotExist:
            return self.error_response(404, "Invalid grading standard")

        if grading_standard.created_by != self.blti.user_login_id:
            return self.error_response(401, "Not authorized")

        grading_standard.is_deleted = True
        grading_standard.deleted_date = timezone.now()
        grading_standard.save()

        logger.info("Grading scheme deleted: {}".format(gs_id))

        return self.json_response({
            "grading_standard": grading_standard.json_data()
        })
