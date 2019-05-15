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

    function modify_community_submit(){
        var f = $('#modify-community-form');
        f.submit();
    }

    //error_msg表示
    function modify_community_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //modifyボタンクリック
    $('#modify-community-detail-submit').click(function(){
        var name = $('#modify-community-name').val();
        if(name.length == 0){
        	modify_community_error('Enter name');
            return;
        }
        modify_community_submit();
    });

    //deleteボタンクリック
    $('.delete-community-button').click(function(){
        var coummunity_id = $(this).attr('community_id');
        var msg = 'Delete ' + name + '?';
        if(confirm(msg) == false){
            return
        }
        var f = $('#delete-community-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'community_id';
        elem.value = coummunity_id;
        f.append(elem);
        f.submit();
    });
    
    //webhook-addボタンクリック
    $('.add-webhook-button').click(function(){
        var f = $('#add-webhook-form');
        var url = $('#webhook-text').val();
        if(url.length == 0){
        	modify_community_error('Enter URL');
            return;
        }
        f.submit();
    });
    
    //webhook deleteボタンクリック
    $('.delete-webhook-button').click(function(){
        var url = $(this).attr('webhook_url');
        var msg = 'Delete ' + url + '?';
        if(confirm(msg) == false){
            return
        }
        var webhook_id = $(this).attr('webhook_id');
        var community_id = $('#community-id').val();
        var f = $('#delete-webhook-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'webhook_id';
        elem.value = webhook_id;
        f.append(elem);
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'community_id';
        elem.value = community_id;
        f.append(elem);
        f.submit();
    });

    //webhook testボタンクリック
    $('.test-webhook-button').click(function(){
        d = {
                'webhook_id' : $(this).attr('webhook_id'),
        };
        //ajax呼び出し
        $.ajax({
            type: 'GET',
            url: '/configuration/community/ajax/test_webhook',
            timeout: 100 * 1000,
            cache: true,
            data: d,
            dataType: 'json',
        }).done(function(r,textStatus,jqXHR){
            if(r['status'] != 'OK'){
                alert('test_webhook failed:' + r['message'], 'Error!');
            }else{
                toastr['success']('test_webhook successfully.', 'Success!');
            }
        }).fail(function(jqXHR,textStatus,errorThrown){
            alert('Error has occured:test_webhook:' + textStatus + ':' + errorThrown);
            //失敗
        }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
            //done fail後の共通処理
        });
    });
});
