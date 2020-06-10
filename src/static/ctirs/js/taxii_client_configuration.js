$(function(){
	
	if($('#create-ca').prop('checked') ==  false){
    	//Use Certificate Authentication にチェックが入っていない場合は非表示
    	$('#certificate-file-div').hide();
	}

    function taxii_submit(){
        var f = $('#create-taxii-client-form');
        f.submit();
    }

    //error_msg表示
    function modify_taxii_error(msg){
        $('#info-msg').html('');
        $('#error-msg').html(msg);
    }

    //community-nameのリストボックスをクリックした時
    $("#dropdown-menu-community-name li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-community-id').val($(this).attr("data-value"));
    });

    //protocol-versionのリストボックスをクリックした時
    $("#dropdown-protocol-version li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-protocol-version').val($(this).attr("data-value"));
    });

    //uploader のリストボックスをクリックした時
    $("#dropdown-menu-uploader li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-uploader-id').val($(this).attr("data-value"));
    });

    //submitボタンクリック
    $('#create-taxii-client-submit').click(function(){
    	//Setting Name check
        var name = $('#create-display-name').val();
        if(name.length == 0){
            modify_taxii_error('Enter Display Name');
            return;
        }
    	//Address check
        var address = $('#create-address').val();
        if(address.length == 0){
            modify_taxii_error('Enter Address');
            return;
        }
    	//port check
        var port_str = $('#create-port').val();
        if(port_str.length == 0){
        	modify_taxii_error('Enter port');
            return;
        }
        var port = Number(port_str);
        if (isNaN(port) == true){
        	modify_taxii_error('Invalid port');
            return;
        }
        if((port < 0) || (port > 65535)){
        	modify_taxii_error('Invalid port');
            return;
        }
    	//Path check
        var path = $('#create-path').val();
        if(path.length == 0){
            modify_taxii_error('Enter Path');
            return;
        }
    	//Collection check
        var collection = $('#create-collection').val();
        if(collection.length == 0){
            modify_taxii_error('Enter Collection');
            return;
        }
        //Use Certificate Authencationチェック時
        if($('#create-ca').prop('checked') == true){
            var certificate = $('#create-certificate').val();
            if(certificate.length == 0){
                modify_taxii_error('Enter Certificate');
                return;
            }
            var private_key = $('#create-private-key').val();
            if(private_key.length == 0){
                modify_taxii_error('Enter Private Key');
                return;
            }
            if($('#create-ssl').prop('checked') == false){
                modify_taxii_error('Not checked  Use SSL.');
                return;
            }
        } else{
        	//Login ID check
            var login_id = $('#create-login-id').val();
            if(login_id.length == 0){
                modify_taxii_error('Enter Login ID');
                return;
            }
        }
    	//Community check
        var community = $('#create-community-id').val();
        if(community.length == 0){
            modify_taxii_error('Choose Community.');
            return;
        }
    	//Protocol Version check
        var protocol_version = $('#create-protocol-version').val();
        if(protocol_version.length == 0){
            modify_taxii_error('Choose Protocol Version.');
            return;
        }
    	//Uploader check
        var uploader_id = $('#create-uploader-id').val();
        if(uploader_id.length == 0){
            modify_taxii_error('Choose Uploader.');
            return;
        }
        taxii_submit();
    });

    //deleteボタンクリック
    $('.delete-taxii-client-button').click(function(){
        var display_name = $(this).attr('display_name');
        var msg = 'Delete ' + display_name + '?';
        if(confirm(msg) == false){
            return
        }
        var f = $('#delete-taxii-client-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'display_name';
        elem.value = display_name;
        f.append(elem);
        f.submit();
    });

    //Modifyボタンクリック
    $('.modify-taxii-client-button').click(function(){
        $('#info-msg').html('');
        $('#error-msg').html('');
    	//Modifyボタンの行を取得
        var tr = $(this).closest('.configure-tr');
        //行の各値をテキストエリアとチェックボックスに反映(password/certificate/private以外)
        $('#create-display-name').val(tr.find('.display-name').text());
        $('#create-address').val(tr.find('.address').text());
        $('#create-port').val(tr.find('.port').text());
        $('#create-path').val(tr.find('.path').text());
        $('#create-collection').val(tr.find('.collection').text());
        $('#create-login-id').val(tr.find('.login-id').text());
        $('#create-login-password').val('');
        var ca = tr.find('.ca').prop("checked");
        var d = $('#certificate-file-div');
        $('#create-ca').prop("checked",ca);
        //certificate-file-divはcaの状態によってshow/hideを切り替える
        if(ca == true){
        	d.show();
        }
        else{
        	d.hide();
        }
        $('#create-ssl').prop("checked",tr.find('.ssl').prop("checked"));
        $('#create-community-id').val(tr.find('.community-id').val());
        $('#create-community-dropdown-button').text(tr.find('.community').text());
        $('#create-protocol-version-dropdown-button').text(tr.find('.protocol-version').text());
        $('#create-protocol-version').val(tr.find('.protocol-version').text());
        var push_flag = tr.find('.push').prop("checked");
        $('#create-push').prop("checked",push_flag);
        $('#create-uploader-id').val(tr.find('.uploader-id').val());
        $('#create-uploader-dropdown-button').text(tr.find('.uploader').text());
        $('#create-can-read').prop("checked",tr.find('.can-read').prop("checked"));
        $('#create-can-write').prop("checked",tr.find('.can-write').prop("checked"));
    });
    
    //Use Certificate Authenticationクリック
    //Animationモードのチェックボックスのステータス変更時
    $('#create-ca').click(function(){
    	$('#certificate-file-div').toggle();
    	if($(this).prop('checked') ==  true){
    		$('#create-ssl').prop('checked',true);
    	}
    }); 

    //detailボタンクリック
    $('.detail-taxii-client-button').click(function(){
    	var id = $(this).attr('taxii_client_id');
    	var f = $('#configuration-taxii-client-detail');
    	var action = f.attr('action');
    	//actionにidを付加する
    	f.attr('action',action + id);
    	f.submit();
    });
});
