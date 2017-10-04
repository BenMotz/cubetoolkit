/* Common setup for public content pages */

$(document).ready(function($){
    /* init Masonry -------------------------------------------------------- */
    var $grid = $('.programme').masonry({
        percentPosition: true,
        gutter: '.gutter-sizer',
        columnWidth: '.grid-sizer',
        itemSelector: '.grid-item'
    });

    // re-layout Masonry after each image loads
    $grid.imagesLoaded().progress(function() {
       $grid.masonry('layout');
    });

    /* set up small form factor menu --------------------------------------- */
    $("#mobile-menu-btn").click(function() {
        var toggle_el = $(this).data("toggle");
        $(toggle_el).toggleClass("open-sidebar");
        $(".black_overlay").toggleClass("active-search-bg");
    });

    $(".black_overlay").swipe({
        swipe: function(event, direction, distance, duration, fingerCount, fingerData) {
            $(".grid").removeClass("open-sidebar");
            $(".black_overlay").removeClass("active-search-bg");
        },
        threshold: 0
    });

    /* Set up nav menu ----------------------------------------------------- */
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

    /* Set up grid/list switcher (event list only) ------------------------- */
    $('a#listbtn.switcher').click(function() {
        $('.programme').animate({opacity: 0},function() {
            $('.programme').hide();
            $('.list').addClass('active');
            $('.list.active').stop().animate({opacity: 1});
        });
    });

    $('a#gridbtn.switcher').click(function() {
        $('.list').animate({opacity:0},function() {
            $('.list').removeClass('active');
            $('.programme').show();
            $('.programme').masonry({
                gutter: '.gutter-sizer',
                columnWidth: '.showing-sizer',
                itemSelector: '.showing'
            });
            $('.programme').stop().animate({opacity: 1});
        });
    });
});

// Belt and braces: do a final masonry layout after all images are
// definitely loaded:
$(window).load(function() {
    $('.programme').masonry('layout');
});
