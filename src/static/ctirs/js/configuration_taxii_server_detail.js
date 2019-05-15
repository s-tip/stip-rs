$(function(){
    //error_msg表示
    function modify_taxii_server_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //All Check リンククリック
    $('#all_check_information_sources').click(function(){
    	$('.taxii_server_information_source').prop('checked',true);
    });

    //All Uncheck リンククリック
    $('#all_uncheck_information_sources').click(function(){
    	$('.taxii_server_information_source').prop('checked',false);
    });

    //Modify ボタンクリック
    $('#modify-taxii-server-submit').click(function(){
    	var f = $('#configuration-taxii-server-modify');
    	var collection_name = $('#taxii-server-collection-name').val();
        if(collection_name.length == 0){
        	modify_taxii_server_error('Enter Collection name.');
            return;
        }
        
        //check が入っているリストを取得する
        var information_sources = [];
        $('.taxii_server_information_source').each(function(i,elem){
        	if(elem.checked == true){
        		console.log(elem.value)
        		information_sources.push(elem.id)
        	}
        });
        console.log(information_sources)

        //IDを要素にする
        if(information_sources.length != 0){
            var elem = document.createElement('input');
            elem.type = 'hidden';
            elem.name = 'information_sources';
            elem.value = information_sources;
            f.append(elem);
        }
        
    	f.submit()
    });
});
