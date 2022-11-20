# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon

import json
import gzip 

try:
    from urllib2 import urlopen, Request, HTTPError
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError

class O2API:
    def __init__(self):
        self.headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0', 'Accept-Encoding' : 'gzip', 'Accept' : '*/*', 'Content-type' : 'application/json;charset=UTF-8'} 

    def call_o2_api(self, url, data, headers):
        addon = xbmcaddon.Addon()
        if data != None:
            data = json.dumps(data).encode("utf-8")
        request = Request(url = url , data = data, headers = headers)

        if addon.getSetting('log_request_url') == 'true':
            xbmc.log('O2TV > ' + str(url))
        if addon.getSetting('log_request_data') == 'true' and data != None:
            xbmc.log('O2TV > ' + str(data))
        try:
            response = urlopen(request)
            if response.getheader("Content-Encoding") == 'gzip':
                gzipFile = gzip.GzipFile(fileobj = response)
                html = gzipFile.read()
            else:
                html = response.read()
            if addon.getSetting('log_response') == 'true':
                xbmc.log('O2TV > ' + str(html))
            if html and len(html) > 0:
                data = json.loads(html)
                return data
            else:
                return []
        except HTTPError as e:
            xbmc.log('O2TV > ' 'Chyba při volání '+ str(url) + ': ' + e.reason)
            return { 'err' : e.reason }  

