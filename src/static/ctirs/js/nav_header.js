$(function(){
    //navvarの内、現在のリンク項目にactive classを付与
    $('.nav li a').each(function(){
    	var href = $(this).attr('href');
        if(location.href.match(href)) {
    	    $(this).addClass('active');
        } else {
    	    $(this).removeClass('active');
        }
    	//configuration項目のサブ項目選択時はConfigurationにactive classを付与
    	var conf = $('#navbar-configuration')
    	if (location.href.match('/configuration')){
    		conf.addClass('active')
    	}
    	else{
    		conf.removeClass('active')
    	}
    });
});
