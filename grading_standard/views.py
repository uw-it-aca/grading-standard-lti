from django.core.context_processors import csrf
from django.core.exceptions import ValidationError
from django.utils import timezone
from blti.views import BLTILaunchView
from blti.views.rest_dispatch import RESTDispatch
from grading_standard.models import GradingStandard as GradingStandardModel
from grading_standard.models import GradingStandardCourse
from restclients.canvas.grading_standards import GradingStandards as Canvas
from restclients.exceptions import DataFailureException
from urllib import unquote
import logging
import json


logger = logging.getLogger(__name__)


class LaunchView(BLTILaunchView):
    template_name = 'grading_standard/standard.html'
    authorized_role = 'admin'

    def get_context_data(self, **kwargs):
        request = kwargs.get('request')
        blti_data = kwargs.get('blti_params')
        canvas_login_id = blti_data.get('custom_canvas_user_login_id')
        canvas_course_id = blti_data.get('custom_canvas_course_id')

        grading_standards = GradingStandardModel.objects.filter(
            created_by=canvas_login_id, is_deleted__isnull=True
        ).order_by('created_date')

        context = {
            'session_id': request.session.session_key,
            'grading_standards': grading_standards,
            'sis_course_id': blti_data.get('lis_course_offering_sourcedid',
                                           'course_%s' % canvas_course_id),
            'canvas_course_id': canvas_course_id,
            'course_title': blti_data.get('context_title'),
            'course_name': blti_data.get('context_label'),
            'launch_presentation_return_url': blti_data.get(
                'launch_presentation_return_url'),
        }
        context.update(csrf(request))
        return context


class GradingStandard(RESTDispatch):
    def GET(self, request, **kwargs):
        try:
            blti = self.get_session(request)
            user_id = blti.get('custom_canvas_user_login_id')
            if 'grading_standard_id' in kwargs:
                grading_standard = GradingStandardModel.objects.get(
                    id=kwargs['grading_standard_id'],
                    created_by=user_id,
                    is_deleted__isnull=True
                )
            else:
                scheme_name = request.GET.get('name', None)
                if scheme_name and len(scheme_name.strip()):
                    grading_standard = GradingStandardModel.objects.get(
                        name=scheme_name,
                        created_by=user_id,
                        is_deleted__isnull=True
                    )

            if 'grading_standard' not in locals():
                return self.error_response(400, "Unspecified grading standard")

            return self.json_response({
                "grading_standard": grading_standard.json_data()
            })

        except GradingStandardModel.DoesNotExist:
            return self.error_response(
                404, "Unknown Grading Standard: %s" % scheme_name)

    def POST(self, request, **kwargs):
        blti = self.get_session(request)
        user_id = blti.get('custom_canvas_user_login_id')
        sis_user_id = blti.get('lis_person_sourcedid')
        course_id = blti.get('custom_canvas_course_id')
        try:
            data = json.loads(request.body).get("grading_standard", {})
            scheme_name = self._valid_scheme_name(data.get("name", "").strip())
            course_sis_id = self._valid_course_id(
                data.get("course_id", "").strip())
            scale = self._valid_scale(data.get("scale", "").strip())
            scheme_data = self._valid_grading_scheme(data.get("scheme", []))
        except ValidationError as err:
            return self.error_response(400, "Invalid grading scheme: %s" % err)

        try:
            grading_standard = GradingStandardModel.objects.get(
                created_by=user_id,
                name=scheme_name
            )
            grading_standard.is_deleted = None
            grading_standard.deleted_date = None

        except GradingStandardModel.DoesNotExist:
            grading_standard = GradingStandardModel()
            grading_standard.created_by = user_id
            grading_standard.name = scheme_name
            grading_standard.scale = scale

        grading_standard.scheme = json.dumps(scheme_data)

        # For Canvas, append the lower bound explicitly
        canvas_scheme = json.loads(grading_standard.scheme)
        canvas_scheme.append({"grade": "0.0", "min_percentage": 0})

        client = Canvas()
        try:
            canvas_gs = client.create_grading_standard_for_course(
                course_id,
                scheme_name,
                map(lambda s: {"name": s["grade"],
                               "value": s["min_percentage"]},
                    canvas_scheme),
                unquote(client.sis_user_id(sis_user_id)))

        except DataFailureException as ex:
            grading_standard.save()
            content = json.loads(ex.msg)
            content["status_code"] = ex.status
            return self.error_response(
                500, "Unable to save scheme", content=content)

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
            grading_standard = GradingStandardModel.objects.get(pk=gs_id)
        except GradingStandardModel.DoesNotExist:
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

    def _valid_scheme_name(self, name):
        if not (name and len(name) > 0):
            raise ValidationError("Name is required")
        return name

    def _valid_scale(self, scale):
        for choice in GradingStandardModel.SCALE_CHOICES:
            if scale == choice[0]:
                return scale

        raise ValidationError("Invalid scale: %s" % (scale))

    def _valid_grading_scheme(self, scheme):
        if not (scheme and len(scheme) > 0):
            raise ValidationError("Scheme is required")
        return scheme

    def _valid_course_id(self, sis_id):
        if not (sis_id and len(sis_id) > 0):
            raise ValidationError("Course SIS ID is required")
        return sis_id
