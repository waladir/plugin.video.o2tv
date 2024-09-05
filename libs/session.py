# -*- coding: utf-8 -*-
import sys
import xbmcaddon
import xbmcgui

import json
import time 

from libs.o2tv import O2API
from libs.utils import clientTag, apiVersion, get_partnerId

import requests
import random, string
from base64 import b64encode, urlsafe_b64encode
from hashlib import sha256
from urllib.parse import parse_qs, urlparse

class Session:
    def __init__(self):
        self.valid_to = -1
        self.load_session()

    def create_session(self):
        self.get_token()
        self.save_session()

    def enable_service(self, serviceid):
        for service in self.services:
            if serviceid == service:
                self.services[service]['enabled'] = 1
            else:
                self.services[service]['enabled'] = 0
        self.save_session()

    def get_token_sk(self):
        addon = xbmcaddon.Addon()
        o2api = O2API()

        code_verifier = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(43))
        code_challenge = urlsafe_b64encode(sha256(code_verifier.encode('ascii')).digest()).decode('ascii')[:-1]

        session = requests.Session()
        headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0', 'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8', 'Refered' : 'https://www.o2tv.sk/', 'Upgrade-Insecure-Requests' : '1', 'Host' : 'api.o2.sk', 'Accept-Encoding' : 'gzip', 'DNT' : '1', 'Sec-GPC' : '1', 'Connection' : 'keep-alive', 'Sec-Fetch-Dest' : 'document', 'Sec-Fetch-Mode' : 'navigate', 'Sec-Fetch-Site' : 'cross-site' , 'Sec-Fetch-User' : '?1', 'Priority' : 'u=0, i'}

        params = {'key': addon.getSetting('deviceid'), 'name' : 'anonymous', 'anonymous' : True, 'custom' : {'applicationName' : 'com.Kaltura.telenorhungary.web', 'clientTag' : clientTag, 'clientVersion' : '9.40.0', "consumerEmail":"","platform":"other","deviceBrand":'22', 'deviceFamily' : '5', 'firmware' : 'n/a', 'partnerId' : get_partnerId(), 'release' : 'com.Kaltura.telenorhungary.web@9.40.0', 'osVersion' : '5.0 (Windows)', 'tvpilVersion' :'1.55.3'}}
        data = session.get(url = 'https://app.launchdarkly.com/sdk/evalx/600829da51479b0a7a58ca57/contexts/' + b64encode(json.dumps(params).encode('utf-8')).decode('utf-8'), headers = {'X-Launchdarkly-User-Agent' : 'JSClient/3.1.3'}).json()
        if not 'AUTH_PARAMS' in data or not 'oAuthClientId' in data['AUTH_PARAMS']['value']:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()
        client_id = data['AUTH_PARAMS']['value']['oAuthClientId']

        response = session.get(url = 'https://api.o2.sk/oauth2/authorize?response_type=code&client_id=' + client_id + '&redirect_uri=https://www.o2tv.sk/auth/&code_challenge=' + code_challenge + '&code_challenge_method=S256&scope=tv_info', headers = headers)
        if not 'sessionDataKey' in response.url:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení1', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()
        url_parts = urlparse(response.url)
        data = parse_qs(url_parts.query)
        sessionDataKey = data['sessionDataKey'][0]

        response = session.post(url = 'https://api.o2.sk/commonauth?sessionDataKey=' + sessionDataKey + '&handler=UIDAuthenticationHandler&username=' + addon.getSetting('username') + '&password=' + addon.getSetting('password'), headers = headers)
        if not 'code' in response.url:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()
        url_parts = urlparse(response.url)
        data = parse_qs(url_parts.query)
        code = data['code'][0]

        params = 'grant_type=authorization_code&client_id=' + client_id + '&code=' + code + '&redirect_uri=https%3A%2F%2Fwww.o2tv.sk%2Fauth%2F&code_verifier=' + code_verifier
        data = session.post(url = 'https://api.o2.sk/oauth2/token?' + params, headers = {'Content-type' : 'application/x-www-form-urlencoded'}).json()
        if not 'access_token' in data:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()
        access_token = data['access_token']

        post = {'language' : '*', 'partnerId' : int(get_partnerId()), 'clientTag' : clientTag, 'apiVersion' : apiVersion}
        data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/ottuser/action/anonymousLogin?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaLoginSession':
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        ks = data['result']['ks']

        post = {'language' : 'slk', 'ks': ks, 'partnerId' : get_partnerId(), 'username' : '11111', 'password' : '11111' ,'extraParams' : {'loginType' : {'objectType' : 'KalturaStringValue', 'value' : 'accessToken'},"accessToken":{"objectType":"KalturaStringValue","value":access_token}},'udid' : addon.getSetting('deviceid'), 'clientTag' : clientTag, 'apiVersion' : apiVersion}
        data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/ottuser/action/login?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaLoginResponse' or not 'loginSession' in data['result']:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 

        if self.services is None:
            self.services = {}
        self.services.update({'O2TV' : {'ks_name' : 'O2TV', 'ks_code' : 'O2TV', 'ks_expiry' : data['result']['loginSession']['expiry'], 'ks_refresh_token' : data['result']['loginSession']['refreshToken'], 'ks' : data['result']['loginSession']['ks'], 'enabled' : 1}})
        ks = data['result']['loginSession']['ks']

        post = {'language' : 'slk', 'ks' : ks, 'clientTag' : clientTag, 'apiVersion' : apiVersion}
        data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/householddevice/action/get', data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or 'error' in data['result']:
                post = {'language' : 'slk', 'ks' : ks, 'device' : {'objectType' : 'KalturaHouseholdDevice', 'udid': addon.getSetting('deviceid'), 'name' : '', 'brandId':22}, 'clientTag' : clientTag, 'apiVersion' : apiVersion}
                data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/householddevice/action/add?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
                if 'err' in data or not 'result' in data or 'error' in data['result']:
                    xbmcgui.Dialog().notification('O2TV','Problém při regostraci zařízení', xbmcgui.NOTIFICATION_ERROR, 5000)
                    sys.exit() 

    def get_token_cz(self):
        addon = xbmcaddon.Addon()
        o2api = O2API()

        post = {'language' : '*', 'partnerId' : int(get_partnerId()), 'clientTag' : clientTag, 'apiVersion' : apiVersion}
        data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/ottuser/action/anonymousLogin?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaLoginSession':
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        ks = data['result']['ks']

        post = {'username' : addon.getSetting('username'), 'password' : addon.getSetting('password'), 'udid' : addon.getSetting('deviceid'), 'service' : 'https://www.new-o2tv.cz/'} 
        data = o2api.call_o2_api(url = 'https://login-a-moje.o2.cz/cas-external/v1/login', data = post, headers = o2api.headers, sensitive = True)
        if 'err' in data or not 'jwt' in data or not 'refresh_token' in data:
            xbmcgui.Dialog().ok('O2TV', 'Chyba při přihlášení, zkontrolujte jméno a heslo')
            sys.exit() 
        jwt_token = data['jwt']

        post = {"intent":"Service List","adapterData":[{"_allowedEmptyArray":[],"_allowedEmptyObject":[],"_dependentProperties":{},"key":"access_token","value":jwt_token,"relatedObjects":{}},{"_allowedEmptyArray":[],"_allowedEmptyObject":[],"_dependentProperties":{},"key":"pageIndex","value":"0","relatedObjects":{}},{"_allowedEmptyArray":[],"_allowedEmptyObject":[],"_dependentProperties":{},"key":"pageSize","value":"100","relatedObjects":{}}],"ks":ks}
        data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api/p/' + get_partnerId() + '/service/CZ/action/Invoke', data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or not 'adapterData' in data['result'] or not 'service_list' in data['result']['adapterData']:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        services = json.loads(data['result']['adapterData']['service_list']['value'])

        services = services['ServicesList']
        ks_codes = {}
        ks_names = {}
        for service in services:
            for id in service:
                ks_codes.update({service[id] : service[id]})
                ks_names.update({service[id] : id})

        if len(ks_codes) < 1:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 

        for service in ks_codes:
            if self.services is None:
                self.services = {}
                self.services.update({service : {'ks_name' : ks_names[service], 'ks_code' : ks_codes[service], 'ks_expiry' : -1, 'ks_refresh_token' : '', 'ks' : '', 'enabled' : 1}})
            if service in self.services and self.services[service]['enabled'] == 1:
                post = {'language' : 'ces', 'ks' : ks, 'partnerId' : int(get_partnerId()), 'username' : 'NONE', 'password' : 'NONE', 'extraParams' : {'token' : {'objectType' : 'KalturaStringValue', 'value' : jwt_token}, 'loginType' : {'objectType' : 'KalturaStringValue', 'value' : 'accessToken'}, 'brandId' : {'objectType' : 'KalturaStringValue', 'value' : '22'}, 'externalId' : {'objectType' : 'KalturaStringValue', 'value' : ks_codes[service]}}, 'udid' : addon.getSetting('deviceid'), 'clientTag' : clientTag, 'apiVersion' : apiVersion}
                data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/ottuser/action/login?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
                if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaLoginResponse' or not 'loginSession' in data['result']:
                    xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
                    sys.exit() 
                self.services.update({service : {'ks_name' : ks_names[service], 'ks_code' : ks_codes[service], 'ks_expiry' : data['result']['loginSession']['expiry'], 'ks_refresh_token' : data['result']['loginSession']['refreshToken'], 'ks' : data['result']['loginSession']['ks'], 'enabled' : self.services[service]['enabled']}})
            else:
                self.services.update({service : {'ks_name' : ks_names[service], 'ks_code' : ks_codes[service], 'ks_expiry' : -1, 'ks_refresh_token' : '', 'ks' : '', 'enabled' : 0}})                    

        for service in list(self.services):
            if service not in ks_codes.keys():
                del self.services[service]

        # post = {'language' : 'ces', 'ks' : ks, 'clientTag' : clientTag, 'apiVersion' : apiVersion}
        # data = o2api.call_o2_api(url = 'https://' + partnerId + '.frp1.ott.kaltura.com/api_v3/service/ottuser/action/get?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
        # print(data)

    def get_token(self):
        addon = xbmcaddon.Addon()
        if addon.getSetting('service') == 'o2tv.cz':
            self.get_token_cz()
        elif addon.getSetting('service') == 'o2tv.sk':
            self.get_token_sk()

    def load_session(self):
        from libs.settings import Settings
        settings = Settings()
        data = settings.load_json_data({'filename' : 'session.txt', 'description' : 'session'})
        self.services = None
        if data is not None:
            data = json.loads(data)
            reset = 0
            if 'services' in data:
                self.services = {}
                services = data['services']
