var setupTraining = function(options) {
    var GENERAL_TRAINING_VALUE = "general";

    set_field_links();
    $("#training-record form").submit(submit_training_form);
    // hack in the general training type:
    $('#id_training-role').prepend(
        '<option value="' + GENERAL_TRAINING_VALUE
        + '">General Safety Training</option>');
    // force something to be selected (where the browser supports it)
    $('#id_training-role').val('').attr("required", "");

    /* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

    function delete_complete(anchor) {
        anchor.closest('tr').next('tr').remove();
        anchor.closest('tr').remove();
    }

    function set_field_links() {
        $("a.toggle-notes").off().click(function () {
            var note_row = $(this).closest('tr').next('.training-notes');
            var new_text = note_row.is(":visible") ? "(+)" : "(-)";
            note_row.toggle();
            $(this).text(new_text);
            return false;
        });
        $("a.delete-training").off().click(function () {
            var a = $(this);
            var confirmed = confirm("Delete training record - are you sure?\nThis cannot be undone");
            if(confirmed) {
                jQuery.post(
                    $(this)[0].href,
                    {'csrfmiddlewaretoken': options.csrf_token},
                    function() { delete_complete(a); },
                    "text").fail(function(jqXHR, textStatus, errorThrown) {
                        alert("Network / server error when deleting training record: " + textStatus + ' ' + errorThrown);
                    });
            }
            return false;
        });
    }

    // Add a training record:
    function submit_training_form() {
        var url = options.add_training_record_url;
        var training_type;
        var role = $('#id_training-role').val();
        if (role === GENERAL_TRAINING_VALUE) {
            role = null;
            training_type = 'G';
        } else {
            training_type = 'R';
        }
        var data = {
            'csrfmiddlewaretoken': options.csrf_token,
            'training-role': role,
            'training-training_type': training_type,
            'training-trainer': $('#id_training-trainer').val(),
            'training-training_date': $('#id_training-training_date').val(),
            'training-notes': $('#id_training-notes').val(),
        };
        console.log("data:", data);
        $('#form-errors').hide();
        $('#form-errors').children().text('');
        jQuery.post(
            url,
            data,
            record_add_complete,
            "json").fail(function() {
                alert("Network / server error when adding training record");
            });
        return false;
    }

    function record_add_complete(data) {
        if(data.succeeded === true) {
            $("#training-record form")[0].reset();
            $('#new-record-row').before(
                '<tr>' +
                '    <td>' + data.training_description + '</td>' +
                '    <td>' + data.training_date + '</td>' +
                '    <td>' + data.trainer + '</td>' +
                '    <td>' +
                (data.notes !== '' ? '<a class="toggle-notes" href="#">(+)</a>' : '') +
                '    </td>' +
                '    <td>' +
                '<a class="delete-training" title="delete" href="' +
                options.delete_training_record_url.replace("9999", data.id) +
                '">[X]</a>' +
                '    </td>' +
                '</tr>' +
                '<tr class="training-notes">' +
                '    <td colspan="4">' +
                '        ' + data.notes +
                '    </td>' +
                '</tr>'
            );
            set_field_links();
        } else {
            $('#form-errors').show();
            var field_map = {'role': 0, 'training_date': 1, 'trainer': 2};
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
