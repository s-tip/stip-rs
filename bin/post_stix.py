import os
import sys
import json
import requests
import argparse

##############################
#post_stix
#STIX 登録
##############################
#第1引数：URL
#第2引数：username
#第3引数：apikey
#第4引数：community_name
#第5引数：attachment 
##############################
#オプション
# -p  package name
##############################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Post STIX Script')
    parser.add_argument('-p','--package_name',help='package name(option)')
    parser.add_argument('url',help='url')
    parser.add_argument('user_name',help='user name')
    parser.add_argument('apikey',help='apikey')
    parser.add_argument('community_name',help='community name')
    parser.add_argument('attachments',help='attachements file')
    args = parser.parse_args()

    #認証情報
    headers = {
        'username': args.user_name,
        'apikey': args.apikey,
    }

    #upload情報
    data = {
        'community_name' : args.community_name
    }
    if args.package_name is not None:
        data['package_name'] = args.package_name

    #ファイルアップロード
    files = {}
    files['stix'] = open(args.attachments)

    #リクエスト送信
    r = requests.post(
        args.url,
        headers=headers,
        data=data,
        files=files,
        verify=False)

    #response 解析
    b = json.loads(r.text)
    if r.status_code != 201:
        print('Request Failed (%s, %s).' % (r.status_code,b['userMessage']))
        sys.exit(os.EX_UNAVAILABLE)
    else:
        print('Success!')
        sys.exit(os.EX_OK)
        
