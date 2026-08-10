# Copyright 2026 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from urllib.parse import unquote

from uw_canvas.grading_standards import GradingStandards


def create_grading_standard(course_id, name, scheme_data, sis_user_id):
    client = GradingStandards()

    # For Canvas, append the lower bound explicitly
    scheme_data.append({'grade': '0.0', 'min_percentage': 0})

    scheme = [{'name': s['grade'], 'value': s['min_percentage']} for s in scheme_data]

    user_id = unquote(client.sis_user_id(sis_user_id))

    return client.create_grading_standard_for_course(
        course_id, name, scheme, user_id)
