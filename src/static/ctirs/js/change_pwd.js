$(function(){

    function change_password_submit(){
        //passwordフィールドを作成
        var f = $('#change-password-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'password';
        elem.value = $('#password-1').val();
        f.append(elem);
        //usernameフィールドを作成
        elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'username';
        elem.value = $('#change-pwd-username').val();
        f.append(elem);
        f.submit();
    }

    //error_msg表示
    function create_user_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //change-password button クリック
    $('#change-pwd-submit').click(function(){
        var username = $('#change-pwd-username').val();
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
        change_password_submit();
    });

    //change-password button クリック
    $('#back-button-submit').click(function(){
        window.location.href = '/configuration/user/';
    });
});
