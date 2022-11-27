# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon
import xbmcgui

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

    def call_o2_api(self, url, data, headers, nolog = False):
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
            if addon.getSetting('log_response') == 'true' and nolog == False :
                xbmc.log('O2TV > ' + str(html))
            if html and len(html) > 0:
                data = json.loads(html)
                return data
            else:
                return []
        except HTTPError as e:
            xbmc.log('O2TV > ' 'Chyba při volání '+ str(url) + ': ' + e.reason)
            return { 'err' : e.reason }  
        
def o2tv_list_api(post, nolog = False):
    result = []
    o2api = O2API()
    fetch = True
    while fetch == True:
        data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/asset/action/list?format=1&clientTag=1.16.1-PC', data = post, headers = o2api.headers, nolog = nolog)
        if 'err' in data or not 'result' in data or not 'totalCount' in data['result']:
            xbmcgui.Dialog().notification('O2TV','Problém při stažení dat z O2TV', xbmcgui.NOTIFICATION_ERROR, 5000)
            fetch = False
        else:
            total_count = data['result']['totalCount']
            if total_count > 0:
                for object in data['result']['objects']:
                    result.append(object)
                if total_count == len(result):
                    fetch = False
                else:
                    pager = post['pager']
                    pager['pageIndex'] = pager['pageIndex'] + 1
                    post['pager'] = pager
            else:
                fetch = False
    return result        


