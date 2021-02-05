$(function(){
    function modify_taxii_server_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    $('#all_check_communities').click(function(){
    	$('.taxii_server_community').prop('checked',true);
    });

    $('#all_uncheck_communities').click(function(){
    	$('.taxii_server_community').prop('checked',false);
    });

    $('#modify-taxii-server-submit').click(function(){
    	var f = $('#configuration-taxii-server-modify');
    	var collection_name = $('#taxii-server-collection-name').val();
        if(collection_name.length == 0){
        	modify_taxii_server_error('Enter Collection name.');
            return;
        }
        
        var communities = [];
        $('.taxii_server_community').each(function(i,elem){
        	if(elem.checked == true){
        		communities.push(elem.id)
        	}
        });

        if(communities.length != 0){
            var elem = document.createElement('input');
            elem.type = 'hidden';
            elem.name = 'communities';
            elem.value = communities;
            f.append(elem);
        }
        
    	f.submit()
    });
});
