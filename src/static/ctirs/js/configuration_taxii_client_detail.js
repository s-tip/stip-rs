$(function(){
    //error_msg表示
    function modify_taxii_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //error_msg表示(interval)
    function set_interval_error(msg){
        $('#interval-error-msg').text(msg);
        $('#interval-info-msg').text('');
    }
    
    //Set Interval ボタンクリック
    $('#set-interval-submit').click(function(){
    	var f = $('#configuration-taxii-client-interval');
    	var interval = $('#interval').val();
    	//interval は数値以外は NG
        if (isNaN(interval) == true){
        	set_interval_error('Invalid interval value.');
            return;
        }
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'interval';
        elem.value = interval;
        f.append(elem);
    	f.submit();
    });

    //Create Or Modifyボタンクリック
    $('#create-taxii-schedule-submit').click(function(){
    	var f = $('#configuration-taxii-client-detail-create');
    	f.submit();
    });

    //startボタンクリック
    $('.configuration-taxii-client-start-button').click(function(){
    	var f = $('#configuration-taxii-client-job-start');
    	var action = f.attr('action');
    	var taxii_id = $(this).attr('taxii_client_id');
    	var job_id = $(this).attr('job_id');
    	f.attr('action',action + '/' + taxii_id + '/resume/' + job_id);
    	f.submit();
    });

    //stopボタンクリック
    $('.configuration-taxii-client-stop-button').click(function(){
    	var f = $('#configuration-taxii-client-job-stop');
    	var action = f.attr('action');
    	var taxii_id = $(this).attr('taxii_client_id');
    	var job_id = $(this).attr('job_id');
    	f.attr('action',action + '/' + taxii_id + '/pause/' + job_id);
    	f.submit();
    });

    //deleteボタンクリック
    $('.configuration-taxii-client-delete-button').click(function(){
    	var f = $('#configuration-taxii-client-job-delete');
    	var action = f.attr('action');
    	var taxii_id = $(this).attr('taxii_client_id');
    	var job_id = $(this).attr('job_id');
    	f.attr('action',action + '/' + taxii_id + '/remove/' + job_id);
    	f.submit();
    });
});
