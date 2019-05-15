$(function(){
    function modify_system_submit(){
        var f = $('#modify-system-form');
        f.submit();
    }

    //error_msg表示
    function modify_demo_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //modifyボタンクリック
    $('#modify-system-submit').click(function(){
    	modify_system_submit();
    });

    //error_msg表示
    function create_user_error(msg){
        $('#error-msg').html(msg);
        $('#info-msg').html('');
    }

    //Rebuild Cacheボタンクリック
    $('#rebuild-cache-submit').click(function(){
    	if(confirm('Rebuild Cache?','Confirm') == false){
    		return;
    	}
        var f = $('#rebuild-cache-form');
        f.submit();
    });
});
