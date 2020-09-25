$(function(){
    $('[data-toggle="popover"]').popover();
    //error_msg表示
    function modify_taxii_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //pollボタンクリック
    $('#poll-start-submit').click(function(){
    	var f = $('#poll-start-form');
    	f.submit();
    });

});
