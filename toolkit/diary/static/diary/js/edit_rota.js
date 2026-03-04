function edit_rota(jQuery, rota_edit_base_url, edit_rota_notes_url_prefix, vol_email, CSRF_TOKEN) {
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
            onSelect : dateRangeSelected,
            minDate : 0
        });
        $('#id_to_date').datepicker({
            dateFormat : 'dd-mm-yy',
            onSelect : dateRangeSelected,
            minDate : 0
        });
        $('#daterange')[0].onsubmit = function() {
            dateRangeSelected();
            return false;
        };
    }

    function nameEditedCallback(value) {
        if (value === "" && this.revert !== "") {
            window.alert("Rota entry cleared.\nPlease consider emailing " +
                         vol_email +
                         " to say that the shift needs covering.");
        }
    }

    function configureRotaNameEditInPlaceControls() {
        $('.rota_name').editable('', {
            width: "25%",
            placeholder: '<span class="na">Click to edit</span>',
            submit: "Save",
            submitdata: {
                csrfmiddlewaretoken: CSRF_TOKEN
            },
            callback: nameEditedCallback
        });
    }

    function unEscape(text) {
        // The inverse of the python stdlib html.escape
        return text
            .replace(/&amp;/g,  '&')
            .replace(/&lt;/g,   '<')
            .replace(/&gt;/g,   '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g,  "'")
            .replace(/&#x27;/g, "'");
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
                        },
                        // So, this is confusing.
                        // 1. The template populates the notes with escaped text (&amp; etc.)
                        // 2. The user clicks 'edit'. Before displaying the DOM node in the edit control,
                        //    this function is called to un-escape most entities that people use
                        // 3. The user edits beautiful clear text, happily adding ampersands, and clicks "save"
                        // 4. The unescaped text is sent to the server, saved, and returned escaped (back to &amp;)
                        // 5. The escaped text is inserted into the DOM, and the cycle continues
                        data: unEscape
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
