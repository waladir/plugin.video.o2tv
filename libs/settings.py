# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
try:
    from xbmcvfs import translatePath
except ImportError:
    from xbmc import translatePath

from datetime import datetime

from libs.session import Session
from libs.o2tv import O2API
from libs.utils import get_url, get_partnerId, apiVersion, clientTag, encode

def list_settings(label):
    _handle = int(sys.argv[1])
    xbmcplugin.setPluginCategory(_handle, label)

    list_item = xbmcgui.ListItem(label='Kanály')
    url = get_url(action='manage_channels', label = 'Kanály')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label='Služby')
    url = get_url(action='list_services', label = 'Služby')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label='Zařízení')
    url = get_url(action='list_devices', label = 'Zařízení')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label='Nastavení doplňku')
    url = get_url(action='addon_settings', label = 'Nastavení doplňku')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle)

def list_services(label):
    _handle = int(sys.argv[1])
    xbmcplugin.setPluginCategory(_handle, label)   
    session = Session()
    for serviceid in session.services:
        if 'ks_name' in session.services[serviceid]:
            name = ' - ' + session.services[serviceid]['ks_name']
        else:
            name = ''
        if session.services[serviceid]['enabled'] == 1:
            list_item = xbmcgui.ListItem(label = serviceid + name)
        else:
            list_item = xbmcgui.ListItem(label = '[COLOR=gray]' + serviceid + name + '[/COLOR]')
        url = get_url(action='enable_service', serviceid = serviceid)  
        xbmcplugin.addDirectoryItem(_handle, url , list_item, False)  
        first = 0
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def enable_service(serviceid):
    session = Session()
    if serviceid in session.services:
        session.enable_service(serviceid)
    xbmcgui.Dialog().notification('O2TV', 'Po změně služby je třeba resetovat seznam kanálů!', xbmcgui.NOTIFICATION_WARNING, 5000)
    xbmc.executebuiltin('Container.Refresh')   

def list_devices(label):
    _handle = int(sys.argv[1])
    xbmcplugin.setPluginCategory(_handle, label)   
    session = Session()
    o2api = O2API()

    active = []
    post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaStreamingDeviceFilter"},"clientTag":clientTag,"apiVersion":apiVersion}
    data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/streamingdevice/action/list?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers, nolog = False)
    if 'err' not in data and 'result' in data and len(data['result']) > 0 and 'objects' in data['result'] and len(data['result']['objects']) > 0:
        for device in data['result']['objects']:
            active.append(device['udid'])

    types = {}
    post = {"language":"ces","ks":session.ks,"clientTag":clientTag,"apiVersion":apiVersion}
    data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/devicebrand/action/list?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers, nolog = False)
    if 'err' not in data and 'result' in data and len(data['result']) > 0 and 'objects' in data['result'] and len(data['result']['objects']) > 0:
        for item in data['result']['objects']:
            types.update({item['id'] : item['name']})

    post = {"language":"ces","ks":session.ks,"clientTag":clientTag,"apiVersion":apiVersion}
    data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/householddevice/action/list?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers, nolog = False)
    if 'err' in data or not 'result' in data or len(data['result']) == 0 or 'objects' not in data['result'] or len(data['result']['objects']) == 0:
        xbmcgui.Dialog().notification('O2TV','Problém při načtení zařízení', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit() 
    for device in data['result']['objects']:
        if 'activatedOn' in device and len(str(device['activatedOn'])) > 0: 
            activated = '\n[COLOR=gray]aktivováno: ' + datetime.fromtimestamp(int(device['activatedOn'])).strftime('%d.%m.%Y %H:%M') + '[/COLOR]'
        else:
            activated = ''
        if device['udid'] in active:
            streaming = True
        else:
            streaming = False        
        if device['brandId'] in types:
            device_name = device['udid'] + ' (' + types[device['brandId']] + ')'
        else:
            device_name = device['udid']

        if streaming:
            list_item = xbmcgui.ListItem(label = '[COLOR=red]' + encode(device_name) + activated + '[/COLOR]')
        else:
            list_item = xbmcgui.ListItem(label = encode(device_name) + activated)
        url = get_url(action='delete_device', udid = device['udid'])  
        xbmcplugin.addDirectoryItem(_handle, url , list_item, False)  
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def delete_device(udid):
    response = xbmcgui.Dialog().yesno('Odhlášení zařízení', 'Opravdu provést odhlašení zařízení s ID ' + udid + '?', nolabel = 'Ne', yeslabel = 'Ano')
    if response:
        session = Session()
        o2api = O2API()
        post = {"language":"ces","ks":session.ks,"udid":udid,"clientTag":clientTag,"apiVersion":apiVersion}
        data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/householddevice/action/delete?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers, nolog = False)
        xbmc.executebuiltin('Container.Refresh')
    
class Settings:
    def __init__(self):
        self.is_settings_ok = self.check_settings()
           
    def check_settings(self):
        addon = xbmcaddon.Addon()
        if not addon.getSetting('username') or not addon.getSetting('password'):
            xbmcgui.Dialog().notification('O2TV', 'V nastavení je nutné mít vyplněné přihlašovací údaje', xbmcgui.NOTIFICATION_ERROR, 5000)            
            return False
        else:
            return True

    def save_json_data(self, file, data):
        addon = xbmcaddon.Addon()
        addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
        if self.is_settings_ok:
            filename = os.path.join(addon_userdata_dir, file['filename'])
            try:
                with open(filename, "w") as f:
                    f.write('%s\n' % data)
            except IOError:
                xbmcgui.Dialog().notification('O2TV', 'Chyba uložení ' + file['description'], xbmcgui.NOTIFICATION_ERROR, 5000)

    def load_json_data(self, file):
        data = None
        if self.is_settings_ok:
            addon = xbmcaddon.Addon()
            addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
            filename = os.path.join(addon_userdata_dir, file['filename'])
            try:
                with open(filename, "r") as f:
                    for row in f:
                        data = row[:-1]
            except IOError:
                pass
            except IOError:
                xbmcgui.Dialog().notification('O2TV', 'Chyba při načtení ' + file['description'], xbmcgui.NOTIFICATION_ERROR, 5000)
        return data    

    def reset_json_data(self, file):
        if self.is_settings_ok:
            addon = xbmcaddon.Addon()
            addon_userdata_dir = translatePath(addon.getAddonInfo('profile'))
            filename = os.path.join(addon_userdata_dir, file['filename'])
            try:
                os.remove(filename)
            except IOError:
                pass
            except IOError:
                xbmcgui.Dialog().notification('O2TV', 'Chyba při resetu ' + file['description'], xbmcgui.NOTIFICATION_ERROR, 5000)