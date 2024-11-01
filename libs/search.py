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
import json

from libs.utils import get_url, plugin_id, day_translation_short, clientTag, apiVersion, encode
from libs.session import Session
from libs.channels import Channels
from libs.epg import epg_listitem, epg_api

_handle = int(sys.argv[1])

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
    channels = Channels()
    channels_list = channels.get_channels_list(visible_filter = True)
    post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaChannelFilter","orderBy":"NAME_ASC","kSql":"(and name^'" + query +  "')","idEqual":355960},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
    epg = epg_api(post = post, key = 'startts_channel_number')
    if len(epg) > 0:
        for key in sorted(epg.keys(), reverse = True):
            if epg[key]['channel_id'] in channels_list:                
                list_item = xbmcgui.ListItem(label = encode(epg[key]['title']) + ' (' + encode(channels_list[epg[key]['channel_id']]['name']) + ' | ' + day_translation_short[datetime.fromtimestamp(epg[key]['startts']).strftime('%w')] + ' ' + datetime.fromtimestamp(epg[key]['startts']).strftime('%d.%m. %H:%M') + ' - ' + datetime.fromtimestamp(epg[key]['endts']).strftime('%H:%M') + ')')
                list_item = epg_listitem(list_item = list_item, epg = epg[key], logo = channels_list[epg[key]['channel_id']]['logo'])
                list_item.setProperty('IsPlayable', 'true')
                list_item.setContentLookup(False)          
                url = get_url(action='play_archive', id = epg[key]['id'], epg = json.dumps(epg[key]), channel_id = epg[key]['channel_id'], startts = epg[key]['startts'], endts = epg[key]['endts'])
                menus = [('Přidat nahrávku', 'RunPlugin(plugin://' + plugin_id + '?action=add_recording&id=' + str(epg[key]['id']) + ')')]
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
        with open(filename, 'r') as file:
            for line in file:
                item = line[:-1]
                history.append(item)
    except IOError:
        history = []
    history.insert(0,query)
    with open(filename, 'w') as file:
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
        with open(filename, 'r') as file:
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
        with open(filename, 'w') as file:
            for item in history:
                file.write('%s\n' % item)
    except IOError:
        pass
    xbmc.executebuiltin('Container.Refresh')

