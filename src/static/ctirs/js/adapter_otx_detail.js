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
    //Create Or Modifyボタンクリック
    $('#create-otx-schedule-submit').click(function(){
    	var f = $('#adapter-otx-detail-create');
    	f.submit();
    });

    //startボタンクリック
    $('.adapter-otx-start-button').click(function(){
    	var f = $('#adapter-otx-job-start');
    	var action = f.attr('action');
    	var job_id = $(this).attr('job_id');
    	f.attr('action',action + job_id);
    	f.submit();
    });

    //stopボタンクリック
    $('.adapter-otx-stop-button').click(function(){
    	var f = $('#adapter-otx-job-stop');
    	var action = f.attr('action');
    	var job_id = $(this).attr('job_id');
    	f.attr('action',action + job_id);
    	f.submit();
    });

    //deleteボタンクリック
    $('.adapter-otx-delete-button').click(function(){
    	var f = $('#adapter-otx-job-delete');
    	var action = f.attr('action');
    	var job_id = $(this).attr('job_id');
    	f.attr('action',action + job_id);
    	f.submit();
    });
    
    //Set Interval ボタンクリック
    $('#set-interval-submit').click(function(){
    	var f = $('#adapter-otx-job-interval');
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
});
