# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
import argparse

##############################
# delete_stix
# STIX 削除
##############################
# 第1引数：URL (http(s)://host:port/api/vi/stix_files_package_id/)
# 第2引数：username
# 第3引数：apikey
# 第4引数：package_id
##############################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete STIX Script')
    parser.add_argument('url', help='url')
    parser.add_argument('user_name', help='user name')
    parser.add_argument('apikey', help='apikey')
    parser.add_argument('package_id', help='package id')
    args = parser.parse_args()

    # 認証情報
    headers = {
        'username': args.user_name,
        'apikey': args.apikey,
    }

    url = '%s%s' % (args.url, args.package_id)

    # リクエスト送信
    r = requests.delete(
        url,
        headers=headers,
        verify=False)

    # response 解析
    b = json.loads(r.text)
    if r.status_code != 200:
        print 'Request Failed (%s).' % (r.status_code)
        sys.exit(os.EX_UNAVAILABLE)
    else:
        print 'Success!'
        sys.exit(os.EX_OK)
