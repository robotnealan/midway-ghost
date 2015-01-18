$( document ).ready(function() {

	$('.post-content img').parent('p').addClass('image');
	
	$('.menu-trigger').on('click', function(e) {
		e.preventDefault();
		$('body').toggleClass('menu-open');
	});

	$('.page-wrapper').on('click', function(e) {
		if($('body').hasClass('menu-open')) {
			if( !$( e.target ).hasClass( 'menu-trigger' ) ) {
		        $('body').removeClass('menu-open');
		    }
		}
	});
});