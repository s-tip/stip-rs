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
        const f = $('#poll-detail')
        const protocol_version = $(this).data('protocol-version');
        const elem = document.createElement('input');
        elem.type = 'hidden';
        elem.name = 'protocol_version';
        elem.value = protocol_version;
        f.append(elem);
        f.submit();
    })
})