$(function(){
    const table = $('#versions-table').DataTable({
        searching: true,
        paging: true,
        info: true,
        order: [[0,'desc']],
        columns:[
        	{width:'50%'},	//Version
        	{width:'25%'},	//Get
        	{width:'25%'},	//Delete
        ],
        columnDefs:[
            {targets:0,orderable:true},
            {targets:1,orderable:true},
            {targets:2,orderable:true},
        ]
    })

    const view_object_dialog = $('#view-object-dialog').dialog({
        width: 800,
        height: 800,
        resizable: true,
        autoOpen: false,
        buttons: {
          Close: function() {
            $(this).dialog('close');
          },
        },
    });

    $(document).on('click','#button-back',function(){
      history.back()
    })

    $(document).on('click','.button-get',function(){
      const object_id = $('#input-object-id').val()
      const taxii_id = $('#input-taxii-id').val()
      const protocol_version = $('#input-protocol-version').val()
      const version = $(this).data('version')
      d = {
        'protocol_version' : protocol_version,
      }
      const url = '/poll/' + taxii_id + '/objects/' + object_id + '/versions/' + version + '/'

      $.ajax({
        type: 'GET',
        url: url,
        timeout: 100 * 1000,
        cache: true,
        data: d,
        dataType: 'json',
      }).done(function(r,textStatus,jqXHR){
        if(r['status'] != 'OK'){
          alert(url + ' failed:' + r['message'], 'Error!');
        }else{
          view_object_dialog
          const title = object_id + ' (' + version + ')'
          $('#object-content').val(JSON.stringify(r['data'], null, 4))
          view_object_dialog.dialog('option', 'title', title)
          view_object_dialog.dialog('open')
        }
      }).fail(function(jqXHR,textStatus,errorThrown){
        alert('Error occured: ' + url + ':' + textStatus + ':' + errorThrown);
      }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
      });        
    })

    $(document).on('click','.button-delete',function(){
      const object_id = $('#input-object-id').val()
      const taxii_id = $('#input-taxii-id').val()
      const protocol_version = $('#input-protocol-version').val()
      const version = $(this).data('version')
      const msg = 'Would you like to delete (' + object_id + '/' + version + ') object?'
      ret = confirm(msg)
      if (ret == false) {
          return
      }
      alert('delete')
    })
})