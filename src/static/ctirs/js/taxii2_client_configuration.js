$(function(){
    function taxii2_submit(){
        var f = $('#create-taxii2-client-form');
        f.submit();
    }

    function modify_taxii2_error(msg){
        $('#info-msg').html('');
        $('#error-msg').html(msg);
    }

    if($('#create-ca').prop('checked') ==  false){
        $('#certificate-file-div').hide();
    }

    $("#dropdown-menu-community-name li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-community-id').val($(this).attr("data-value"));
    });

    $("#dropdown-protocol-version li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-protocol-version').val($(this).attr("data-value"));
    });

    $("#dropdown-menu-uploader li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-uploader-id').val($(this).attr("data-value"));
    });

    $('#create-taxii2-client-submit').click(function(){
        var name = $('#create-display-name').val();
        if(name.length == 0){
            modify_taxii2_error('Enter Display Name');
            return;
        }
        var api_root = $('#create-api-root').val();
        if(api_root.length == 0){
            modify_taxii2_error('Enter API Root');
            return;
        }
        var collection = $('#create-collection').val();
        if(collection.length == 0){
            modify_taxii2_error('Enter Collection');
            return;
        }
        if($('#create-ca').prop('checked') == true){
            if($('#create-certificate').val().length == 0){
                modify_taxii2_error('Enter Certificate');
                return;
            }
            if($('#create-private-key').val().length == 0){
                modify_taxii2_error('Enter Private Key');
                return;
            }
        } else{
            var login_id = $('#create-login-id').val();
            if(login_id.length == 0){
                modify_taxii2_error('Enter Login ID');
                return;
            }
            $('#create-certificate').val('');
            $('#create-private-key').val('');
        }
        var community = $('#create-community-id').val();
        if(community.length == 0){
            modify_taxii2_error('Choose Community.');
            return;
        }
        var protocol_version = $('#create-protocol-version').val();
        if(protocol_version.length == 0){
            modify_taxii2_error('Choose Protocol Version.');
            return;
        }
        var uploader_id = $('#create-uploader-id').val();
        if(uploader_id.length == 0){
            modify_taxii2_error('Choose Uploader.');
            return;
        }
        taxii2_submit();
    });

    $('.delete-taxii2-client-button').click(function(){
        var display_name = $(this).attr('display_name');
        var msg = 'Delete ' + display_name + '?';
        if(confirm(msg) == false){
            return
        }
        var f = $('#delete-taxii2-client-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'display_name';
        elem.value = display_name;
        f.append(elem);
        f.submit();
    });

    $('.modify-taxii2-client-button').click(function(){
        $('#info-msg').html('');
        $('#error-msg').html('');
        var tr = $(this).closest('.configure-tr');
        $('#create-display-name').val(tr.find('.display-name').text());
        $('#create-api-root').val(tr.find('.api-root').text());
        $('#create-collection').val(tr.find('.collection').text());
        $('#create-login-id').val(tr.find('.login-id').text());
        $('#create-login-password').val('');
        var ca = tr.find('.ca').prop("checked");
        var d = $('#certificate-file-div');
        $('#create-ca').prop("checked",ca);
        if(ca == true){
            d.show();
        }
        else{
            d.hide();
        }
        $('#create-community-id').val(tr.find('.community-id').val());
        $('#create-community-dropdown-button').text(tr.find('.community').text());
        $('#create-protocol-version-dropdown-button').text(tr.find('.protocol-version').text());
        $('#create-protocol-version').val(tr.find('.protocol-version').text());
        var push_flag = tr.find('.push').prop("checked");
        $('#create-push').prop("checked",push_flag);
        $('#create-uploader-id').val(tr.find('.uploader-id').val());
        $('#create-uploader-dropdown-button').text(tr.find('.uploader').text());
        $('#create-can-read').prop("checked",tr.find('.can-read').prop("checked"));
        $('#create-can-write').prop("checked",tr.find('.can-write').prop("checked"))
    });
    
    $('.detail-taxii2-client-button').click(function(){
    	var id = $(this).attr('taxii2_client_id');
    	var f = $('#configuration-taxii2-client-detail');
    	var action = f.attr('action');
    	f.attr('action',action + id);
    	f.submit();
    });

    $('#create-ca').click(function(){
        $('#certificate-file-div').toggle();
        if($(this).prop('checked') ==  true){
            $('#create-ssl').prop('checked',true);
        }
    }); 
});
