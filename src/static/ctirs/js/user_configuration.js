$(function(){
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
        var f = $('#create-user-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'password';
        elem.value = $('#password-1').val();
        f.append(elem);
        elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'screen_name';
        elem.value = $('#screen-name').val();
        f.append(elem);
        f.submit();
    }

    function create_user_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

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

    $('.change-auth').change(function(){
        var d = {
                'username' : $(this).attr('username'),
                'value' : $(this).is(':checked'),
        };
        $.ajax({
            type: 'GET',
            url: '/configuration/user/ajax/change_auth',
            timeout: 100 * 1000,
            cache: true,
            data: d,
            dataType: 'json',
        }).done(function(r,textStatus,jqXHR){
            if(r['status'] != 'OK'){
                toastr['error']('change_auth failed:' + r['message'], 'Error!');
            }else{
                toastr['success']('change_auth successfully.', 'Success!');
            }
        }).fail(function(jqXHR,textStatus,errorThrown){
            toastr['error']('Error has occured:change_auth:' + textStatus + ':' + errorThrown, 'Error!');
        });
    });


    $('.change-active').change(function(){
        var d = {
                'username' : $(this).attr('username'),
                'value' : $(this).is(':checked'),
        };
        $.ajax({
            type: 'GET',
            url: '/configuration/user/ajax/change_active',
            timeout: 100 * 1000,
            cache: true,
            data: d,
            dataType: 'json',
        }).done(function(r,textStatus,jqXHR){
            if(r['status'] != 'OK'){
                toastr['error']('change_active failed:' + r['message'], 'Error!');
            }else{
                toastr['success']('change_active successfully.', 'Success!');
            }
        }).fail(function(jqXHR,textStatus,errorThrown){
            toastr['error']('Error has occured:change_active:' + textStatus + ':' + errorThrown, 'Error!');
        });
    });

    $('.change-password').click(function(){
        var user = $(this).attr('username');
        var f = $('#change-password-top-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'username';
        elem.value = $(this).attr('username');
        f.append(elem);
        f.submit();
    });

    $('#disable-2fa-dialog').dialog({
        autoOpen: false,
        modal: true,
        open: function(){
            $('.ui-dialog-titlebar').hide();
            $('.ui-dialog-titlebar-close').hide();
        },
        buttons: [
            {
                text: 'Yes',
                click: function(){
                    var dialog_this = $(this);
                    var d = {
                        'username': dialog_this.attr('username'),
                    };
                    $.ajax({
                        type: 'GET',
                        url: '/configuration/user/ajax/unset_mfa',
                        timeout: 100 * 1000,
                        cache: true,
                        data: d,
                        dataType: 'json'
                    }).done(function(r,textStatus,jqXHR){
                        if(r['status'] != 'OK'){
                            toastr['error']('unset_mfa failed:' + r['message'], 'Error!');
                        }else{
                            toastr['success']('Disable 2FA successfully.', 'Success!');
                            document.getElementById('disable-' + dialog_this.attr('username')).textContent = 'Disabled';
                        }
                    }).fail(function(jqXHR,textStatus,errorThrown){
                        toastr['error']('Error has occured:unset_mfa:' + textStatus + ':' + errorThrown, 'Error!')
                    }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
                        dialog_this.dialog('close');
                    });
                }
            },
            {
                text: 'No',
                click: function(){
                    $(this).dialog('close');
                }
            }
        ]
    });

    $('.disable-2fa').click(function(){
        $("#disable-2fa-dialog").dialog('open');
        $("#disable-2fa-dialog").attr({
            'username': $(this).attr('username'),
            'config_name': $(this).attr('config_name')
        });
    });
});
