$(function(){
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

    var delete_visible = false;
    if($('input[name="delete-visible"]').val() == "True"){         
        delete_visible　= true
    }

    table = $('#cti-table').DataTable({
        searching: true,
        paging: true,
        info: false,
        bProcessing: true,
        bServerSide : true,
        sAjaxSource : '/list/ajax/get_table_info',
        order: [[1,'desc']],
        columns:[
        	{width:'4%'},	//#
        	{width:'7%'},	//Crate At
        	{width:'20%'},	//Package Name
        	{width:'20%'},	//Package ID
        	{width:'5%'},	//STIX Version
        	{width:'9%'},	//Community
        	{width:'5%'},	//Via
        	{width:'10%'},	//Uploader
        	{width:'10%'},	//Download
        	{width:'5%'},	//Publish
        	{width:'5%'},	//MISP
        ],
        columnDefs:[
                    {targets:0,orderable:false,className:'file-delete-td',visible:delete_visible},
                    {targets:1,orderable:true},
                    {targets:2,orderable:true},
                    {targets:3,orderable:true},
                    {targets:4,orderable:true},
                    {targets:5,orderable:false},
                    {targets:6,orderable:false},
                    {targets:7,orderable:false},
                    {targets:8,orderable:false},
                    {targets:9,orderable:false},]
    });

    $('#delete-icon').on('click',function(){
    	var deleteList = [];
    	$.each($('.delete-checkbox'),function(){
    		if($(this).prop('checked') == true){
    			var delete_id = $(this).attr('file_id');
    			deleteList.push(delete_id);
    		}
    	});
    	if(deleteList.length == 0){
    		alert('No file is checked.');
    		return;
    	}
        var msg = 'Are you sure you want to delete ' + deleteList.length + ' files?';
        if(confirm(msg) == false){
            return;
        }
        var f = $('#stix-delete-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'id';
        elem.value = deleteList;
        f.append(elem);
    	f.submit();
    });

    $('#select-all-icon').on('click',function(){
    	$('.delete-checkbox').prop('checked',true);
    });

    $('#deselect-all-icon').on('click',function(){
    	$('.delete-checkbox').prop('checked',false);
    });

    var resultPublishTaxiiDialog = $('#publish-taxii-result-dialog');
    resultPublishTaxiiDialog.dialog({
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

    var publishTaxiiDialog = $('#publish-taxii-confirm-dialog');
    publishTaxiiDialog.dialog({
        width: 800,
        height: 600,
        resizable: true,
        autoOpen: false,
        modal: true,
        buttons: {
            Cancel: function() {
                $( this ).dialog('close');
            },
            Publish: function() {
            	var taxii_id = $('#hidden-taxii-id').val();
            	var stix_id = $('#hidden-stix-id').val();
                var protocol_version = $('#hidden-protocol-version').val();
            	if (taxii_id.length == 0){
            		alert('Choose TAXII Server to Publish.');
            	}else{
                    var d = {
                            'taxii_id' : taxii_id,
                            'stix_id' : stix_id,
                            'protocol_version' : protocol_version,
                    };
                    var msg = '';
                    $.ajax({
                        type: 'get',
                        url: '/list/ajax/publish',
                        timeout: 100 * 1000,
                        cache: true,
                        data: d,
                        dataType: 'json',
                    }).done(function(r,textStatus,jqXHR){
                    	if(r['status'] == 'OK'){
                            msg = r['message']
                    	}else{
                    		msg = 'Publish failed. Message: ' + r['message'];
                    	}
                    }).fail(function(jqXHR,textStatus,errorThrown){
                        msg = 'publish error has occured: ' + textStatus + ': ' + errorThrown;
                    }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
                        $('#push-result').val(msg)
                        resultPublishTaxiiDialog.dialog('open');
                    });            		
                	$( this ).dialog('close');
            	}
            },
        },
    });

    $('#dropdown-choose-taxii li a').click(function(){
        $(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
        $('#hidden-taxii-id').val($(this).data('taxii-id'));
        $('#hidden-protocol-version').val($(this).data('protocol-version'));
        $('#taxii-address-confirm').text($(this).data('address'));
        $('#taxii-collection-confirm').text($(this).data('collection'));
    })

    $(document).on('click','.publish-share-alt-icon',function(){
    	var file_id = $(this).data('file-id');
    	var package_id = $(this).data('package-id');
    	var package_name = $(this).data('package-name');
        $('#hidden-stix-id').val(file_id);
        $('#stix-package-name-confirm').text(package_name);
        $('#stix-package-id-confirm').text(package_id);
        toggle_display_taxii_setting();
    	publishTaxiiDialog.dialog('open');
    });

    $(document).on('change','.taxii-version-radio-button',function(){
       toggle_display_taxii_setting();
    });

    function toggle_display_taxii_setting(){
        if($('#taxii-v1-button').prop('checked')){
            $('#taxii-v1-configuration-div').show();
            $('#taxii-v2-configuration-div').hide();
        }else{
            $('#taxii-v1-configuration-div').hide();
            $('#taxii-v2-configuration-div').show();
        }
    };

    $(document).on('click','.misp-import-icon',function(){
    	var package_id = $(this).attr('package_id');
    	var d = {
    			'package_id' : package_id
    	};
        $.ajax({
            type: 'post',
            url: '/list/ajax/misp_import',
            timeout: 100 * 1000,
            cache: true,
            data: d,
            async: false,
            dataType: 'json',
        }).done(function(r,textStatus,jqXHR){
        	if(r['status'] == 'OK'){
        		toastr['success']('MISP upload success!', 'Success!');
        	}else{
        		msg = 'MISP import failed. Message: ' + r['message'];
        	}
        }).fail(function(jqXHR,textStatus,errorThrown){
            msg = 'MISP import error has occured: ' + textStatus + ': ' + errorThrown;
        }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
        	alert(msg);
        });
    });

    var reload_time = 60000;
    var reload_event;
    set_reload();
    $('#auto-reload-event').change(function() {
        if($(this).prop('checked')){
            set_reload();
        }else{
            clearTimeout(reload_event);
        }
    });
    function set_reload(){
        reload_event = setTimeout('location.reload(true)', reload_time);
    }
});
