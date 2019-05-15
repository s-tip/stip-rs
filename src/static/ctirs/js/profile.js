$(function(){

    function change_password_submit(){
        //passwordフィールドを作成
        var f = $('#change-password');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'new_password';
        elem.value = $('#new-password-1').val();
        f.append(elem);
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'old_password';
        elem.value = $('#old-password').val();
        f.append(elem);
        f.submit();
    }

    function change_screen_name_submit(){
        //scree_nameフィールドを作成
        var f = $('#change-screen-name');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'screen_name';
        elem.value = $('#screen-name').val();
        f.append(elem);
        f.submit();
    }

    //error_msg表示
    function change_password_error(msg){
        $('#error-change-password-msg').text(msg);
        $('#info-change-password-msg').text('');
    }

    //Change Passwordボタンクリック
    $('#change-password-submit').click(function(){
        var old_password = $('#old-password').val();
        if(old_password.length == 0){
            change_password_error('Enter Old Password');
            return;
        }
        var new_pwd_1 = $('#new-password-1').val();
        if(new_pwd_1.length == 0){
            change_password_error('Enter New Password');
            return;
        }
        var new_pwd_2 = $('#new-password-2').val();
        if(new_pwd_2.length == 0){
            change_password_error('Enter New Password(again)');
            return;
        }
        if(new_pwd_1 != new_pwd_2){
            change_password_error('Enter Same New Password.');
            return;
        }
        change_password_submit();
    });

    //Change Screen Nameボタンクリック
    $('#change-screen-name-submit').click(function(){
        change_screen_name_submit();
    });
    
    
    //Change APIKEYボタンクリック
    $('#change-api-key-submit').click(function(){
        var d = {};
        //ajax呼び出し
        $.ajax({
            type: 'GET',
            url: '/profile/ajax/change_api_key',
            timeout: 100 * 1000,
            cache: true,
            data: d,
            dataType: 'json',
        }).done(function(r,textStatus,jqXHR){
            if(r['status'] != 'OK'){
                alert('change_api_key failed:' + r['message'], 'Error!');
            }
            $('#api-key').val(r['api_key'])
        }).fail(function(jqXHR,textStatus,errorThrown){
            alert('Error has occured:change_api_key:' + textStatus + ':' + errorThrown);
            //失敗
        }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
            //done fail後の共通処理
        });
    });
});
