$(function(){
    $('[data-toggle="popover"]').popover();
    function modify_otx_submit(){
        var f = $('#modify-otx-form');
        f.submit();
    }

    //error_msg表示
    function modify_otx_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //modifyボタンクリック
    $('#modify-otx-submit').click(function(){
    	var apikey = $('#modify-otx-apikey').val()
    	if(apikey.length == 0){
    		modify_otx_error('Enter APIKEY.');
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
        modify_otx_submit();
    });

    //startボタンクリック
    $('#get-otx-submit').click(function(){
        var f = $('#get-otx-form');
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
    $('#otx-detail-button').click(function(){
        var f = $('#otx-detail');
        f.submit();
    });
});
