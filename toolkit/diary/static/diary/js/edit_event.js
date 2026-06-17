"use strict";
var setupPage = function(options) {
    const bookings_form = $("#bookings form");
    bookings_form.submit(submit_new_showing_form);
    $('#form-errors').hide();

    // Add a showing
    function submit_new_showing_form() {
        const url = options.add_booking_url;
        const data = {
            'csrfmiddlewaretoken': options.csrfmiddlewaretoken,
            'clone_start': $('#id_clone_start').val(),
            'booked_by': $('#id_booked_by').val(),
        };
        $('#form-errors').hide();
        $('#form-errors').children().text('');
        $.post(
            url,
            data,
            showing_add_complete,
            "json").fail(function(r) {
                console.log("Failed: ", r);
                alert("Network / server error when adding booking (" + r.status + ')');
            });
        return false;
    }

    function showing_add_complete(data) {
        if(data.succeeded === true) {
            bookings_form[0].reset();
            $('#form-errors').before(data.html);
        } else {
            $('#form-errors').show();
            const field_map = {'clone_start': 0, 'booked_by': 1};
            for(const field in data.errors) {
                let messages;
                if(data.errors.hasOwnProperty(field)) {
                    messages = data.errors[field].join(', ');
                }
                $('#form-errors').children().eq(field_map[field]).text(messages);
            }
        }
    }
};
