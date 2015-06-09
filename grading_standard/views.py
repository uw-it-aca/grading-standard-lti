from django.template import Context, loader
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.context_processors import csrf
from django.core.exceptions import ValidationError
from django.utils import timezone
from blti import BLTI, BLTIException
from blti.views.rest_dispatch import RESTDispatch
from grading_standard.models import GradingStandard as GradingStandardModel
from grading_standard.models import GradingStandardCourse
from restclients.canvas.grading_standards import GradingStandards as Canvas
from restclients.exceptions import DataFailureException
from urllib import unquote
import logging
import json


logger = logging.getLogger(__name__)


@csrf_exempt
def Main(request, template='grading_standard/standard.html'):
    blti_data = {"context_label": "NO COURSE"}
    blti_error = None
    sis_course_id = 'None'
    canvas_course_id = 'None'
    grading_standards = []
    try:
        blti = BLTI()
        blti_data = blti.validate(request)
        canvas_login_id = blti_data.get('custom_canvas_user_login_id')
        canvas_course_id = blti_data.get('custom_canvas_course_id')
        sis_course_id = blti_data.get('lis_course_offering_sourcedid',
                                      'course_%s' % canvas_course_id)
        blti.set_session(request,
                         user_id=canvas_login_id,
                         sis_user_id=blti_data.get('lis_person_sourcedid'),
                         canvas_course_id=canvas_course_id)

        grading_standards = GradingStandardModel.objects.filter(
            created_by=canvas_login_id, is_deleted__isnull=True
        ).order_by('created_date')

    except Exception as err:
        blti_error = '%s' % err

    t = loader.get_template(template)
    c = Context({
        'session_id': request.session.session_key,
        'grading_standards': grading_standards,
        'sis_course_id': sis_course_id,
        'canvas_course_id': canvas_course_id,
        'blti_json': json.dumps(blti_data),
        'blti_error': blti_error,
    })

    c.update(csrf(request))
    return HttpResponse(t.render(c))


class GradingStandard(RESTDispatch):
    def GET(self, request, **kwargs):
        try:
            blti = BLTI().get_session(request)
            if 'grading_standard_id' in kwargs:
                grading_standard = GradingStandardModel.objects.get(
                    id=kwargs['grading_standard_id'],
                    created_by=blti.get("user_id"),
                    is_deleted__isnull=True
                )
            else:
                scheme_name = request.GET.get('name', None)
                if scheme_name and len(scheme_name.strip()):
                    grading_standard = GradingStandardModel.objects.get(
                        name=scheme_name,
                        created_by=blti.get("user_id"),
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
        blti = BLTI().get_session(request)
        try:
            data = json.loads(request.body).get("grading_standard", {})
            scheme_name = self._valid_scheme_name(data.get("name", "").strip())
            course_id = self._valid_course_id(
                data.get("course_id", "").strip())
            scale = self._valid_scale(data.get("scale", "").strip())
            scheme_data = self._valid_grading_scheme(data.get("scheme", []))
        except ValidationError as err:
            logger.exception(err)
            return self.error_response(400, "Invalid grading scheme: %s" % err)

        try:
            grading_standard = GradingStandardModel.objects.get(
                created_by=blti.get("user_id"),
                name=scheme_name
            )
            grading_standard.is_deleted = None
            grading_standard.deleted_date = None

        except GradingStandardModel.DoesNotExist:
            grading_standard = GradingStandardModel()
            grading_standard.created_by = blti.get("user_id")
            grading_standard.name = scheme_name
            grading_standard.scale = scale

        grading_standard.scheme = json.dumps(scheme_data)

        client = Canvas()
        try:
            canvas_gs = client.create_grading_standard_for_course(
                blti.get('canvas_course_id'),
                scheme_name,
                map(lambda s: {"name": s["grade"],
                               "value": s["min_percentage"]},
                    json.loads(grading_standard.scheme)),
                unquote(client.sis_user_id(blti.get('sis_user_id'))))

        except DataFailureException as ex:
            logger.exception(ex)
            grading_standard.save()
            return self.error_response(500, "Unable to save scheme: %s" % ex)

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

        blti = BLTI().get_session(request)
        if grading_standard.created_by != blti.get("user_id"):
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
