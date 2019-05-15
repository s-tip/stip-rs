$(function(){
    var jsonData = $.ajax({
        type: 'GET',
        url: '/dashboard/ajax/get_stix_counts',
        data: {},
        dataType: 'json',
    }).done(function(results,textStatus,jqXHR){
        if(results['status'] != 'OK'){
            alert('Error has occured:get_stix_counts:');
            return;
        }

        var data = results['data'];
        var pie_labels = data['pie_labels'];
        var pie_datasets = data['pie_datasets'];
        var last_cti_pie_ctx = document.getElementById('canvas-last-cti-pie').getContext('2d');
        var last_cti_pie_ctx_2= document.getElementById('canvas-last-cti-pie-2').getContext('2d');
        var backgroundColor = [
                          'rgba(255, 99, 132, 0.3)',
                          'rgba(54, 162, 235, 0.3)',
                          'rgba(255, 206, 86, 0.3)',
                          'rgba(75, 192, 192, 0.3)',
                          'rgba(153, 102, 255, 0.3)',
                          'rgba(255, 159, 64, 0.3)',
                          'rgba(255, 99, 132, 0.3)',
                          ];
        var hoverBackgroundColor = [
                          'rgba(255, 99, 132, 0.5)',
                          'rgba(54, 162, 235, 0.5)',
                          'rgba(255, 206, 86, 0.5)',
                          'rgba(75, 192, 192, 0.5)',
                          'rgba(153, 102, 255, 0.5)',
                          'rgba(255, 159, 64, 0.5)',
                          'rgba(255, 99, 132, 0.5)',
                          ];


        var last_cti_pie_chart = new Chart(last_cti_pie_ctx, {
            type: 'pie',
            data:{
                labels :pie_labels,
                datasets: [
                    {
                        backgroundColor: backgroundColor,
                        hoverBackgroundColor: hoverBackgroundColor,
                        data: pie_datasets,

                    }]
            },
            options: {
                responsive: true,
            }
        });
        var last_cti_pie_chart_2 = new Chart(last_cti_pie_ctx_2, {
            type: 'pie',
            data:{
                labels :pie_labels,
                datasets: [
                    {
                        backgroundColor: backgroundColor,
                        hoverBackgroundColor: hoverBackgroundColor,
                        data: pie_datasets,

                    }]
            },
            options: {
                responsive: true,
            }
        });
    }).fail(function(jqXHR,textStatus,errorThrown){
        alert('Error has occured:get_stix_counts:' + textStatus + ':' + errorThrown);
        //失敗
    }).always(function(data_or_jqXHR,textStatus,jqHXR_or_errorThrown){
        //done fail後の共通処理
    });
});