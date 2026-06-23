function edit_rota(jQuery, rota_edit_base_url, edit_rota_notes_url_prefix, vol_email, CSRF_TOKEN) {
    "use strict";
    const $ = jQuery;
    let fromDatePicker;
    let toDatePicker;

    function dateRangeSelected() {
        const fromDate = fromDatePicker.selectedDates[0];
        const toDate = toDatePicker.selectedDates[0];
        if(!fromDate || !toDate) {
            console.error("fromDate or toDate is null", fromDate, toDate);
	    return;
        }
        // Calculate days between those two dates:
        let daysAhead = Math.ceil(
            (toDate.getTime() - fromDate.getTime()) / 86400000
        );
        if(daysAhead <= 0) {
            daysAhead = 0;
        }
        window.location.href = rota_edit_base_url + "/" +
            fromDate.getFullYear() + "/" + (fromDate.getMonth() + 1) +
            "/" + fromDate.getDate() + "?daysahead=" + daysAhead;
    }

    function configureDatePickerControls() {
        // Add date picker:
        fromDatePicker = flatpickr('#id_from_date', {
           dateFormat: 'd-m-Y',
           onChange: dateRangeSelected,
           minDate: 'today',
        });
        toDatePicker = flatpickr('#id_to_date', {
            dateFormat: 'd-m-Y',
            onChange: dateRangeSelected,
            minDate: 'today',
        });
        $('#daterange')[0].onsubmit = function() {
            dateRangeSelected();
            return false;
        };
    }

    function nameEditedCallback(value) {
        if(value === "" && this.revert !== "") {
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
        const showing_id_re = /showing_rota_notes_(\d+)/;

        $('.showing_rota_notes span').each(function() {
            const element = $(this),
                showing_id_match = showing_id_re.exec(element.attr('id'));

            if(showing_id_match) {
                const showing_id = showing_id_match[1];
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
