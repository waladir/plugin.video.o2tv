# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

try:
    from xbmcvfs import translatePath
except ImportError:
    from xbmc import translatePath

try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote    

from datetime import datetime

from libs.utils import PY3, get_url, plugin_id, day_translation_short, decode
from libs.session import Session
from libs.o2tv import O2API
from libs.channels import Channels
from libs.epg import epg_listitem, epg_api

_handle = int(sys.argv[1])

def openfile(fname, mode):
    return open(fname, mode, encoding = 'utf-8') if PY3 else open(fname, mode)

def list_search(label):
    xbmcplugin.setPluginCategory(_handle, label)
    list_item = xbmcgui.ListItem(label='Nové hledání')
    url = get_url(action='program_search', query = '-----', label = label + ' / ' + 'Nové hledání')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    history = load_search_history()
    for item in history:
        list_item = xbmcgui.ListItem(label=item)
        url = get_url(action='program_search', query = item, label = label + ' / ' + item)  
        list_item.addContextMenuItems([('Smazat', 'RunPlugin(plugin://' + plugin_id + '?action=delete_search&query=' + quote(item) + ')')])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle,cacheToDisc = False)

def program_search(query, label):
    xbmcplugin.setPluginCategory(_handle, label)
    if query == '-----':
        input = xbmc.Keyboard('', 'Hledat')
        input.doModal()
        if not input.isConfirmed(): 
            return
        query = input.getText()
        if len(query) == 0:
            xbmcgui.Dialog().notification('O2TV', 'Je potřeba zadat vyhledávaný řetězec', xbmcgui.NOTIFICATION_ERROR, 5000)
            return   
        else:
            save_search_history(query)
    session = Session()
    o2api = O2API()
    channels = Channels()
    channels_list = channels.get_channels_list(visible_filter = True)
    post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaChannelFilter","orderBy":"NAME_ASC","kSql":"(and name^'" + query +  "')","idEqual":355960},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":"1.16.1-PC","apiVersion":"5.4.0"}
    data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/asset/action/list?format=1&clientTag=1.16.1-PC', data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaAssetListResponse':
        xbmcgui.Dialog().notification('O2TV','Problém při stažení EPG', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit() 
    if 'objects' in data['result'] and len(data['result']['objects']) > 0:
        epg = epg_api(post = post, key = 'id')
        for item in data['result']['objects']:
            if item['objectType'] == 'KalturaProgramAsset' and item['linearAssetId'] in channels_list:                
                list_item = xbmcgui.ListItem(label = item['name'] + ' (' + channels_list[item['linearAssetId']]['name'] + ' | ' + decode(day_translation_short[datetime.fromtimestamp(item['startDate']).strftime('%w')]) + ' ' + datetime.fromtimestamp(item['startDate']).strftime('%d.%m %H:%M') + ' - ' + datetime.fromtimestamp(item['endDate']).strftime('%H:%M') + ')')
                list_item = epg_listitem(list_item = list_item, epg = epg[item['id']], logo = channels_list[item['linearAssetId']]['logo'])
                list_item.setProperty('IsPlayable', 'true')
                list_item.setContentLookup(False)          
                url = get_url(action='play_archive', id = item['id'], start = item['startDate'], end = item['endDate'])
                menus = [('Přidat nahrávku', 'RunPlugin(plugin://' + plugin_id + '?action=add_recording&id=' + str(item['id']) + ')')]
                list_item.addContextMenuItems(menus)       
                xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
        xbmcplugin.endOfDirectory(_handle)
    else:
        xbmcgui.Dialog().notification('O2TV','Nic nenalezeno', xbmcgui.NOTIFICATION_INFO, 3000)

def save_search_history(query):
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile')) 
    max_history = int(addon.getSetting('search_history'))
    cnt = 0
    history = []
    filename = addon_userdata_dir + 'search_history.txt'
    try:
        with openfile(filename, 'r') as file:
            for line in file:
                item = line[:-1]
                history.append(item)
    except IOError:
        history = []
    history.insert(0,query)
    with openfile(filename, 'w') as file:
        for item  in history:
            cnt = cnt + 1
            if cnt <= max_history:
                file.write('%s\n' % item)

def load_search_history():
    history = []
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile')) 
    filename = addon_userdata_dir + 'search_history.txt'
    try:
        with openfile(filename, 'r') as file:
            for line in file:
                item = line[:-1]
                history.append(item)
    except IOError:
        history = []
    return history

def delete_search(query):
    addon = xbmcaddon.Addon()
    addon_userdata_dir = translatePath(addon.getAddonInfo('profile')) 
    filename = addon_userdata_dir + 'search_history.txt'
    history = load_search_history()
    for item in history:
        if item == query:
            history.remove(item)
    try:
        with openfile(filename, 'w') as file:
            for item in history:
                file.write('%s\n' % item)
    except IOError:
        pass
    xbmc.executebuiltin('Container.Refresh')

