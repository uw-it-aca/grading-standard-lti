/*jslint browser: true, plusplus: true */
/*global jQuery, Handlebars, top */
(function ($) {
    "use strict";
    $(document).ready(function () {

        var calculator_container = '.grade-standard-calculator-container';

        // prep for api post/put
        function csrfSafeMethod(method) {
            // these HTTP methods do not require CSRF protection
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }

        function prettyDate(d) {
            var m = ['Jan', 'Feb', 'Mar',
                     'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep',
                     'Oct', 'Nov', 'Dec'][d.getMonth()],
                h = d.getHours(),
                am = (h > 11) ? 'pm' : 'am';

            return m + '. ' + d.getDate() +
                ', ' + d.getFullYear() +
                ', ' + ((h > 12) ? (h - 12) : h) +
                ':' + ('0' + d.getMinutes()).slice(-2) + ' ' + am;
        }

        function ajaxFailureModal(msg) {
            var tpl = Handlebars.compile($('#ajax-fail-tmpl').html()),
                data = JSON.parse(msg),
                modal_container;

            $('body').append(tpl({failure_message: data.error}));
            modal_container = $('#failure-modal');
            modal_container.modal();
            modal_container.on('hidden.bs.modal', function () {
                modal_container.remove();
            });
        }

        function loadGradingStandard() {
            var tpl = Handlebars.compile($('#grading-standard').html());

            $('.canvas-UW-grade-scheme-container').html(tpl({}));

            $('li.selected-scheme').removeClass('selected-scheme');
            $('.saved-schemes').show();

            $('#CreateNew-btn').click(function (e) {
                e.preventDefault();
                loadGradingCalculator();
            });
        }

        function loadSaveSuccessMessage(standard) {
            var tpl = Handlebars.compile($('#grading-success-tmpl').html()),
                node = $('.canvas-UW-success-message');

            node.html(tpl({
                scheme_name: standard.name,
                course_name: window.grading_standard.course_title
            }));

            $('a', node).click(function (e) {
                e.preventDefault();
                top.location.replace(window.grading_standard.launch_presentation_return_url);
            });
        }

        function prependSavedScheme(scheme, which) {
            var tpl = Handlebars.compile($('#saved-scheme-tmpl').html()),
                schemes = $('#' + which + '_scheme_box ol li .scheme-name'),
                tpl_data = {
                    id: scheme.id,
                    name: scheme.name,
                    created_date: scheme.created_date,
                    saved: false
                },
                this_course = false,
                node;

            $.each(scheme.classes, function () {
                if (this.course === window.grading_standard.sis_course_id) {
                    this_course = true;
                    tpl_data.created_date = this.date;
                    return false;
                }
            });

            if (which !== 'saved') {
                tpl_data.saved = this_course;
            }

            node = $(tpl(tpl_data));

            if (schemes.length) {
                schemes.each(function () {
                    if (scheme.name === $(this).html()) {
                        node = null;
                        return false;
                    }
                });

                if (!node) {
                    return false;
                }

                $('#' + which + '_scheme_box ol li:first').before(node);
            } else {
                tpl = Handlebars.compile($('#' + which + '-schemes-tmpl').html());
                $('.' + which + '-schemes').html(tpl({
                    course_name: window.grading_standard.course_name
                }));
                $('#' + which + '_scheme_box ol').append(node);
            }

            $('a', node).click(function (e) {
                e.preventDefault();

                loadGradingCalculator({
                    scale_name: scheme.name,
                    default_scale: scheme.scale,
                    default_scale_values: scheme.scheme.slice()
                });

                $('li#saved_scheme_' + scheme.id).addClass('selected-scheme');
            });

            $('button', node).click(function () {
                var tmpl = Handlebars.compile($('#remove-modal-tmpl').html()),
                    modal_container;

                $('body').append(tmpl({
                    name: scheme.name,
                    scheme_edit_url: window.grading_standard.launch_presentation_return_url + '/grading_standards',
                    course_name: window.grading_standard.course_name
                }));
                modal_container = $('#remove-modal');
                modal_container.modal();
                modal_container.on('hidden.bs.modal', function () {
                    modal_container.remove();
                });

                $('#remove-scheme', modal_container).click(function () {
                    modal_container.modal('hide');
                    $.ajax({
                        type: 'DELETE',
                        url: 'api/v1/grading_standards/' + scheme.id,
                        async: false
                    }).fail(function (xhr) {
                        ajaxFailureModal(xhr.responseText);
                    }).done(function () {
                        $.each(window.grading_standard.saved_standards, function (i) {
                            if (this.id === scheme.id) {
                                window.grading_standard.saved_standards.splice(i, 1);
                                return false;
                            }
                        });

                        $('li#saved_scheme_' + scheme.id).fadeOut('fast', function () {
                            $(this).remove();
                            if (!$('#' + which + '_scheme_box ol li').length) {
                                $('.' + which + '-schemes').empty();
                            }
                        });
                    });
                });
            });
        }

        function postGradingStandard(name, scheme) {
            var request_data = {
                grading_standard: {
                    name: name,
                    course_id: window.grading_standard.sis_course_id,
                    scheme: scheme.grade_scale,
                    scale: scheme.scale
                }
            };

            $.ajax({
                type: 'POST',
                url: 'api/v1/grading_standards/',
                async: false,
                processData: false,
                contentType: 'application/json',
                data: JSON.stringify(request_data)
            }).fail(function (xhr) {
                ajaxFailureModal(xhr.responseText);
            }).done(function (msg) {
                var d = prettyDate(new Date(msg.grading_standard.created_date)),
                    standard = {
                        id: msg.grading_standard.id,
                        name: msg.grading_standard.name,
                        created_date: d,
                        scale: msg.grading_standard.scale,
                        scheme: msg.grading_standard.scheme,
                        classes: [{
                            course: window.grading_standard.sis_course_id,
                            date: d
                        }]
                    };

                $('body').scrollTop(0);

                loadGradingStandard();
                loadSaveSuccessMessage(standard);

                window.grading_standard.saved_standards.push(standard);
                prependSavedScheme(standard, 'saved');
            });
        }

        function saveGradingStandard(name, scheme) {
            var tpl,
                modal_container;

            // collect the name
            tpl = Handlebars.compile($('#name-and-save-tmpl').html());
            $('body').append(tpl({
                course_title: window.grading_standard.course_title,
                course_name: window.grading_standard.course_name
            }));
            modal_container = $('#save-scheme-modal');

            modal_container.on('hidden.bs.modal', function () {
                modal_container.remove();
            });

            modal_container.on('shown.bs.modal', function () {
                $('#scheme-name', modal_container).focus();
            });

            modal_container.modal();

            $('#scheme-name', modal_container).val(name.length ? 'Copy of ' + name : '');

            if (name.length === 0) {
                $('#save-valid-scheme', modal_container).prop('disabled', true);
            }

            $('#scheme-name', modal_container).on('keyup', function () {
                $('#duplicate-name', modal_container).hide();
                if ($(this).val().trim().length > 0) {
                    $('#save-valid-scheme', modal_container).prop('disabled', false);
                } else {
                    $('#save-valid-scheme', modal_container).prop('disabled', true);
                }
            });

            // save named scheme
            $('#save-valid-scheme', modal_container).click(function (e) {
                var scheme_name = $('#scheme-name', modal_container).val().trim(),
                    proceed = true;

                e.preventDefault();

                if (scheme_name.length) {
                    $.ajax({
                        type: 'GET',
                        url: 'api/v1/grading_standards/?name=' + encodeURIComponent(scheme_name),
                        async: false
                    }).fail(function (xhr) {
                        if (xhr.status !== 404) {
                            ajaxFailureModal(xhr.responseText);
                            modal_container.modal('hide');
                            proceed = false;
                        }
                    }).done(function () {
                        $('#duplicate-name', modal_container).show();
                        proceed = false;
                    });

                    if (!proceed) {
                        return false;
                    }

                    modal_container.modal('hide');
                    postGradingStandard(scheme_name, scheme);
                }
            });
        }

        function loadGradingCalculator(opts) {
            var tpl = Handlebars.compile($('#grading-calculator').html()),
                container_node,
                calc,
                calc_opts = {
                    default_scale: 'ug',
                    default_scale_values: [],
                    default_calculator_values: []
                },
                scale_name = '';

            $('.canvas-UW-success-message').empty();

            $('.canvas-UW-grade-scheme-container').html(tpl());

            // hide saved schemes
            $('.saved-schemes').hide();

            // add existing schemes
            $.each(window.grading_standard.saved_standards, function () {
                var standard = this;

                $.each(standard.classes, function () {
                    prependSavedScheme(standard, 'existing');
                });
            });

            container_node = $(calculator_container);

            if (typeof opts === 'object') {
                $.each(calc_opts, function (key) {
                    if (opts.hasOwnProperty(key)) {
                        calc_opts[key] = opts[key];
                    }
                });

                if (opts.hasOwnProperty("scale_name")) {
                    scale_name = opts.scale_name;
                    $('.canvas-UW-grade-scheme-container > h3').html(scale_name);
                }
            }

            container_node.on("renderedGradeConversion", function () {
                // removes visual cue on button
                $('button.gp-convert-review i', container_node).hide();

                // removes unused scale options
                $('#import_scale_selector option').not('[value=ug]').not('[value=gr]').remove();
            });

            calc = container_node.grade_conversion_calculator(calc_opts);

            calc.on("saveGradeConversion", function (e, scheme) {
                var same_scale = function (s1, s2) {
                    var dict = {};

                    $.each(s1, function () {
                        if (this.grade !== '0.0') {
                            dict[this.grade] = this.min_percentage;
                        }
                    });

                    $.each(s2, function () {
                        if (dict.hasOwnProperty(this.grade) && dict[this.grade] === this.min_percentage) {
                            delete dict[this.grade];
                        } else if (this.grade !== '0.0') {
                            return false;
                        }
                    });

                    return $.isEmptyObject(dict);
                };

                e.preventDefault();

                if (calc_opts.default_scale_values.length === 0 ||
                        calc_opts.default_scale !== scheme.scale ||
                        !same_scale(calc_opts.default_scale_values, scheme.grade_scale)) {
                    saveGradingStandard(scale_name, scheme);
                } else {
                    postGradingStandard(scale_name, scheme);
                }
            });

            calc.on("cancelGradeConversion", function (e) {
                e.preventDefault();
                loadGradingStandard();
            });
        }

        function reportErrorCount(error_count) {
            var tpl = Handlebars.compile($('#save-error-tmpl').html()),
                node;

            $('body').append(tpl({error_count: error_count}));
            node = $('#save-error-modal');
            node.modal();
            node.on('hidden.bs.modal', function () {
                node.remove();
            });
        }

        $.ajaxSetup({
            crossDomain: false, // obviates need for sameOrigin test
            beforeSend: function (xhr, settings) {
                if (window.grading_standard.session_id) {
                    xhr.setRequestHeader("X-SessionId", window.grading_standard.session_id);
                }
                if (!csrfSafeMethod(settings.type)) {
                    xhr.setRequestHeader("X-CSRFToken", window.grading_standard.csrftoken);
                }
            }
        });

        // load main content
        loadGradingStandard();

        $.each(window.grading_standard.saved_standards, function () {
            var standard = this;

            $.each(standard.classes, function () {
                if (this.course === window.grading_standard.sis_course_id) {
                    prependSavedScheme(standard, 'saved');
                    return false;
                }
            });
        });
    });
}(jQuery));
