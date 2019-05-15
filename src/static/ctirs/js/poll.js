$(function(){
    //error_msg表示
    function modify_taxii_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //pollボタンクリック
    $('.poll-detail-button').click(function(){
    	var id = $(this).attr('taxii_client_id');
    	var f = $('#poll-detail');
    	var action = f.attr('action');
    	//actionにidを付加する
    	f.attr('action',action + id);
    	f.submit();
    });

});