# konverze id pro sluzby (update 1.3.1)                
                for serviceid in services:
                    id = services[serviceid]['ks_code']
                    self.services.update({id : services[serviceid]})
                for serviceid in self.services:
                    service = self.services[serviceid]
                    if 'ks_expiry' not in service or (int(service['enabled']) == 1 and int(service['ks_expiry']) < int(time.time())):
                        if reset == 0: 
                            self.create_session()
                            reset = 1
            else:
                self.create_session()
        else:
            self.create_session()
        active = False
        for service in self.services:
            if self.services[service]['enabled'] == 1:
                active = True
                self.ks = self.services[service]['ks']
        if active == False:
            for service in self.services:
                if active == False:
                    active = True
                    self.ks = self.services[service]['ks']
                    self.services[service]['enabled'] = 1
                    self.save_session                

    def save_session(self):
        from libs.settings import Settings
        settings = Settings()
        data = json.dumps({'services' : self.services})        
        settings.save_json_data({'filename' : 'session.txt', 'description' : 'session'}, data)

    def remove_session(self):
        from libs.settings import Settings
        settings = Settings()
        settings.reset_json_data({'filename' : 'session.txt', 'description' : 'session'})
        self.valid_to = -1
        self.create_session()
        xbmcgui.Dialog().notification('O2TV', 'Byla vytvořená nová session', xbmcgui.NOTIFICATION_INFO, 5000)
