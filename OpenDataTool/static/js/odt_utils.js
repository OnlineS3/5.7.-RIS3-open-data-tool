$(document).ready(function() {
    window.addEventListener('resize', function(){
        $('.carousel').css('min-height', $(window).height() - 50);
    });
    window.dispatchEvent(new Event('resize'));

    $('#navigator').affix({
        offset: { top: 227 }
    });
});

function scrollToElement(element) {
    $('html, body').animate({
        scrollTop: $(element).offset().top - 50 + 'px'
    }, 'fast');
}