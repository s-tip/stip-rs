$(function(){
    table = $('#status-table').DataTable({
        searching: true,
        paging: true,
        info: false,
        order: [[1,'desc']],
         columns:[
        	{width:'10%'},	//#
        	{width:'25%'},	//status_id
        	{width:'25%'},	//publish
        	{width:'20%'},	//client name
        	{width:'10%'},	//check
        ],
        columnDefs:[
                    {targets:0,orderable:false},
                    {targets:1,orderable:true},
                    {targets:2,orderable:true},
                    {targets:3,orderable:true},
                    {targets:4,orderable:false},
        ]
    });
 
    $('#delete-icon').on('click',function(){
    	var delete_list = [];
    	$.each($('.delete-checkbox'),function(){
    		if($(this).prop('checked') == true){
    			var delete_id = $(this).data('status-id');
    			delete_list.push(delete_id);
    		}
    	});
    	if(delete_list.length == 0){
    		alert('No status is checked.');
    		return;
    	}
        var msg = 'Would you like to delete ' + delete_list.length + ' status(es)?';
        if(confirm(msg) == false){
            return;
        }

        const f = $('#status-delete-form')
        $('#hidden-status-id').val(JSON.stringify(delete_list))
        f.submit()
    });

    $('#select-all-icon').on('click',function(){
    	$('.delete-checkbox').prop('checked',true);
    });

    $('#deselect-all-icon').on('click',function(){
    	$('.delete-checkbox').prop('checked',false);
    });

    var status_dialog = $('#status-dialog');
    status_dialog.dialog({
        width: 800,
        height: 600,
        resizable: true,
        autoOpen: false,
        modal: true,
        buttons: {
            Close: function() {
                $( this ).dialog('close');
            },
        }
    })

    $(document).on('click','.button-check',function(){
      const status_id = $(this).data('status-id')
      const d = {
        'taxii_id': $(this).data('taxii-id'),
        'status_id': status_id,
      }
      $.ajax({
        type: 'GET',
        url: '/status/ajax/check/',
        timeout: 100 * 1000,
        cache: true,
        data: d,
        dataType: 'json',
      }).done(function(r,textStatus,jqXHR){
      	if(r['status'] == 'OK'){
          const title = 'Status ID: ' + status_id
          $('#status-result').val(JSON.stringify(r['data'], null, 4))
          status_dialog.dialog('option', 'title', title)
          status_dialog.dialog('open')
      	}else{
      	  msg = 'Status check failed. Message: ' + r['message'];
          alert(msg)
      	}
      }).fail(function(jqXHR,textStatus,errorThrown){
        msg = 'Status check error has occured: ' + textStatus + ': ' + errorThrown;
        alert(msg)
      }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
      });            	
    })
});
