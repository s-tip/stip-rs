$(function(){
    const table = $('#manifest-table').DataTable({
        searching: true,
        paging: true,
        info: true,
        order: [[0,'desc']],
        columns:[
        	{width:'25%'},	//version
        	{width:'25%'},	//date_added
        	{width:'30%'},	//id
        	{width:'20%'},	//media_type
        ],
        columnDefs:[
            {targets:0,orderable:true},
            {targets:1,orderable:true},
            {targets:2,orderable:true},
            {targets:3,orderable:true},
        ]
    })

    $(document).on('click','#manifest-back',function(){
      history.back()
    })
})