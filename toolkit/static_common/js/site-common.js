/* Common setup for public content pages */
function setup_page (index_page) {
  $(document).ready(function ($) {
    /* set up small form factor menu --------------------------------------- */
    function toggleSidebar () {
      $('.grid').toggleClass('grid--open-sidebar')
      $('.sidebar').toggleClass('sidebar--open')
      $('.programme').attr(
        'inert',
        $('.programme').attr('inert') === 'true' ? null : 'true'
      )
    }

    $('#mobile-menu-btn').click(toggleSidebar)

    $('.grid').swipe({
      swipe: function (
        event,
        direction,
        distance,
        duration,
        fingerCount,
        fingerData
      ) {
        if ($('.grid').hasClass('grid--open-sidebar')) toggleSidebar()
      },
      threshold: 0
    })

    /* Set up nav menu ----------------------------------------------------- */
    $('#navmenu > ul > li:has(ul)').addClass('has-sub')

    $('#navmenu > ul > li > a').click(function () {
      var checkElement = $(this).next()

      $('#navmenu li').removeClass('active')
      $(this)
        .closest('li')
        .addClass('active')

      if (checkElement.is('ul') && checkElement.is(':visible')) {
        $(this)
          .closest('li')
          .removeClass('active')
        checkElement.slideUp('normal')
      }

      if (checkElement.is('ul') && !checkElement.is(':visible')) {
        $('#navmenu ul ul:visible').slideUp('normal')
        checkElement.slideDown('normal')
      }

      if (checkElement.is('ul')) {
        return false
      } else {
        return true
      }
    })

    /* Set up grid/list switcher (event list only) ------------------------- */
    $('a#listbtn.switcher').click(function () {
      $('.programme').animate({ opacity: 0 }, function () {
        $('.programme').hide()
        $('.list').addClass('active')
        $('.list.active')
          .stop()
          .animate({ opacity: 1 })
      })
    })

    $('a#gridbtn.switcher').click(function () {
      $('.list').animate({ opacity: 0 }, function () {
        $('.list').removeClass('active')
        $('.programme').show()
        $('.programme')
          .stop()
          .animate({ opacity: 1 })
      })
    })
  })
}
