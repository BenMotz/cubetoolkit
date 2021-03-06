var mailoutController = function (options) {
    "use strict";

    var POLL_PERIOD = 1000; // milliseconds

    // Configured by setupPage:
    var mail_subject;
    var mail_body_text;
    var mail_body_html;
    var mail_send_html;
    var progressURL;
    var execURL;
    var testURL;
    var progressBar;
    var csrftoken;
    var jQuery;

    // States that page can be in:
    var S_READY = 0;
    var S_SENDING = 1;
    var S_COMPLETE = 2;
    var S_ABORTED = 3;
    var S_ERROR = 4;

    // State:
    var send_xhr;

    function setupPage(options) {
        var progressBarId;

        mail_subject = options.subject;
        mail_body_text = options.body_text;
        mail_body_html = options.body_html;
        mail_send_html = options.send_html;

        progressURL = options.progressURL;
        execURL = options.execURL;
        testURL = options.testURL;
        progressBarId = options.progressBarId;
        jQuery = options.jQuery;

        progressBar = jQuery("#" + progressBarId).progressbar(0);
        csrftoken = getCookie('csrftoken');
        set_state(S_READY);
    }

    function getCookie(name) {
        var cookieValue = null, cookies, cookie, i;
        if (document.cookie) {
            cookies = document.cookie.split(';');
            for (i = 0; i < cookies.length; i++) {
                cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function update_progress(percentage) {
        progressBar.progressbar('value', percentage);
    }

    function mail_send_progress_poll(data) {
        if (!data) {
            return;
        }

        if (data.complete !== true) {
            update_progress(data.progress);
            window.setTimeout(function() {
                jQuery.getJSON(
                    progressURL + '?task_id=' + data.task_id,
                    mail_send_progress_poll
                );
            }, POLL_PERIOD);
        } else {
            if (data.error === true) {
                set_state(S_ERROR);
                if (data.error_msg) {
                    jQuery('#error_msg').html(data.error_msg);
                }
            } else {
                set_state(S_COMPLETE);
                if (data.sent_count) {
                    jQuery('#sent_stats').html("(" + data.sent_count + " emails sent)");
                }
            }
        }
    }

    function mail_send_error(jqXHR, textStatus, errorThrown) {
        window.alert("Error: " + textStatus + " " + errorThrown);
    }

    function start_send() {
        var data;

        set_state(S_SENDING);

        data = 'csrfmiddlewaretoken=' + encodeURIComponent(csrftoken) +
               '&subject=' +  encodeURIComponent(mail_subject) +
               '&body_text=' + encodeURIComponent(mail_body_text) +
               '&body_html=' + encodeURIComponent(mail_body_html) +
               '&send_html=' + encodeURIComponent(mail_send_html);

        send_xhr = jQuery.ajax(execURL, {
            'type': 'POST',
            'cache': false,
            'data': data,
            'dataType': 'json',
            'error': mail_send_error,
            'success': mail_send_progress_poll
        });

        window.setTimeout(mail_send_progress_poll, 100);
    }

    function cancel_send() {
        set_state(S_ABORTED);
    }

    function test_send() {
        var email = jQuery('#id_test_email').val();
        var email_regex = /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        if(email === "") {
            return;
        }
        if(!email_regex.test(email)) {
            alert("Invalid looking email: '" + email + "'");
            return;
        }

        jQuery('#test').html("Sending one copy to '" + email + "'");

        var data = 'csrfmiddlewaretoken=' + encodeURIComponent(csrftoken) +
               '&address=' + encodeURIComponent(email) +
               '&subject=' +  encodeURIComponent(mail_subject) +
               '&body_text=' + encodeURIComponent(mail_body_text) +
               '&body_html=' + encodeURIComponent(mail_body_html) +
               '&send_html=' + encodeURIComponent(mail_send_html);

        send_xhr = jQuery.ajax(testURL, {
            'type': 'POST',
            'cache': false,
            'data': data,
            'dataType': 'json',
            'error': function (jqXHR, textStatus, errorThrown) {
                jQuery('#test').html("Failed sending one copy to '" + email  +
                    "': " + textStatus + " " + errorThrown);
            },
            'success': function(data) {
                if(data.status === 'ok') {
                    jQuery('#test').html("Sent one copy to '" + email + "'");
                } else {
                    jQuery('#test').html("Failed sending one copy to '" +
                        email + "': " + data.errors);
                }
            },
        });
    }

    function set_state(state) {
        switch (state) {
        case S_READY:
            update_progress(0);
            jQuery('#status').html('Please read through and check the text ' +
                'below, then click <span id="send">Send</span> when ' +
                'you\'re sure...');
            jQuery('#send').button().click(start_send);
            jQuery('#test_send').button().click(test_send);
            break;
        case S_SENDING:
            jQuery('#status').html('Sending. If you change your mind then ' +
                '<span id="cancel">Cancel</span>');
            jQuery('#cancel').button().click(cancel_send);
            jQuery('#test_send').button("disable");
            break;
        case S_ABORTED:
            jQuery('#status').html('Sending aborted not yet implemented!');
            jQuery('#test_send').button("disable");
            break;
        case S_COMPLETE:
            update_progress(100);
            jQuery('#status').html('Success! <span id="sent_stats"></span>');
            jQuery('#test_send').button("disable");
            break;
        case S_ERROR:
            jQuery('#status').html('An error occurred: <span id="error_msg">' +
                '(unknown)</span>');
            jQuery('#test_send').button("disable");
            break;
        }
    }

    setupPage(options);
};
