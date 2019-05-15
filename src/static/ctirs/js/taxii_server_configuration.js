$(function(){
    //reboot-taxii-serverボタンクリック
    $('#reboot-taxii-server-submit').click(function(){
    	var f = $('#reboot-taxii-server-form')
        f.submit();
    });

    //create-taxii-serverボタンクリック
    $('#create-taxii-server-submit').click(function(){
    	var f = $('#create-taxii-server-form');
        var setting_name = $('#create-setting-name').val();
        if(setting_name.length == 0){
        	create_taxii_error('Enter setting name.');
            return;
        }
        var collection_name = $('#create-collection-name').val();
        if(collection_name.length == 0){
        	create_taxii_error('Enter collection name.');
            return;
        }
        f.submit();
    });

    //delete-taxii-server-button ボタンクリック
    $('.delete-taxii-server-button').click(function(){
    	var f = $('#delete-taxii-server-form');
        var setting_name = $(this).attr('setting_name');
        var id = $(this).attr('id');
        
        //確認メッセージ
        var msg = 'Delete \"' + setting_name + '\" setting?'
        if(confirm (msg) == false){
        	return;
        }
        
        //IDを要素にする
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'id';
        elem.value = id;
        f.append(elem);
        f.submit();
    });

    //detail-taxii-server-button ボタンクリック
    $('.detail-taxii-server-button').click(function(){
    	var id = $(this).attr('id');
    	var f = $('#detail-taxii-server-form');
    	var action = f.attr('action');
    	//詳細画面に遷移
    	action += id
    	window.location.replace(action)
    });

    //error_msg表示
    function create_taxii_error(msg){
        $('#create-error-msg').html(msg);
        $('#info-error-msg').html('');
    };
});
