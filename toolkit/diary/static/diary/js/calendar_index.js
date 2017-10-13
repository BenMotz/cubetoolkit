function init_calendar_view(jQuery, CSRF_TOKEN, defaultView, defaultDate, django_urls, resources) {
    "use strict";
    var $ = jQuery;

    var FLASH_MESSAGE_DISPLAY_TIME = 3000;
    var FLASH_MESSAGE_FADE_TIME = 1500;

    // state to detect when things have changed
    var currentView = defaultView;
    var currentDate = $.fullCalendar.moment(defaultDate);

    var clearMessageTimer = null;

    var resources_enabled = resources.length > 0 ? true : false;

    function onEventClick(calEvent, jsEvent, view) {
        var fb_target = $("#fb_target");
        fb_target.attr('href', calEvent.url);
        fb_target.click();
        return false;
    }

    function showIdeas(intervalStart) {
        $.getJSON(django_urls["edit-ideas"] + intervalStart.format("YYYY/M/"),
            function(data) {
                // Data is available from intervalStart in the context, but
                // pull it from the response anyway.
                var monthMoment = moment(data.month, "YYYY-MM-DD");
                var historic = monthMoment.isBefore(moment(), 'month');
                var edit_control_id = 'ideas-' + monthMoment.format("YYYY-M");
                var edit_control_html = '<h3>Ideas for '
                    + monthMoment.format("MMMM YYYY")
                    + ':</h3> <div class="idea'
                    + (historic ? '-historic' : '')
                    + '" id="' + edit_control_id + '">'
                    + (data.ideas !== null ? data.ideas : '')
                    + '</div></p>';

                $('#ideas').html(edit_control_html);

                // XXX: This isn't currently enforced server-side!
                if (!historic) {
                    $('#' + edit_control_id).editable(
                        django_urls["edit-ideas"] + monthMoment.format("YYYY/M/"),
                        {
                            width: "5cm",
                            name: 'ideas',
                            placeholder: 'Click to add ideas',
                            submit: "Save",
                            type: 'textarea',
                            rows: 5,
                            width: "auto",
                            submitdata: {
                                csrfmiddlewaretoken: CSRF_TOKEN,
                                source: 'inline',
                            }
                        }
                    );
                }
            }
        );

    }

    function showMessages() {
        // Get 'flash' messages, put thim in a div, show them for a few seconds
        $.getJSON(django_urls["get-messages"], function(data) {
            var message_html = '';
            var message_div = $("div.messages");

            if(data.length === 0) {
                return;
            }

            try {
                for(var i = 0; i < data.length; i++) {
                    message_html += '<li class="' + data[i].tags + '">'
                                    + data[i].message + '</li>';
                }
            } catch (e) {
                console.log("Failed processing messages: " + e
                            + " (data: '" + data + '"');
                return;
            }
            $(".messages ul").html(message_html);

            message_div.show()

            if(clearMessageTimer !== null) {
                window.clearTimeout(clearMessageTimer);
            }

            clearMessageTimer = window.setTimeout(function() {
                message_div.fadeOut(FLASH_MESSAGE_FADE_TIME);
                clearMessageTimer = null;
            }, FLASH_MESSAGE_DISPLAY_TIME);

            message_div.off('click').click(function() {
                message_div.hide();
            });
        });
    }

    function onDayClick(date, jsEvent, view, resource) {
        var url = django_urls["add-event"] + "?date=" + date.format("D-M-YYYY");
        var fb_target = $("#fb_target");
        if(date.isBefore(moment())) {
            return;
        }
        if(date.hasTime()) {
            // User clicked on a timeslot in week / day view: this is handled
            // by onSelect, so do nothing
            return;
        }
        if(resources_enabled && resource !== null && typeof resource === 'object'
            && resource.hasOwnProperty("id")) {
            url += "&room=" + resource.id;
        }
        fb_target.attr('href', url);
        fb_target.click();
    }

    function onSelect(start, end, jsEvent, view, resource) {
        var url = django_urls["add-event"] + "?date=" + start.format("D-M-YYYY");
        var calendar = $('#calendar');
        var fb_target = $("#fb_target");
        // Don't allow new events in the past. This is also enforced
        // server-side.
        if(start.isBefore(moment())) {
            calendar.fullCalendar('unselect');
            return;
        }
        if(start.hasTime() && end.hasTime()) {
            // User clicked on a timeslot in week / day view
            url += "&time=" + start.format("H:m");
            url += "&duration=" + (end.unix() - start.unix());
        };
        if(resources_enabled && resource !== null && typeof resource === 'object'
            && resource.hasOwnProperty("id")) {
            url += "&room=" + resource.id;
        }
        fb_target.attr('href', url);
        fb_target.click();
    }

    function onViewRender(view, element) {
        var calendar = $('#calendar');
        var newDate = calendar.fullCalendar('getDate');
        if(view.name === 'month' || view.name === 'timelineMonth') {
            var newUrl = django_urls['diary-edit-calendar'] + '/' + newDate.year()
                         + '/' + (newDate.month() + 1) + '/';

            if(!currentDate.isSame(newDate, 'month') || (currentView != view.name)) {
                history.replaceState(null, document.title, newUrl);
            }
        } else if(view.name === "agendaWeek" || view.name === "agendaThreeDay") {
            var newUrl = django_urls['diary-edit-calendar'] + '/' + newDate.year()
                         + '/' + (newDate.month() + 1)
                         + '/' + newDate.date();

            if(!currentDate.isSame(newDate, 'day') || (currentView != view.name)) {
                history.replaceState(null, document.title, newUrl);
            }
        }
        currentView = view.name;
        currentDate = newDate;
        showIdeas(view.intervalStart);
    }

    function init_fancybox() {
        var calendar = $('#calendar');
        var fb_target = $("#fb_target");
        fb_target.fancybox({
            openEffect: 'none',
            closeEffect: 'none',
            afterClose: function() {
                calendar.fullCalendar('unselect');
                calendar.fullCalendar('refetchEvents');
                showMessages();
            },
            iframe : {
                preload: false
            }
        });
    }

    function init_calendar() {
        var calendar = $('#calendar');
        currentDate = $.fullCalendar.moment(defaultDate);

        var calendar_options = {
            header: {
                left: 'prev,next today',
                center: 'title',
                right:
                    (resources_enabled ?
                        'agendaThreeDay,agendaWeek,month,timelineMonth'
                        : 'agendaWeek,month')
            },
            allDaySlot: false,
            defaultDate: defaultDate,
            defaultView: defaultView,
            editable: false,
            selectable: true,
            selectHelper: true,
            // Force events to a single day. It is valid to have a duration >
            // 24hr, but historically we've not done that to indicate multi-day
            // events, so nothing else is expecting it.
            selectConstraint: {
                start: '0:00',
                end: '23:59'
            },
            select: onSelect,
            eventLimit: true,
            timeFormat: 'H:mm',
            scrollTime: '18:00:00',
            nowIndicator: true,
            // The server will provide localised time. Don't mess with them:
            timezone: false,
            views: {
                agendaThreeDay: {
                    type: 'agenda',
                    duration: { days: 3 },
                    groupByResource: true,
                    groupByDateAndResource: true,
                    scrollTime: '10:00:00'
                },
                month: {
                    scrollTime: '10:00:00'
                },
                timelineMonth: {
                    buttonText: 'month timeline',
                }
            },
            events: django_urls["edit-diary-data"],
            eventClick: onEventClick,
            dayClick: onDayClick,
            viewRender: onViewRender,
            schedulerLicenseKey: 'GPL-My-Project-Is-Open-Source',
            resourceAreaWidth: "15%"
        };
        if(resources.length) {
            calendar_options.resources = resources;
        }

        calendar.fullCalendar(calendar_options);
    }

    $(document).ready(function() {
        var fb_target;

        init_fancybox();
        init_calendar();

        fb_target = $("#fb_target");

        $('#new-booking-link').click(function(){
            fb_target.attr('href', django_urls["add-event"]);
            fb_target.click();
            return false;
        });
    });
}
