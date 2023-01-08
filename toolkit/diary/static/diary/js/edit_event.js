"use strict";
var setupPage = function(options) {
    var bookings_form = $("#bookings form");
    bookings_form.submit(submit_new_showing_form);
    $('#form-errors').hide();

    // Add a showing
    function submit_new_showing_form() {
        var url = options.add_booking_url;
        var data = {
            'csrfmiddlewaretoken': options.csrfmiddlewaretoken,
            'clone_start': $('#id_clone_start').val(),
            'booked_by': $('#id_booked_by').val(),
        };
        $('#form-errors').hide();
        $('#form-errors').children().text('');
        jQuery.post(
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
            var field_map = {'clone_start': 0, 'booked_by': 1};
            for (var field in data.errors) {
                var i;
                if (data.errors.hasOwnProperty(field)) {
                    var messages = data.errors[field].join(', ');
                }
                $('#form-errors').children().eq(field_map[field]).text(messages);
            }
        }
    }
};
