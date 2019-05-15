$(function(){
    //community-nameのリストボックスをクリックした時
    $("#dropdown-menu-community-name li a").click(function(){
    	$(this).parents('.dropdown').find('.dropdown-toggle').html($(this).text() + ' <span class="caret"></span>');
    	$(this).parents('.dropdown').find('#community-id').val($(this).attr("data-value"));
    });

    //stix-file-button押下時
    $('#stix-file-button').click(function(){
        $('#stix-file-file').click();
    });

    //STIXファイル選択ボタンにてファイル選択後
    $('#stix-file-file').change(function(){
        $('#stix-file-text').val(get_selected_fileform_value(this));
    });

    //Upload押下時
    $('#upload-button').click(function(){
    	//引数チェック
    	if($('#community-id').val() == ''){
    		alert('Choose Community');
    		return false;
    	}
    	if($('#stix-file-file').val() == ''){
    		alert('Choose Stix File');
    		return false;
    	}
        $('#upload-form').submit();
    });
    //ファイルフォームのok押下後にテキストエリアに書き込む
    //ファイル名文字列を取得
    function get_selected_fileform_value(fileForm){
        var text = '';
        for(i = 0;i < fileForm.files.length;i++){
            text += (fileForm.files[i].name+ ';')
        }
        return text;
    };
});
