$(function(){
    $('[data-toggle="popover"]').popover();
    function modify_taxii2_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    function set_interval_error(msg){
        $('#interval-error-msg').text(msg);
        $('#interval-info-msg').text('');
    }

    function _append_hidden_param (f, selector, var_name) {
        const elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = var_name;
        elem.value = selector.val();
        f.append(elem);
    }
        
    function _set_poll_parameter (f) {
       _append_hidden_param(f, $('#poll-limit'), 'poll_limit')
       _append_hidden_param(f, $('#poll-match-id'), 'poll_match_id')
       _append_hidden_param(f, $('#poll-match-spec-version'), 'poll_match_spec_version')
       _append_hidden_param(f, $('#poll-match-type'), 'poll_match_type')
       _append_hidden_param(f, $('#poll-match-version'), 'poll_match_version')
 
    }
    
    $('#set-interval-submit').click(function(){
    	var f = $('#configuration-taxii2-client-interval');
    	var interval = $('#interval').val();
        if (isNaN(interval) == true){
        	set_interval_error('Invalid interval value.');
            return;
        }
        var elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'interval';
        elem.value = interval;
        f.append(elem);
        _set_poll_parameter(f);
    	f.submit();
    });

    $('#create-taxii2-schedule-submit').click(function(){
    	var f = $('#configuration-taxii2-client-detail-create');
    	f.submit();
    });

    $('.configuration-taxii2-client-start-button').click(function(){
    	var f = $('#configuration-taxii2-client-job-start');
    	var action = f.attr('action');
    	var taxii2_id = $(this).attr('taxii2_client_id');
    	var job_id = $(this).attr('job_id');
        f.attr('action',action + '/' + taxii2_id + '/resume/' + job_id);
    	f.submit();
    });

    $('.configuration-taxii2-client-stop-button').click(function(){
    	var f = $('#configuration-taxii2-client-job-stop');
    	var action = f.attr('action');
    	var taxii2_id = $(this).attr('taxii2_client_id');
    	var job_id = $(this).attr('job_id');
    	f.attr('action',action + '/' + taxii2_id + '/pause/' + job_id);
    	f.submit();
    });

    $('.configuration-taxii2-client-delete-button').click(function(){
    	var f = $('#configuration-taxii2-client-job-delete');
    	var action = f.attr('action');
    	var taxii2_id = $(this).attr('taxii2_client_id');
    	var job_id = $(this).attr('job_id');
    	f.attr('action',action + '/' + taxii2_id + '/remove/' + job_id);
    	f.submit();
    });
});
