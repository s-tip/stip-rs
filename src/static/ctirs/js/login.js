$(function(){
    function login_submit(){
        $('#login').submit();
    }

    //loginボタンクリック
    $('#login-submit').click(function(){
        login_submit();
    });

    //enter押下でlogin_submit
    var elements = 'input[type=text],input[type=password]';
    $(elements).keypress(function(e) {
        var c = e.which ? e.which : e.keyCode;
        if (c == 13) {
            login_submit();
        }
    });
});
