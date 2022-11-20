# -*- coding: utf-8 -*-
import sys
import xbmcgui
import xbmcplugin
    
from datetime import date, datetime, timedelta
import time

from libs.utils import get_url, decode, encode, day_translation, day_translation_short, plugin_id
from libs.channels import Channels 
from libs.epg import get_channel_epg, epg_listitem

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_archive(label):
    xbmcplugin.setPluginCategory(_handle, label)
    channels = Channels()
    channels_list = channels.get_channels_list('channel_number')
    for number in sorted(channels_list.keys()):  
        list_item = xbmcgui.ListItem(label=channels_list[number]['name'])
        list_item.setArt({'thumb': channels_list[number]['logo'], 'icon': channels_list[number]['logo']})
        url = get_url(action='list_archive_days', id = encode(channels_list[number]['id']), label = encode(label + ' / ' + channels_list[number]['name']))  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def list_archive_days(id, label):
    xbmcplugin.setPluginCategory(_handle, label)
    for i in range (8):
        day = date.today() - timedelta(days = i)
        if i == 0:
            den_label = 'Dnes'
            den = 'Dnes'
        elif i == 1:
            den_label = 'Včera'
            den = 'Včera'
        else:
            den_label = day_translation_short[day.strftime('%w')] + ' ' + day.strftime('%d.%m')
            den = decode(day_translation[day.strftime('%w')]) + ' ' + day.strftime('%d.%m.%Y')
        list_item = xbmcgui.ListItem(label = den)
        url = get_url(action='list_program', id = id, day_min = i, label = label + ' / ' + den_label)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def list_program(id, day_min, label):
    label = label.replace('Archiv /','')
    xbmcplugin.setPluginCategory(_handle, label)
    today_date = datetime.today() 
    today_start_ts = int(time.mktime(datetime(today_date.year, today_date.month, today_date.day) .timetuple()))
    today_end_ts = today_start_ts + 60*60*24 -1
    if int(day_min) == 0:
        from_ts = today_start_ts - int(day_min)*60*60*24
        to_ts = int(time.mktime(datetime.now().timetuple()))
    else:
        from_ts = today_start_ts - int(day_min)*60*60*24
        to_ts = today_end_ts - int(day_min)*60*60*24
    epg = {}
    epg = get_channel_epg(id, from_ts, to_ts)
    for key in sorted(epg.keys(), reverse = False):
        if int(epg[key]['endts']) > int(time.mktime(datetime.now().timetuple()))-60*60*24*7:
            list_item = xbmcgui.ListItem(label = decode(day_translation_short[datetime.fromtimestamp(epg[key]['startts']).strftime('%w')]) + ' ' + datetime.fromtimestamp(epg[key]['startts']).strftime('%d.%m %H:%M') + ' - ' + datetime.fromtimestamp(epg[key]['endts']).strftime('%H:%M') + ' | ' + epg[key]['title'])
            list_item = epg_listitem(list_item = list_item, epg = epg[key], logo = '')
            menus = [('Přidat nahrávku', 'RunPlugin(plugin://' + plugin_id + '?action=add_recording&id=' + str(epg[key]['id']) + ')')]
            list_item.addContextMenuItems(menus)       
            list_item.setProperty('IsPlayable', 'true')
            list_item.setContentLookup(False)          
            url = get_url(action='play_archive', id = epg[key]['id'], start = epg[key]['startts'], end = epg[key]['endts'])
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)