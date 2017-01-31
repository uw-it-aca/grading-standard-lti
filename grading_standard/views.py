from django.core.context_processors import csrf
from django.core.exceptions import ValidationError
from django.utils import timezone
from blti.views import BLTILaunchView
from blti.views.rest_dispatch import RESTDispatch
from grading_standard.models import GradingStandard, GradingStandardCourse
from grading_standard.dao.canvas import create_grading_standard
from restclients.exceptions import DataFailureException
import logging
import json


logger = logging.getLogger(__name__)


class LaunchView(BLTILaunchView):
    template_name = 'grading_standard/standard.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        request = kwargs.get('request')
        blti_data = kwargs.get('blti_params')
        login_id = blti_data.get('custom_canvas_user_login_id', '')
        course_id = blti_data.get('custom_canvas_course_id')

        grading_standards = GradingStandard.objects.find_by_login(login_id)

        context = {
            'session_id': request.session.session_key,
            'grading_standards': grading_standards,
            'sis_course_id': blti_data.get('lis_course_offering_sourcedid',
                                           'course_%s' % course_id),
            'canvas_course_id': course_id,
            'course_title': blti_data.get('context_title'),
            'course_name': blti_data.get('context_label'),
            'launch_presentation_return_url': blti_data.get(
                'launch_presentation_return_url'),
        }
        context.update(csrf(request))
        return context


class GradingStandardView(RESTDispatch):
    def GET(self, request, **kwargs):
        try:
            blti = self.get_session(request)
            login_id = blti.get('custom_canvas_user_login_id', '')
            name = request.GET.get('name', '')
            if 'grading_standard_id' in kwargs:
                kwargs['id'] = kwargs['grading_standard_id']
            else:
                kwargs['name'] = GradingStandard.valid_scheme_name(name)

            grading_standard = GradingStandard.objects.find_by_login(
                login_id, **kwargs)[0]

            if 'grading_standard' not in locals():
                return self.error_response(400, "Unspecified grading standard")

            return self.json_response({
                "grading_standard": grading_standard.json_data()
            })

        except ValidationError as err:
            return self.error_response(400, "Invalid grading scheme: %s" % err)
        except IndexError as err:
            return self.error_response(404, "Grading Standard not found")

    def POST(self, request, **kwargs):
        blti = self.get_session(request)
        login_id = blti.get('custom_canvas_user_login_id')
        sis_user_id = blti.get('lis_person_sourcedid')
        course_id = blti.get('custom_canvas_course_id')
        try:
            data = json.loads(request.body).get("grading_standard", {})
            name = GradingStandard.valid_scheme_name(data.get("name", ""))
            course_sis_id = GradingStandard.valid_course_id(
                data.get("course_id", "").strip())
            scale = GradingStandard.valid_scale(data.get("scale", "").strip())
            scheme_data = GradingStandard.valid_grading_scheme(
                data.get("scheme", []))
        except ValidationError as err:
            return self.error_response(400, "Invalid grading scheme: %s" % err)

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
                500, "There was a problem saving this scale in Canvas: %s" % (
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

    def DELETE(self, request, **kwargs):
        gs_id = kwargs.get("grading_standard_id", None)
        if gs_id is None:
            return self.error_response(404, "Invalid grading standard")

        try:
            grading_standard = GradingStandard.objects.get(pk=gs_id)
        except GradingStandard.DoesNotExist:
            return self.error_response(404, "Invalid grading standard")

        blti = self.get_session(request)
        user_id = blti.get('custom_canvas_user_login_id')
        if grading_standard.created_by != user_id:
            return self.error_response(401, "Not authorized")

        grading_standard.is_deleted = True
        grading_standard.deleted_date = timezone.now()
        grading_standard.save()

        logger.info("Grading scheme deleted")

        return self.json_response({
            "grading_standard": grading_standard.json_data()
        })
