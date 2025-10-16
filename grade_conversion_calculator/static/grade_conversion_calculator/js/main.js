/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars, ngettext, gettext, interpolate */
var GradeConversionCalculator = (function ($) {
    "use strict";

    var scales = {
            "cnc": ["CR", "NC"],
            "hpf": ["H", "HP", "P", "F"],
            "pf": ["P", "F"],
            "ug": [],
            "gr": []
        },
        default_scales = {
            "ug": ["4.0", "0.7"],
            "gr": ["4.0", "1.7"]
        },
        selected_scale = "ug",
        saved_calculator_values = [],
        saved_grade_scale = [],
        id_counter = 0,
        calc_row_template,
        scale_row_template,
        add_row_template,
        render_container;

    function is_fixed_scale(scale) {
        return (scale === "cnc" || scale === "hpf" || scale === "pf");
    }

    function set_selected_scale(scale) {
        selected_scale = scale;
    }

    function set_saved_scale(values) {
        if ($.isArray(values)) {
            saved_grade_scale = values;
        }
    }

    function set_saved_calculator(values) {
        if ($.isArray(values)) {
            saved_calculator_values = values;
        }
    }

    function clear_saved_data() {
        saved_calculator_values = [];
        saved_grade_scale = [];
    }

    function build_scales() {
        var i,
            value;

        scales.ug = [];
        scales.gr = [];

        for (i = 40; i >= 7; i--) {
            value = i / 10;
            if (value === parseInt(value, 10)) {
                value = value + ".0";
            }
            scales.ug.push(value.toString());
            if (value >= 1.7) {
                scales.gr.push(value.toString());
            }
        }
        scales.ug.push("0.0");
        scales.gr.push("0.0");
    }

    function add_calculator_row(ev) {
        var params = {id: ++id_counter};
        ev.preventDefault();
        $("#gp-calculator-add-row").before(calc_row_template(params))
                                   .prev()
                                   .find("input[name='calculator-percentage']:first")
                                   .focus();
    }

    function update_lowest() {
        var p = $("input[name='min-percentage']:last"),
            percentage = $.trim(p.val());

        percentage = Math.round(parseFloat(percentage) * 10) / 10;
        if (!isNaN(percentage)) {
            $(".gp-lowest-grade .gp-calc-percentage").html(percentage);
        }
    }

    function highlight_calculator_grades() {
        var grade,
            i;

        $(".gp-scale-row").not(".gp-lowest-grade").each(function (idx) {
            grade = scales[selected_scale][idx];
            for (i = 0; i < saved_calculator_values.length; i++) {
                if (saved_calculator_values[i].grade === grade) {
                    $(this).addClass("gp-scale-row-selected");
                }
            }
        });
    }

    function update_scale_selector() {
        var selector = $(".gp-scale-selector").find("select");
        selector.find("option").removeAttr("selected");
        selector.val(selected_scale).find("option")
                                    .filter("[value=" + selected_scale + "]")
                                    .attr("selected", "selected");
        render_container.trigger("updateGradeScale", {"scale": selected_scale});
    }

    function valid_input(input) {
        input.removeAttr("aria-invalid");
        input.parent().removeClass("has-error");
        input.next().find("span.gp-calc-err:first").html("");
    }

    function invalid_input(input, error) {
        input.attr("aria-invalid", "true");
        input.parent().addClass("has-error");
        input.next().find("span.gp-calc-err:first").html(error);
    }

    function draw_calculator() {
        var params = saved_calculator_values,
            text,
            len,
            i;

        $(".gp-calculator-row-container").empty();
        if (is_fixed_scale(selected_scale)) {
            text = gettext("calculator_min_" + selected_scale);
            $(".gp-calculator-row-container").html(text);
            $(".gp-calculator-header").hide();
            $(".gp-conversion-calculator-buttons").hide();
        } else {
            if (!params.length) {
                params = $.map(default_scales[selected_scale], function (val) {
                    return {grade: val, percentage: ""};
                });
            }

            for (i = 0, len = params.length; i < len; i++) {
                params[i].id = ++id_counter;
                if (i === 0) {
                    params[i].is_first = true;
                } else if (i === len - 1) {
                    params[i].is_last = true;
                }
                $(".gp-calculator-row-container").append(calc_row_template(params[i]));
                if (i === len - 2) {
                    $(".gp-calculator-row-container").append(add_row_template());
                    $("#gp-calculator-add-row a").click(add_calculator_row);
                }
            }
            $(".gp-calculator-header").show();
            $(".gp-conversion-calculator-buttons").show();
        }
    }

    function calculate_grade_scale() {
        var grades = saved_calculator_values,
            curr_grade,
            curr_pos = 0,
            matched_pos = null;

        if (!grades.length) {
            return;
        }

        grades.sort(function (a, b) {
            return b.percentage - a.percentage;
        });

        curr_grade = grades[0].grade;
        $(".gp-scale-row").not(".gp-lowest-grade").each(function (idx) {
            var class_grade = scales[selected_scale][idx],
                curr_percentage,
                prev_percentage,
                step_value,
                step_percentage,
                i;

            if (!grades[curr_pos]) {
                $(this).remove();
                return;
            }

            if (class_grade === curr_grade) {
                if (matched_pos !== null) {
                    curr_percentage = parseFloat(grades[curr_pos].percentage, 10);
                    prev_percentage = parseFloat(grades[curr_pos - 1].percentage, 10);
                    step_value = (curr_percentage - prev_percentage) / (idx - matched_pos);

                    for (i = matched_pos; i <= idx; i++) {
                        step_percentage = prev_percentage + (step_value * (i - matched_pos));
                        step_percentage = Math.round(step_percentage * 10) / 10;

                        $(".gp-scale-row").eq(i)
                                          .find("input[name='min-percentage']:first")
                                          .val(step_percentage);
                    }
                }
                matched_pos = idx;
                curr_pos++;
                if (grades[curr_pos]) {
                    curr_grade = grades[curr_pos].grade;
                }
            }
        });
    }

    function draw_grade_scale() {
        var params,
            len,
            i;

        if (saved_grade_scale.length) {
            params = saved_grade_scale.slice();
            // Saved scales don't include the lowest scale grade
            params.push({
                grade: scales[selected_scale][scales[selected_scale].length - 1],
                min_percentage: ""
            });
        } else {
            params = $.map(scales[selected_scale], function (val) {
                return {grade: val, min_percentage: ""};
            });
        }

        $(".gp-scale-row-container").empty();

        for (i = 0, len = params.length; i < len; i++) {
            params[i].id = ++id_counter;
            params[i].is_last = (i === len - 1);
            $(".gp-scale-row-container").append(scale_row_template(params[i]));
        }
        $("input[name='min-percentage']").change(update_lowest);
        $(".gp-conversion-err").html("");

        // Don't generate a calculated scale if there is a saved scale
        if (!saved_grade_scale.length) {
            calculate_grade_scale();
        }
        update_lowest();
        highlight_calculator_grades();
    }

    function apply_conversion() {
        var highest_valid_grade = parseFloat(scales[selected_scale][0]),
            lowest_valid_grade = parseFloat(scales[selected_scale][scales[selected_scale].length - 2]),
            last_seen_percentage,
            last_seen_grade;

        clear_saved_data();
        $(".gp-calculator-row").each(function () {
            var p = $(this).find("input[name='calculator-percentage']:first"),
                g = $(this).find("input[name='calculator-grade']:first"),
                percentage = $.trim(p.val()),
                grade = $.trim(g.val()),
                has_error = false;

            if (!$(this).is(":first-child") && !$(this).is(":last-child")) {
                if (percentage === "" && grade === "") {
                    // Trim any blank rows, skipping the bottom row
                    $(this).remove();
                    return;
                }
            }

            if (percentage === "") {
                has_error = true;
                invalid_input(p, gettext("calculator_min_missing"));
            } else if (percentage.match(/^[^-]+[-]/)) {
                // Input looks like a range
                has_error = true;
                invalid_input(p, gettext("calculator_min_invalid"));
            } else {
                percentage = Math.round(parseFloat(percentage) * 10) / 10;
                if (isNaN(percentage) || percentage >= last_seen_percentage) {
                    has_error = true;
                    invalid_input(p, gettext("calculator_min_invalid"));
                } else {
                    last_seen_percentage = percentage;
                    valid_input(p);
                }
            }

            if (grade === "") {
                has_error = true;
                invalid_input(g, gettext("calculator_grade_missing"));
            } else {
                grade = Math.round(parseFloat(grade) * 10) / 10;
                if (isNaN(grade) || grade > highest_valid_grade ||
                        grade < lowest_valid_grade ||
                        grade >= last_seen_grade) {
                    has_error = true;
                    invalid_input(g, gettext("calculator_grade_invalid"));
                } else {
                    last_seen_grade = grade;
                    valid_input(g);
                }
            }

            if (!has_error) {
                grade = grade.toString();
                if (!grade.match(/\./)) {
                    grade += ".0";
                }
                if (grade.match(/^\./)) {
                    grade = "0" + grade;
                }
                g.val(grade);
                p.val(percentage);
                saved_calculator_values.push({grade: grade,
                                              percentage: percentage});
            }
        });

        if (saved_calculator_values.length !== $(".gp-calculator-row").length) {
            clear_saved_data();
        }
        draw_grade_scale();
    }

    function save_conversion() {
        var seen_mins = {},
            error_count = 0,
            base;

        saved_grade_scale = [];
        $(".gp-scale-row").not(".gp-lowest-grade").each(function (idx) {
            var p = $(this).find("input[name='min-percentage']:first"),
                percentage = $.trim(p.val()),
                dupe_p;

            if (percentage === "") {
                error_count++;
                invalid_input(p, gettext("calculator_min_missing"));
            } else {
                percentage = Math.round(parseFloat(percentage) * 10) / 10;
                if (isNaN(percentage)) {
                    error_count++;
                    invalid_input(p, gettext("calculator_min_invalid"));
                } else if (seen_mins[percentage]) {
                    p.val(percentage);
                    invalid_input(p, gettext("min_percentage_duplicate"));
                    error_count++;
                    dupe_p = $(".gp-scale-row").eq(seen_mins[percentage])
                        .find("input[name='min-percentage']:first");
                    invalid_input(dupe_p, gettext("min_percentage_duplicate"));
                } else {
                    valid_input(p);
                }
            }
            seen_mins[percentage] = idx;
            saved_grade_scale.push({grade: scales[selected_scale][idx],
                                    min_percentage: 1 * percentage});
        });

        if (error_count === 0) {
            $(".gp-conversion-err").html("");
            render_container.trigger("saveGradeConversion", {
                "scale": selected_scale,
                "grade_scale": saved_grade_scale,
                "calculator_values": saved_calculator_values,
                "lowest_valid_grade": scales[selected_scale][scales[selected_scale].length - 1]
            });
        } else {
            base = ngettext("<strong>One invalid grade</strong> (see above)",
                            "<strong>%(count)s invalid grades</strong> (see above)",
                            error_count);
            $(".gp-conversion-err").html(interpolate(base, {count: error_count}, true));
        }
    }

    function cancel_conversion(ev) {
        ev.preventDefault();
        set_selected_scale("ug");
        clear_saved_data();
        render_container.trigger("cancelGradeConversion");
    }

    function reset_calculator(ev) {
        ev.preventDefault();
        clear_saved_data();
        draw_calculator();
        draw_grade_scale();
    }

    function reset_grade_scale(ev) {
        var tmp = saved_calculator_values;
        ev.preventDefault();
        clear_saved_data();
        draw_grade_scale();
        saved_calculator_values = tmp;
    }

    function change_grading_scale() {
        /*jshint validthis:true */
        set_selected_scale($(this).val());
        clear_saved_data();
        update_scale_selector();
        draw_calculator();
        draw_grade_scale();
    }

    function draw_convert_grades() {
        var template = Handlebars.compile($("#grade-conversion-calculator-tmpl").html());

        // pre-compiled templates
        calc_row_template = Handlebars.compile($("#calculator-row-tmpl").html());
        scale_row_template = Handlebars.compile($("#gradescale-row-tmpl").html());
        add_row_template = Handlebars.compile($("#calculator-addrow-tmpl").html());
        id_counter = 0;

        render_container.html(template({}));

        $(".gp-scale-selector").find("select")
                               .change(change_grading_scale);
        $(".gp-btn-convert-clear button").click(reset_calculator);
        $(".gp-btn-convert-apply button").click(apply_conversion);
        $(".gp-btn-scale-clear button").click(reset_grade_scale);
        $(".gp-convert-review").click(save_conversion);
        $(".gp-convert-cancel").click(cancel_conversion);

        update_scale_selector();
        draw_calculator();
        draw_grade_scale();
        render_container.trigger("renderedGradeConversion");
    }

    $.fn.grade_conversion_calculator = function (opts) {
        render_container = $(this);
        if (opts.hasOwnProperty("default_scale")) {
            set_selected_scale(opts.default_scale);
        }
        if (opts.hasOwnProperty("default_scale_values")) {
            set_saved_scale(opts.default_scale_values);
        }
        if (opts.hasOwnProperty("default_calculator_values")) {
            set_saved_calculator(opts.default_calculator_values);
        }
        build_scales();
        draw_convert_grades();
        return render_container;
    };
}(jQuery));
