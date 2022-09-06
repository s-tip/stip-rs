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
          Save: function() {
            _save()
          },
          Close: function() {
            $(this).dialog('close');
          },
        },
    });

    $(document).on('click','#button-back',function(){
      history.back()
    })

    function _get_version_url (taxii_id, object_id, version) {
      return'/poll/' + taxii_id + '/objects/' + object_id + '/versions/' + version + '/'
    }

    function getCookie(name){
        var cookieValue = null
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';')
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i])
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                    break
                }
            }
        }
        return cookieValue;
    }

    function _save() {
      const csrf_token = $('input[name="csrfmiddlewaretoken"]').val()
      d = {
        'content': $('#object-content').val(),
        'taxii_id': $('#input-taxii-id').val(),
        'csrf': csrf_token
      }
      url = '/poll/register_object/'
      $.ajax({
        type: 'POST',
        url: url,
        timeout: 100 * 1000,
        cache: true,
        data: d,
        dataType: 'json',
        beforeSend: function (xhr, settings) {
          xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'))
        }
      }).done(function(r,textStatus,jqXHR){
        if(r['status'] != 'OK'){
          alert('register_object failed:' + r['message'], 'Error!');
        }else{
          alert('Success!!')
        }
      }).fail(function(jqXHR,textStatus,errorThrown){
        alert('Error occured: register_object: ' + textStatus + ': ' + errorThrown);
      }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
      });        
    }

    $(document).on('click','.button-get',function(){
      const object_id = $('#input-object-id').val()
      const taxii_id = $('#input-taxii-id').val()
      const protocol_version = $('#input-protocol-version').val()
      const version = $(this).data('version')
      const d = {
        'protocol_version' : protocol_version,
        'method' : 'get'
      }
      const url = _get_version_url(taxii_id ,object_id, version)

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
      const d = {
        'protocol_version' : protocol_version,
        'method' : 'delete'
      }
      const url = _get_version_url(taxii_id ,object_id, version)

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
          alert('Delete Success!!')
        }
      }).fail(function(jqXHR,textStatus,errorThrown){
        alert('Error occured: ' + url + ':' + textStatus + ':' + errorThrown);
      }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
      });        
    })
})