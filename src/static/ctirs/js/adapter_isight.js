$(function(){
    function modify_isight_submit(){
        var f = $('#modify-isight-form');
        f.submit();
    }

    //error_msg表示
    function modify_isight_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //modifyボタンクリック
    $('#modify-isight-submit').click(function(){
    	var public_key = $('#modify-isight-public-key').val()
    	if(public_key.length == 0){
    		modify_isight_error('Enter Public Key.');
    		return;
    	}
    	var private_key = $('#modify-isight-private-key').val()
    	if(private_key.length == 0){
    		modify_isight_error('Enter Private Key.');
    		return;
    	}
    	var community_id = $('#modify-community-id').val()
    	if(community_id.length == 0){
    		modify_isight_error('Choose Community.');
    		return;
    	}
    	var uploader_id = $('#modify-uploader-id').val()
    	if(uploader_id.length == 0){
    		modify_isight_error('Choose Uploader.');
    		return;
    	}
        modify_isight_submit();
    });

    //startボタンクリック
    $('#get-isight-submit').click(function(){
        var f = $('#get-isight-form');
        f.submit();
    });

    //community-nameのリストボックスをクリックした時
    $("#dropdown-menu-community-name li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#modify-community-id').val($(this).attr("data-value"));
    });

    //uploaderのリストボックスをクリックした時
    $("#dropdown-menu-uploader-name li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#modify-uploader-id').val($(this).attr("data-value"));
    });

    //detailボタンクリック
    $('#isight-detail-button').click(function(){
        var f = $('#isight-detail');
        f.submit();
    });
});
