/* Common setup for public content pages */

$(document).ready(function($){
    // init Masonry
    var $grid = $('.programme').masonry({
        percentPosition: true,
        gutter: '.gutter-sizer',
        columnWidth: '.grid-sizer',
        itemSelector: '.grid-item'
    });
    // layout Masonry after each image loads
    $grid.imagesLoaded().progress(function() {
       $grid.masonry('layout');
    });
});

// Belt and braces: do a final masonry layout after all images are
// definitely loaded:
$(window).load(function() {
    $('.programme').masonry('layout');
});

$(document).ready(function() {
    $("#mobile-menu-btn").click(function() {
        var toggle_el = $(this).data("toggle");
        $(toggle_el).toggleClass("open-sidebar");
        $(".black_overlay").toggleClass("active-search-bg");
    });
});

$(function() {
    $(".black_overlay").swipe({
        swipe: function(event, direction, distance, duration, fingerCount, fingerData) {
            $(".grid").removeClass("open-sidebar");
            $(".black_overlay").removeClass("active-search-bg");
        },
        threshold: 0
    });
});

$(document).ready(function() {
    $('#navmenu > ul > li:has(ul)').addClass("has-sub");
    $('#navmenu > ul > li > a').click(function() {
        var checkElement = $(this).next();

        $('#navmenu li').removeClass('active');
        $(this).closest('li').addClass('active');

        if((checkElement.is('ul')) && (checkElement.is(':visible'))) {
            $(this).closest('li').removeClass('active');
            checkElement.slideUp('normal');
        }

        if((checkElement.is('ul')) && (!checkElement.is(':visible'))) {
            $('#navmenu ul ul:visible').slideUp('normal');
            checkElement.slideDown('normal');
        }

        if (checkElement.is('ul')) {
            return false;
        } else {
            return true;
        }
    });
});
