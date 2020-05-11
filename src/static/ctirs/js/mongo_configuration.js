$(function(){
    function modify_mongo_submit(){
        f = $('#modify-mongo-form');
        f.submit();
    }

    //error_msg表示
    function modify_mongo_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //modifyボタンクリック
    $('#modify-mongo-submit').click(function(){
        $('#error-msg').text('');
        $('#info-msg').text('');
    	var host = $('#modify-mongo-host').val()
    	if(host.length == 0){
    		modify_mongo_error('Enter Host Name.');
    		return;
    	}
    	var port_str = $('#modify-mongo-port').val()
    	if(port_str.length == 0){
    		modify_mongo_error('Enter Port');
    		return;
    	}
        var port = Number(port_str);
        if (isNaN(port) == true){
        	modify_mongo_error('Invalid port');
            return;
        }
        if((port < 0) || (port > 65535)){
        	modify_mongo_error('Invalid port');
            return;
        }
    	var db = $('#modify-mongo-db').val()
    	if(db.length == 0){
    		alert('Enter DB Name');
    		return;
    	}
        modify_mongo_submit();
    });

    //error_msg表示
    function create_user_error(msg){
        $('#error-msg').html(msg);
    }
});
