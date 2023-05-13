# -*- coding: utf-8 -*-
import sys
import xbmcaddon
import xbmcgui

import json
import time 

from libs.o2tv import O2API
from libs.utils import clientTag, apiVersion, partnerId

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

    def get_token(self):
        addon = xbmcaddon.Addon()
        o2api = O2API()

        post = {'language' : '*', 'partnerId' : int(partnerId), 'clientTag' : clientTag, 'apiVersion' : apiVersion}
        data = o2api.call_o2_api(url = 'https://' + partnerId + '.frp1.ott.kaltura.com/api_v3/service/ottuser/action/anonymousLogin?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaLoginSession':
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        ks = data['result']['ks']

        post = {'username' : addon.getSetting('username'), 'password' : addon.getSetting('password'), 'udid' : addon.getSetting('deviceid'), 'service' : 'https://www.new-o2tv.cz/'} 
        data = o2api.call_o2_api(url = 'https://login-a-moje.o2.cz/cas-external/v1/login', data = post, headers = o2api.headers)
        if 'err' in data or not 'jwt' in data or not 'refresh_token' in data:
            xbmcgui.Dialog().ok('O2TV', 'Doplněk je určený pouze pro O2TV 2.0.\n\nPro původní O2TV použijte doplněk Sledování O2TV ze stejného repozitáře.')
            sys.exit() 
        jwt_token = data['jwt']

        post = {"intent":"Service List","adapterData":[{"_allowedEmptyArray":[],"_allowedEmptyObject":[],"_dependentProperties":{},"key":"access_token","value":jwt_token,"relatedObjects":{}},{"_allowedEmptyArray":[],"_allowedEmptyObject":[],"_dependentProperties":{},"key":"pageIndex","value":"0","relatedObjects":{}},{"_allowedEmptyArray":[],"_allowedEmptyObject":[],"_dependentProperties":{},"key":"pageSize","value":"100","relatedObjects":{}}],"ks":ks}
        data = o2api.call_o2_api(url = 'https://' + partnerId + '.frp1.ott.kaltura.com/api/p/' + partnerId + '/service/CZ/action/Invoke', data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or not 'adapterData' in data['result'] or not 'service_list' in data['result']['adapterData']:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        services = json.loads(data['result']['adapterData']['service_list']['value'])

        services = services['ServicesList']
        ks_codes = {}
        for service in services:
            for id in service:
                ks_codes.update({id : service[id]})
        
        if len(ks_codes) < 1:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        
        for service in ks_codes:
            post = {'language' : 'ces', 'ks' : ks, 'partnerId' : int(partnerId), 'username' : 'NONE', 'password' : 'NONE', 'extraParams' : {'token' : {'objectType' : 'KalturaStringValue', 'value' : jwt_token}, 'loginType' : {'objectType' : 'KalturaStringValue', 'value' : 'accessToken'}, 'brandId' : {'objectType' : 'KalturaStringValue', 'value' : '22'}, 'externalId' : {'objectType' : 'KalturaStringValue', 'value' : ks_codes[service]}}, 'udid' : addon.getSetting('deviceid'), 'clientTag' : clientTag, 'apiVersion' : apiVersion}
            data = o2api.call_o2_api(url = 'https://' + partnerId + '.frp1.ott.kaltura.com/api_v3/service/ottuser/action/login?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
            if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaLoginResponse' or not 'loginSession' in data['result']:
                xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
                sys.exit() 
            if self.services is not None:
                if service in self.services:
                    self.services.update({service : {'ks_code' : ks_codes[service], 'ks_expiry' : data['result']['loginSession']['expiry'], 'ks_refresh_token' : data['result']['loginSession']['refreshToken'], 'ks' : data['result']['loginSession']['ks'], 'enabled' : self.services[service]['enabled']}})
                else:
                    self.services.update({service : {'ks_code' : ks_codes[service], 'ks_expiry' : data['result']['loginSession']['expiry'], 'ks_refresh_token' : data['result']['loginSession']['refreshToken'], 'ks' : data['result']['loginSession']['ks'], 'enabled' : 0}})                    
            else:
                self.services = {}
                self.services.update({service : {'ks_code' : ks_codes[service], 'ks_expiry' : data['result']['loginSession']['expiry'], 'ks_refresh_token' : data['result']['loginSession']['refreshToken'], 'ks' : data['result']['loginSession']['ks'], 'enabled' : 0}})
        for service in list(self.services):
            if service not in ks_codes.keys():
                del self.services[service]

        # post = {'language' : 'ces', 'ks' : ks, 'clientTag' : clientTag, 'apiVersion' : apiVersion}
        # data = o2api.call_o2_api(url = 'https://' + partnerId + '.frp1.ott.kaltura.com/api_v3/service/ottuser/action/get?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
        # print(data)

    def load_session(self):
        from libs.settings import Settings
        settings = Settings()
        data = settings.load_json_data({'filename' : 'session.txt', 'description' : 'session'})
        self.services = None
        if data is not None :
            data = json.loads(data)
            reset = 0
            if 'services' in data:
                self.services = data['services']
                for serviceid in self.services:
                    service = self.services[serviceid]
                    if 'ks_expiry' not in service or int(service['ks_expiry']) < int(time.time()):
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
