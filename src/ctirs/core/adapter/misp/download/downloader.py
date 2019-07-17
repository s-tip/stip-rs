#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import requests
from ctirs.models.rs.models import System

class MISPDownloader(object):
    def __init__(self,url,api_key):
        self.url = url
        self.header = {}
        self.header['Content-Type'] = 'application/json'
        self.header['Authorization'] = api_key

    def get_date_str(self,dt):
        return dt.strftime('%Y-%m-%d')

    def get(self,
        from_dt=None,
        to_dt=None,
        withAttachment=False):
        payload = {}
        payload_request = {}
        payload_request['eventid'] = False
        payload_request['withAttachment'] = withAttachment

        if from_dt is None:
            payload_request['from'] = False
        else:
            payload_request['from'] = self.get_date_str(from_dt)

        if to_dt is None:
            payload_request['to'] = False
        else:
            payload_request['to'] = self.get_date_str(to_dt)

        payload_request['tags'] = []
        payload['request'] = payload_request

        proxies = System.get_requets_proxies()
        resp = requests.post(
            self.url,
            data = json.dumps(payload),
            headers = self.header,
            verify = False,
            proxies=proxies)

        if resp.status_code == 404:
            print 'No events'
            return None

        if resp.status_code != 200:
            print 'http_response_status is ' + str(resp.status_code)
            print 'message :' + str(resp.text)
            print 'Exit.'
            return None
        return resp.text

