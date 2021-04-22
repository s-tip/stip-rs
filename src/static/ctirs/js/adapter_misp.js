$(function(){
    $('[data-toggle="popover"]').popover();
    function modify_misp_submit(){
        var f = $('#modify-misp-form');
        f.submit();
    }

    //error_msg表示
    function modify_misp_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //modifyボタンクリック
    $('#modify-misp-submit').click(function(){
    	var url = $('#modify-misp-url').val()
    	if(url.length == 0){
    		modify_misp_error('Enter URL.');
    		return;
    	}
    	var apikey = $('#modify-misp-apikey').val()
    	if(apikey.length == 0){
    		modify_misp_error('Enter APIKEY.');
    		return;
    	}
    	var community_id = $('#modify-community-id').val()
    	if(community_id.length == 0){
    		modify_misp_error('Choose Community.');
    		return;
    	}
    	var uploader_id = $('#modify-uploader-id').val()
    	if(uploader_id.length == 0){
    		modify_misp_error('Choose Uploader.');
    		return;
        }
        var stix_version = $('#modify-stix-version').val()
    	if(stix_version.length == 0){
    		modify_misp_error('Choose STIX Version.');
    		return;
        }

        modify_misp_submit();
    });

    //startボタンクリック
    $('#get-misp-submit').click(function(){
        var f = $('#get-misp-form');
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

    $("#dropdown-menu-stix-version li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#modify-stix-version').val($(this).attr("data-value"));
    });
    //detailボタンクリック
    $('#misp-detail-button').click(function(){
        var f = $('#misp-detail');
        f.submit();
    });
});
