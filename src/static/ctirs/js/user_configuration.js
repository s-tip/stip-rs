$(function(){
    //toastr設定
    toastr.options = {
        'closeButton': false,
        'debug': false,
        'newestOnTop': true,
        'progressBar': false,
        'positionClass': 'toast-top-right',
        'preventDuplicates': false,
        'onclick': null,
        'showDuration': '500',
        'hideDuration': '700',
        'timeOut': '1000',
        'extendedTimeOut': '1000',
        'showEasing': 'swing',
        'hideEasing': 'linear',
        'showMethod': 'fadeIn',
        'hideMethod': 'fadeOut'
    };

    function create_user_submit(){
        //passwordフィールドを作成
        var f = $('#create-user-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'password';
        elem.value = $('#password-1').val();
        f.append(elem);
        //screee_nameフィールドを作成
        elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'screen_name';
        elem.value = $('#screen-name').val();
        f.append(elem);
        f.submit();
    }

    //error_msg表示
    function create_user_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //loginボタンクリック
    $('#create-user-submit').click(function(){
        var username = $('#username').val();
        if(username.length == 0){
            create_user_error('Enter Username');
            return;
        }
        var pwd_1 = $('#password-1').val();
        if(pwd_1.length == 0){
            create_user_error('Enter Password');
            return;
        }
        var pwd_2 = $('#password-2').val();
        if(pwd_2.length == 0){
            create_user_error('Enter Password(again)');
            return;
        }
        if(pwd_1 != pwd_2){
            create_user_error('Enter Same Password.');
            return;
        }
        create_user_submit();
    });

    //User Configurationのチェックボックスon/off
    $('.change-auth').change(function(){
        var d = {
                'username' : $(this).attr('username'),
                'key' : $(this).attr('config_name'),
                'value' : $(this).is(':checked'),
        };
        //ajax呼び出し
        $.ajax({
            type: 'GET',
            url: '/configuration/user/ajax/change_auth',
            timeout: 100 * 1000,
            cache: true,
            data: d,
            dataType: 'json',
        }).done(function(r,textStatus,jqXHR){
            if(r['status'] != 'OK'){
                alert('change_auth failed:' + r['message'], 'Error!');
            }else{
                toastr['success']('change_auth successfully.', 'Success!');
            }
        }).fail(function(jqXHR,textStatus,errorThrown){
            alert('Error has occured:change_auth:' + textStatus + ':' + errorThrown);
            //失敗
        }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
            //done fail後の共通処理
        });
    });
});
