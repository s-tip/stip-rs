import json
import traceback
import requests

# Webhook対象の操作
OPERATION_CREATE = 'create'
OPERATION_TEST = 'test'

# StixFile作成時のwebhook


def webhook_create(community, stix_file_doc):
    webhook_doc = {}
    webhook_doc['operation'] = OPERATION_CREATE
    webhook_doc['stix_files'] = []
    webhook_doc['stix_files'].append(stix_file_doc.get_webhook_document())
    webhook_json = json.dumps(webhook_doc)
    for webhook in community.webhooks:
        try:
            webhook_post(webhook, webhook_json)
        except BaseException:
            # webhookに失敗しても処理は止めない(loggingのみ)
            traceback.print_exc()

# test用のwebhook


def webhook_test(webhook):
    webhook_doc = {}
    webhook_doc['operation'] = OPERATION_TEST
    webhook_json = json.dumps(webhook_doc)
    webhook_post(webhook, webhook_json)

# webhook post


def webhook_post(webhook, webhook_json):
    rsp = requests.post(
        webhook.url,
        data=webhook_json,
        headers={'Content-Type': 'application/json'},
        verify=False)
    if rsp.status_code != 200:
        print('Can\'t send webhook(%s)' % (webhook.url))
    return
