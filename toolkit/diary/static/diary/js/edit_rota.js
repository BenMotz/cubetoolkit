function edit_rota(jQuery, rota_edit_base_url, edit_rota_notes_url_prefix, CSRF_TOKEN) {
    "use strict";
    var $ = jQuery;

    function parse_date_from_control(control_id) {
        var text = $(control_id)[0].value;
        return $.datepicker.parseDate('dd-mm-yy', text);
    }

    function dateRangeSelected() {
        var from_date = parse_date_from_control('#id_from_date'),
            to_date = parse_date_from_control('#id_to_date'),
            // Calculate days between those two dates:
            days_ahead = Math.ceil(
                (to_date.getTime() - from_date.getTime()) / 86400000
            );
        if (days_ahead <= 0) {
            days_ahead = 0;
        }
        window.location.href = rota_edit_base_url + "/" +
            (from_date.getYear() + 1900) + "/" + (from_date.getMonth() + 1) +
            "/" + from_date.getDate() + "?daysahead=" + days_ahead;
    }

    function configureDatePickerControls() {
        // Add date picker:
        $('#id_from_date').datepicker({
            dateFormat : 'dd-mm-yy',
            onSelect : dateRangeSelected
        });
        $('#id_to_date').datepicker({
            dateFormat : 'dd-mm-yy',
            onSelect : dateRangeSelected
        });
        $('#daterange')[0].onsubmit = function() {
            dateRangeSelected();
            return false;
        };
    }

    function configureRotaNameEditInPlaceControls() {
        $('.rota_name').editable('', {
            width: "5cm",
            placeholder: '<span class="na">Click to edit</span>',
            submit: "Save",
            submitdata: {
                csrfmiddlewaretoken: CSRF_TOKEN
            }
        });
    }

    function configureRotaNotesEditInPlaceControls() {
        var showing_id_re = /showing_rota_notes_(\d+)/;

        $('.showing_rota_notes span').each(function () {
            var showing_id,
                element = $(this),
                showing_id_match = showing_id_re.exec(element.attr('id'));

            if (showing_id_match) {
                showing_id = showing_id_match[1];
                element.editable(
                    edit_rota_notes_url_prefix + showing_id + "/rota_notes/",
                    {
                        name: 'rota_notes',
                        type: 'textarea',
                        rows: 5,
                        width: '90%',
                        placeholder: '<span class="na">General notes (click to edit)</span>',
                        submit: 'Save',
                        submitdata: {
                            csrfmiddlewaretoken: CSRF_TOKEN
                        }
                    }
                );
            }
        });
    }

    $(document).ready(function() {
        configureDatePickerControls();
        configureRotaNameEditInPlaceControls();
        configureRotaNotesEditInPlaceControls();
    });
}
