$(function(){
    const table = $('#versions-table').DataTable({
        searching: true,
        paging: true,
        info: true,
        order: [[0,'desc']],
        columns:[
        	{width:'10%'},	//version
        ],
        columnDefs:[
            {targets:0,orderable:true},
        ]
    })

    $(document).on('click','#versions-back',function(){
      history.back()
    })
})