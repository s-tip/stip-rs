$(function(){
    function taxii2_submit(){
        var f = $('#create-taxii2-client-form');
        f.submit();
    }

    function modify_taxii2_error(msg){
        $('#info-msg').html('');
        $('#error-msg').html(msg);
    }

    if($('#create-ca').prop('checked') ==  false){
        $('#certificate-file-div').hide();
    }

    $("#dropdown-menu-community-name li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-community-id').val($(this).attr("data-value"));
    });

    $("#dropdown-protocol-version li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-protocol-version').val($(this).attr("data-value"));
    });

    $("#dropdown-menu-uploader li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-uploader-id').val($(this).attr("data-value"));
    });

    $(document).on('click', '#dropdown-menu-api-root li a', function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-api-root').val($(this).attr("data-value"));
      _get_collections($(this).attr("data-value"))
    });

    $(document).on('click', '#dropdown-menu-collection li a', function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#create-collection').val($(this).attr("data-value"));
    });

    function _is_valid_name() {
      const val = $('#create-display-name').val()
      if(val.length == 0){
        modify_taxii2_error('Enter Display Name')
        return false
      }
      return true
    }

    function _is_valid_protocol_version() {
      const val = $('#create-protocol-version').val()
      if(val.length == 0){
        modify_taxii2_error('Choose Protocol Version.')
        return false
      }
      return true
    }

    function _is_valid_domain() {
      const val = $('#create-domain').val()
      if(val.length == 0){
        modify_taxii2_error('Enter TAXII Server Domain')
        return false
      }
      return true
    }

    function _is_valid_port() {
      const val = $('#create-port').val()
      if(val.length == 0){
        modify_taxii2_error('Enter TAXII Server Port')
        return false
      }
      if(isNaN(val)){
        modify_taxii2_error('Enter Integer (Server Port)')
        return false
      }
      const port = parseInt(val, 10)
      if((port < 0) || (port > 65535)){
        modify_taxii2_error('Invalid TAXII Server Port')
        return false
      }
      return true
    }

    function _is_valid_ca() {
      if($('#create-ca').prop('checked') == true){
        if($('#create-certificate').val().length == 0){
          modify_taxii2_error('Enter Certificate')
          return false
        }
        if($('#create-private-key').val().length == 0){
          modify_taxii2_error('Enter Private Key')
          return false
          }
        } else{
          const login_id = $('#create-login-id').val()
          if(login_id.length == 0){
            modify_taxii2_error('Enter Login ID')
            return false
          }
          $('#create-certificate').val('')
          $('#create-private-key').val('')
        }
        return true 
    }

    function _is_valid_api_root() {
      const val = $('#create-api-root').val()
      if(val.length == 0){
        modify_taxii2_error('Enter API Root')
        return false
      }
      return true
    }

    function _is_valid_collection() {
      const val = $('#create-collection').val()
      if(val.length == 0){
        modify_taxii2_error('Enter Collection')
        return false
      }
      return true
    }

    function _is_valid_community() {
      const val = $('#create-community-id').val()
      if(val.length == 0){
        modify_taxii2_error('Choose Community.')
        return false
      }
      return true
    }

    function _is_valid_uploader() {
      var val = $('#create-uploader-id').val()
      if(val.length == 0){
        modify_taxii2_error('Choose Uploader.')
        return false
      }
      return true
    }

    function _check_taxii21_response (resp) {
      if(resp.hasOwnProperty('http_status')) {
        alert(JSON.stringify(resp, null, 2))
        return false
      }
      return true
    }

    function _create_api_root_listbox (resp) {
      const ul = $('#dropdown-menu-api-root')
      ul.empty()
      $.each(
        resp['api_roots'],
        function(index, api_root){
          var data = null
          if (api_root.startsWith('https://')){
            const parser = new URL(api_root)
            data = parser.pathname
          } else {
            data = api_root
          }
          if (data.slice(-1) != '/') {
            data += '/'
          }
          const li = $('<li>')
          const a = $('<a>', {
            'data-value': data,
          })
          a.text(data)
          li.append(a)
          ul.append(li)
      })
      $('#create-api-root-dropdown-button').prop('disabled', false)
      return
    }

    function _create_collections_listbox (resp) {
      const ul = $('#dropdown-menu-collection')
      ul.empty()
      $.each(
        resp['collections'],
        function(index, collection){
          const li = $('<li>')
          const a = $('<a>', {
            'data-value': collection.id,
          })
          var text = collection.id
          text += ' ('
          text += collection.title
          text += '), can_read: '
          text += collection.can_read
          text += ', can_write: '
          text += collection.can_write
          a.text(text)
          li.append(a)
          ul.append(li)
      })
      $('#create-collection-dropdown-button').prop('disabled', false)
      return
    }

    $('#create-taxii2-client-submit').click(function(){
      if (_is_valid_name() == false) {
        return
      }
      if (_is_valid_protocol_version() == false) {
        return
      }
      if (_is_valid_domain() == false) {
        return
      }
      if (_is_valid_port() == false) {
        return
      }
      if (_is_valid_ca() == false) {
        return
      }
      if (_is_valid_api_root() == false) {
        return
      }
      if (_is_valid_collection() == false) {
        return
      }
      if (_is_valid_community() == false) {
        return
      }
      if (_is_valid_uploader() == false) {
        return
      }
      taxii2_submit()
    })

    $('#button-get-discovery').click(function(){
      if (_is_valid_name() == false) {
        return
      }
      if (_is_valid_protocol_version() == false) {
        return
      }
      if (_is_valid_domain() == false) {
        return
      }
      if (_is_valid_port() == false) {
        return
      }
      if (_is_valid_ca() == false) {
         return
      }
      d = {
        'display_name' : $('#create-display-name').val(),
        'protocol_version' : $('#create-protocol-version').val(),
        'domain' : $('#create-domain').val(),
        'port' : $('#create-port').val(),
        'ca' : $('#create-ca').val(),
        'certificate' : $('#create-certificate').val(),
        'private_key' : $('#create-private-key').val(),
        'login_id' : $('#create-login-id').val(),
        'login_password' : $('#create-login-password').val(),
      }
      $.ajax({
        type: 'GET',
        url: '/configuration/taxii2_client/ajax/get_discovery',
        timeout: 100 * 1000,
        cache: true,
        data: d,
        dataType: 'json',
      }).done(function(r,textStatus,jqXHR){
        if(r['status'] != 'OK'){
          alert('get_discovery failed:' + r['message'], 'Error!');
        }else{
          resp = r['data']
          if (_check_taxii21_response(resp) == false) {
            return
          }
          _create_api_root_listbox(resp)
        }
      }).fail(function(jqXHR,textStatus,errorThrown){
        alert('Error occured: get_dicovery:' + textStatus + ':' + errorThrown);
      }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
      });        
    })

    var col_info_dialog = $('#collection-information-dialog')
    col_info_dialog.dialog({
        width: 800,
        height: 800,
        resizable: true,
        autoOpen: false,
        modal: true,
        buttons: {
            Close: function() {
                $( this ).dialog('close');
            },
        },
    });
    function _open_col_confirm_dialog(resp) {
      if ('http_status' in resp){
        alert(JSON.stringify(resp,null,2))
        return
      }
      TAB = 2
      $('#col-info-id').val(resp['id'])
      $('#col-info-title').val(resp['title'])
      $('#col-info-alias').val(JSON.stringify(resp['alias'],null, TAB))
      if(resp['can_read']){
        $('#col-info-can-read').prop('checked', true)
      } else {
        $('#col-info-can-read').prop('checked', false)
      }
      if(resp['can_write']){
        $('#col-info-can-write').prop('checked', true)
      } else {
        $('#col-info-can-write').prop('checked', false)
      }
      $('#col-info-description').val(JSON.stringify(resp['description'],null, TAB))
      $('#col-info-media-type').val(JSON.stringify(resp['media_types'],null, TAB))
      var title = 'Collection Information (id: ' + resp['id'] + ')'
      col_info_dialog.dialog('option', 'title', title)
      col_info_dialog.dialog('open')
    }

    $('#button-get-collection').click(function(){
      if (_is_valid_name() == false) {
        return
      }
      if (_is_valid_protocol_version() == false) {
        return
      }
      if (_is_valid_domain() == false) {
        return
      }
      if (_is_valid_port() == false) {
        return
      }
      if (_is_valid_ca() == false) {
         return
      }
      if (_is_valid_api_root() == false) {
        return
      }
      if (_is_valid_collection() == false) {
        return
      }
      d = {
        'display_name' : $('#create-display-name').val(),
        'protocol_version' : $('#create-protocol-version').val(),
        'domain' : $('#create-domain').val(),
        'port' : $('#create-port').val(),
        'ca' : $('#create-ca').val(),
        'certificate' : $('#create-certificate').val(),
        'private_key' : $('#create-private-key').val(),
        'login_id' : $('#create-login-id').val(),
        'login_password' : $('#create-login-password').val(),
        'api_root' : $('#create-api-root').val(),
        'collection' : $('#create-collection').val(),
      }
      $.ajax({
        type: 'GET',
        url: '/configuration/taxii2_client/ajax/get_collection',
        timeout: 100 * 1000,
        cache: true,
        data: d,
        dataType: 'json',
      }).done(function(r,textStatus,jqXHR){
        if(r['status'] != 'OK'){
          alert('get_collection failed:' + r['message'], 'Error!');
        }else{
          resp = r['data']
          _open_col_confirm_dialog(resp)
        }
      }).fail(function(jqXHR,textStatus,errorThrown){
        alert('Error occured: get_collection:' + textStatus + ':' + errorThrown);
      }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
      });        
    })

    function _get_collections(api_root) {
      if (_is_valid_name() == false) {
        return
      }
      if (_is_valid_protocol_version() == false) {
        return
      }
      if (_is_valid_domain() == false) {
        return
      }
      if (_is_valid_port() == false) {
        return
      }
      if (_is_valid_ca() == false) {
         return
      }
      d = {
        'display_name' : $('#create-display-name').val(),
        'protocol_version' : $('#create-protocol-version').val(),
        'domain' : $('#create-domain').val(),
        'port' : $('#create-port').val(),
        'ca' : $('#create-ca').val(),
        'certificate' : $('#create-certificate').val(),
        'private_key' : $('#create-private-key').val(),
        'login_id' : $('#create-login-id').val(),
        'login_password' : $('#create-login-password').val(),
        'api_root' : api_root,
      }
      $.ajax({
        type: 'GET',
        url: '/configuration/taxii2_client/ajax/get_collections',
        timeout: 100 * 1000,
        cache: true,
        data: d,
        dataType: 'json',
      }).done(function(r,textStatus,jqXHR){
        if(r['status'] != 'OK'){
          alert('get_collections failed:' + r['message'], 'Error!');
        }else{
          resp = r['data']
          if (_check_taxii21_response(resp) == false) {
            return
          }
          _create_collections_listbox(resp)
        }
      }).fail(function(jqXHR,textStatus,errorThrown){
        alert('Error occured: get_collections:' + textStatus + ':' + errorThrown);
      }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
      });
    }

    $('.delete-taxii2-client-button').click(function(){
        var display_name = $(this).attr('display_name');
        var msg = 'Delete ' + display_name + '?';
        if(confirm(msg) == false){
            return
        }
        var f = $('#delete-taxii2-client-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'display_name';
        elem.value = display_name;
        f.append(elem);
        f.submit();
    });

    $('.modify-taxii2-client-button').click(function(){
        $('#info-msg').html('');
        $('#error-msg').html('');
        var tr = $(this).closest('.configure-tr');
        $('#create-display-name').val(tr.find('.display-name').text());
        $('#create-domain').val(tr.find('.domain').text());
        $('#create-port').val(tr.find('.port').text());
        const api_root = tr.find('.api-root').text()
        const collection = tr.find('.collection').text()
        $('#create-api-root-dropdown-button').text(api_root);
        $('#create-collection-dropdown-button').text(collection);
      	$('#create-api-root').val(api_root);
      	$('#create-collection').val(collection);
        $('#create-login-id').val(tr.find('.login-id').text());
        $('#create-login-password').val('');
        var ca = tr.find('.ca').prop("checked");
        var d = $('#certificate-file-div');
        $('#create-ca').prop("checked",ca);
        if(ca == true){
            d.show();
        }
        else{
            d.hide();
        }
        $('#create-community-id').val(tr.find('.community-id').val());
        $('#create-community-dropdown-button').text(tr.find('.community').text());
        $('#create-protocol-version-dropdown-button').text(tr.find('.protocol-version').text());
        $('#create-protocol-version').val(tr.find('.protocol-version').text());
        var push_flag = tr.find('.push').prop("checked");
        $('#create-push').prop("checked",push_flag);
        $('#create-uploader-id').val(tr.find('.uploader-id').val());
        $('#create-uploader-dropdown-button').text(tr.find('.uploader').text());
        $('#create-can-read').prop("checked",tr.find('.can-read').prop("checked"));
        $('#create-can-write').prop("checked",tr.find('.can-write').prop("checked"))
    });
    
    $('.detail-taxii2-client-button').click(function(){
    	var id = $(this).attr('taxii2_client_id');
    	var f = $('#configuration-taxii2-client-detail');
    	var action = f.attr('action');
    	f.attr('action',action + id);
    	f.submit();
    });

    $('#create-ca').click(function(){
        $('#certificate-file-div').toggle();
        if($(this).prop('checked') ==  true){
            $('#create-ssl').prop('checked',true);
        }
    }); 
});
