# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from uw_canvas.grading_standards import GradingStandards
from urllib.parse import unquote


def create_grading_standard(course_id, name, scheme_data, sis_user_id):
    client = GradingStandards()

    # For Canvas, append the lower bound explicitly
    scheme_data.append({'grade': '0.0', 'min_percentage': 0})

    scheme = list(map(lambda s: {
        'name': s['grade'], 'value': s['min_percentage']}, scheme_data))

    user_id = unquote(client.sis_user_id(sis_user_id))

    return client.create_grading_standard_for_course(
        course_id, name, scheme, user_id)
