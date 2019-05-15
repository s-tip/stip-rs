$(function(){
    function create_community_submit(){
        var f = $('#create-community-form');
        f.submit();
    }
    //error_msg表示
    function create_community_error(msg){
        $('#error-msg').text(msg);
        $('#info-msg').text('');
    }

    //submitボタンクリック
    $('#create-community-submit').click(function(){
        var name = $('#name').val();
        if(name.length == 0){
            create_community_error('Enter name');
            return;
        }
        create_community_submit();
    });
});
