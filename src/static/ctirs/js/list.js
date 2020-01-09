$(function(){
    //toastr設定
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

    //DataTable初期化
    table = $('#cti-table').DataTable({
        searching: true,
        paging: true,
        info: false,
        bProcessing: true,
        bServerSide : true,
        sAjaxSource : '/list/ajax/get_table_info',
        //デフォルトは1番目のカラム(Created At)を昇順(desc)で
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
                    {targets:0,orderable:false,className:'file-delete-td'},
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
    	//check されていない
    	if(deleteList.length == 0){
    		alert('No file is checked.');
    		return;
    	}
    	
        //確認ダイアログ
        var msg = 'Are you sure you want to delete ' + deleteList.length + ' files?';
        if(confirm(msg) == false){
            return;
        }

        //CGI送信
        var f = $('#stix-delete-form');
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'id';
        elem.value = deleteList;
        f.append(elem);
    	f.submit();
    });

    //全チェックつけアイコン
    $('#select-all-icon').on('click',function(){
    	$('.delete-checkbox').prop('checked',true);
    });
    //全チェック外しアイコン
    $('#deselect-all-icon').on('click',function(){
    	$('.delete-checkbox').prop('checked',false);
    });

    //TAXII送信ダイアログ
    var publishTaxiiDialog = $('#publish-taxii-confirm-dialog');
    publishTaxiiDialog.dialog({
        width: 400,
        height: 400,
        resizable: true,
        autoOpen: false,
        modal: true,
        buttons: {
            Cancel: function() {
                $( this ).dialog('close');
            },
            Publish: function() {
            	//publish する
            	var taxii_id = $('#hidden-taxii-id').val();
            	var stix_id = $('#hidden-stix-id').val();
            	//何も選択されていない場合はalert表示
            	if (taxii_id.length == 0){
            		alert('Choose TAXII Server to Publish.');
            	}else{
            		// publish して閉じる
                    var d = {
                            'taxii_id' : taxii_id,
                            'stix_id' : stix_id,
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
                    		//成功
                    		msg = 'publish finished. Message: ' + r['message'];
                    	}else{
                    		//失敗
                    		msg = 'publish failed. Message: ' + r['message'];
                    	}
                    }).fail(function(jqXHR,textStatus,errorThrown){
                        //失敗
                        msg = 'publish error has occured: ' + textStatus + ': ' + errorThrown;
                    }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
                        //done fail後の共通処理
                    	alert(msg);
                    });            		
                    // Dialog 閉じる
                	$( this ).dialog('close');
            	}
            },
        },
    });
    //choose-taxiiのドロップダウンメニュー
    $('#dropdown-choose-taxii li a').click(function(){
        $(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
        $(this).parents('.dropdown').find('input[id="hidden-taxii-id"]').val($(this).attr('data-value'));
    })

    //publish icon click
    $(document).on('click','.publish-share-alt-icon',function(){
    	//file_id 取得
    	var file_id = $(this).attr('file_id');
    	//hidden に STIX ID 追加
    	$('#hidden-stix-id').val(file_id);
    	publishTaxiiDialog.dialog('open');
    });

    //MISP import icon
    $(document).on('click','.misp-import-icon',function(){
    	//package_id 取得
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
        		//成功
        		toastr['success']('MISP upload success!', 'Success!');
        	}else{
        		//失敗
        		msg = 'MISP import failed. Message: ' + r['message'];
        	}
        }).fail(function(jqXHR,textStatus,errorThrown){
            //失敗
            msg = 'MISP import error has occured: ' + textStatus + ': ' + errorThrown;
        }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
            //done fail後の共通処理
        	alert(msg);
        });
    });

   // auto reload
    var reload_time = 60000;
    var reload_event;
    reload_set();
    $('#auto-reload-event').change(function() {
        if($(this).prop('checked')){
            reload_set();
        }else{
            clearTimeout(reload_event);
        }
    });
    function reload_set(){
        reload_event = setTimeout('location.reload(true)', reload_time);
    }
});
