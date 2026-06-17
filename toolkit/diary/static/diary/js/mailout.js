var mailoutController = function(options) {
    "use strict";

    const POLL_PERIOD = 1000; // milliseconds

    // Configured by setupPage:
    let mail_subject;
    let mail_body_text;
    let mail_body_html;
    let mail_send_html;
    let progressURL;
    let execURL;
    let testURL;
    let progressBar;
    let csrftoken;
    let jQuery;

    // States that page can be in:
    const S_READY = 0;
    const S_SENDING = 1;
    const S_COMPLETE = 2;
    const S_ABORTED = 3;
    const S_ERROR = 4;

    // State:
    let send_xhr;

    function setupPage(options) {
        mail_subject = options.subject;
        mail_body_text = options.body_text;
        mail_body_html = options.body_html;
        mail_send_html = options.send_html;

        progressURL = options.progressURL;
        execURL = options.execURL;
        testURL = options.testURL;
        const progressBarId = options.progressBarId;
        jQuery = options.jQuery;

        progressBar = jQuery("#" + progressBarId).progressbar(0);
        csrftoken = getCookie('csrftoken');
        set_state(S_READY);
    }

    function getCookie(name) {
        let cookieValue = null;
        if(document.cookie) {
            const cookies = document.cookie.split(';');
            for(let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if(cookie.substring(0, name.length + 1) === (name + '=')) {
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
        if(!data) {
            return;
        }

        if(data.complete !== true) {
            update_progress(data.progress);
            window.setTimeout(function() {
                jQuery.getJSON(
                    progressURL + '?task_id=' + data.task_id,
                    mail_send_progress_poll
                );
            }, POLL_PERIOD);
        } else {
            if(data.error === true) {
                set_state(S_ERROR);
                if(data.error_msg) {
                    jQuery('#error_msg').html(data.error_msg);
                }
            } else {
                set_state(S_COMPLETE);
                if(data.sent_count) {
                    jQuery('#sent_stats').html("(" + data.sent_count + " emails sent)");
                }
            }
        }
    }

    function mail_send_error(jqXHR, textStatus, errorThrown) {
        window.alert("Error: " + textStatus + " " + errorThrown);
    }

    function start_send() {
        set_state(S_SENDING);

        const data = jQuery.param({
            csrfmiddlewaretoken: csrftoken,
            subject: mail_subject,
            body_text: mail_body_text,
            body_html: mail_body_html,
            send_html: mail_send_html
        });

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
        const email = jQuery('#id_test_email').val();
        const email_regex = /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        if(email === "") {
            return;
        }
        if(!email_regex.test(email)) {
            alert("Invalid looking email: '" + email + "'");
            return;
        }

        jQuery('#test').html("Sending one copy to '" + email + "'");

        const data = jQuery.param({
            csrfmiddlewaretoken: csrftoken,
            address: email,
            subject: mail_subject,
            body_text: mail_body_text,
            body_html: mail_body_html,
            send_html: mail_send_html
        });

        send_xhr = jQuery.ajax(testURL, {
            'type': 'POST',
            'cache': false,
            'data': data,
            'dataType': 'json',
            'error': function(jqXHR, textStatus, errorThrown) {
                jQuery('#test').html("Failed sending one copy to '" + email +
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
