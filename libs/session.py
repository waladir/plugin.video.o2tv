# -*- coding: utf-8 -*-
import sys
import xbmcaddon
import xbmcgui

import json
import time 

from libs.settings import Settings
from libs.o2tv import O2API

class Session:
    def __init__(self):
        self.valid_to = -1
        self.load_session()

    def create_session(self):
        self.get_token()
        self.save_session()

    def get_ks_code(self):
        ks_code = None
        addon = xbmcaddon.Addon()    
        o2api = O2API()
        post = {'username' : addon.getSetting('username'), 'password' : addon.getSetting('password')} 
        data = o2api.call_o2_api(url = 'https://api.o2tv.cz/unity/api/v1/services/', data = post, headers = o2api.headers)
        if 'err' in data:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()    
        if 'services' in data and 'remoteAccessToken' in data and len(data['remoteAccessToken']) > 0 and len(data['services']) > 0:
            remote_access_token = data['remoteAccessToken'] 
            for service in data['services']:
                service_id = service['serviceId']
                post = {'remoteAccessToken' : remote_access_token} 
                data = o2api.call_o2_api(url = 'https://api.o2tv.cz/unity/api/v1/services/selection/' + service_id + '/', data = post, headers = o2api.headers)
                if 'err' in data:
                    xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
                    sys.exit()    
                if 'accessToken' in data and len(data['accessToken']) > 0:
                    access_token = data['accessToken']
                    header_unity = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0', 'Content-Type' : 'application/json', 'x-o2tv-access-token' : str(access_token), 'x-o2tv-device-id' : addon.getSetting('deviceid'), 'x-o2tv-device-name' : addon.getSetting('devicename')}
                    data = o2api.call_o2_api(url = 'https://api.o2tv.cz/unity/api/v1/user/profile/', data = None, headers = header_unity)
                    if 'err' in data:
                        xbmcgui.Dialog().notification(' O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
                        sys.exit()  
                    ks_code = data['code']        
        return ks_code

    def get_token(self):
        addon = xbmcaddon.Addon()
        o2api = O2API()
        ks_code = self.get_ks_code()
        post = {'language' : '*', 'partnerId' : 3201, 'clientTag' : '1.16.1-PC', 'apiVersion' : '5.4.0'}
        data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/ottuser/action/anonymousLogin?format=1&clientTag=1.16.1-PC', data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaLoginSession':
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        ks = data['result']['ks']
            
        post = {'username' : addon.getSetting('username'), 'password' : addon.getSetting('password'), 'udid' : addon.getSetting('deviceid'), 'service' : 'https://www.new-o2tv.cz/'} 
        data = o2api.call_o2_api(url = 'https://login-a-moje.o2.cz/cas-external/v1/login', data = post, headers = o2api.headers)
        if 'err' in data or not 'jwt' in data or not 'refresh_token' in data:
            xbmcgui.Dialog().ok('O2TV', 'Doplněk je určený pouze pro O2TV 2.0.\n\nPro původní O2TV použijte doplněk Sledování O2TV ze stejného repozitáře.')
            # xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        jwt_token = data['jwt']
        
        post = {'language' : 'ces', 'ks' : ks, 'partnerId' : 3201, 'username' : 'NONE', 'password' : 'NONE', 'extraParams' : {'token' : {'objectType' : 'KalturaStringValue', 'value' : jwt_token}, 'loginType' : {'objectType' : 'KalturaStringValue', 'value' : 'accessToken'}, 'brandId' : {'objectType' : 'KalturaStringValue', 'value' : '22'}, 'externalId' : {'objectType' : 'KalturaStringValue', 'value' : ks_code}}, 'udid' : addon.getSetting('deviceid'), 'clientTag' : '1.16.1-PC', 'apiVersion' : '5.4.0'}
        data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/ottuser/action/login?format=1&clientTag=1.16.1-PC', data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaLoginResponse' or not 'loginSession' in data['result']:
            xbmcgui.Dialog().notification('O2TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        self.ks_expiry = data['result']['loginSession']['expiry']
        self.ks_refresh_token = data['result']['loginSession']['refreshToken']
        self.ks = data['result']['loginSession']['ks']

        # post = {'language' : 'ces', 'ks' : ks, 'clientTag' : '1.16.1-PC', 'apiVersion' : '5.4.0'}
        # data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/ottuser/action/get?format=1&clientTag=1.16.1-PC', data = post, headers = o2api.headers)
        # print(data)

    def load_session(self):
        settings = Settings()
        data = settings.load_json_data({'filename' : 'session.txt', 'description' : 'session'})
        if data is not None:
            data = json.loads(data)
            self.ks_expiry = int(data['ks_expiry'])
            self.ks_refresh_token = data['ks_refresh_token']
            self.ks = data['ks']
            if self.ks_expiry and self.ks_expiry < int(time.time()):
                self.create_session()
        else:
            self.create_session()

    def save_session(self):
        settings = Settings()
        data = json.dumps({'ks_expiry' : self.ks_expiry, 'ks_refresh_token' : self.ks_refresh_token, 'ks' : self.ks})
        settings.save_json_data({'filename' : 'session.txt', 'description' : 'session'}, data)

    def remove_session(self):
        settings = Settings()
        settings.reset_json_data({'filename' : 'session.txt', 'description' : 'session'})
        self.valid_to = -1
        self.create_session()
        xbmcgui.Dialog().notification('O2TV', 'Byla vytvořená nová session', xbmcgui.NOTIFICATION_INFO, 5000)
