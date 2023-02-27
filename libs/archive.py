# -*- coding: utf-8 -*-
import os
import sys
import xbmcgui
import xbmcplugin
import xbmcaddon

from datetime import date, datetime, timedelta
import time

from libs.utils import get_url, day_translation, day_translation_short, plugin_id
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
        url = get_url(action='list_archive_days', id = channels_list[number]['id'], label = label + ' / ' + channels_list[number]['name'])  
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
            den = day_translation[day.strftime('%w')] + ' ' + day.strftime('%d.%m.%Y')
        list_item = xbmcgui.ListItem(label = den)
        url = get_url(action='list_program', id = id, day_min = i, label = label + ' / ' + den_label)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def list_program(id, day_min, label):
    addon = xbmcaddon.Addon()
    icons_dir = os.path.join(addon.getAddonInfo('path'), 'resources','images')

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

    if int(day_min) < 7:
        list_item = xbmcgui.ListItem(label='Předchozí den')
        day = date.today() - timedelta(days = int(day_min) + 1)
        den_label = day_translation_short[day.strftime('%w')] + ' ' + day.strftime('%d.%m')
        url = get_url(action='list_program', id = id, day_min = int(day_min) + 1, label = label + ' / ' + den_label)  
        list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'previous_arrow.png'), 'icon' : os.path.join(icons_dir , 'previous_arrow.png') })
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    for key in sorted(epg.keys(), reverse = False):
        if int(epg[key]['endts']) > int(time.mktime(datetime.now().timetuple()))-60*60*24*7:
            list_item = xbmcgui.ListItem(label = day_translation_short[datetime.fromtimestamp(epg[key]['startts']).strftime('%w')] + ' ' + datetime.fromtimestamp(epg[key]['startts']).strftime('%d.%m %H:%M') + ' - ' + datetime.fromtimestamp(epg[key]['endts']).strftime('%H:%M') + ' | ' + epg[key]['title'])
            list_item = epg_listitem(list_item = list_item, epg = epg[key], logo = '')
            menus = [('Přidat nahrávku', 'RunPlugin(plugin://' + plugin_id + '?action=add_recording&id=' + str(epg[key]['id']) + ')')]
            list_item.addContextMenuItems(menus)       
            list_item.setProperty('IsPlayable', 'true')
            list_item.setContentLookup(False)          
            url = get_url(action='play_archive', id = epg[key]['id'], channel_id = epg[key]['channel_id'], startts = epg[key]['startts']-1, endts = epg[key]['endts'])
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    if int(day_min) > 0:
        list_item = xbmcgui.ListItem(label='Následující den')
        day = date.today() - timedelta(days = int(day_min) - 1)
        den_label = day_translation_short[day.strftime('%w')] + ' ' + day.strftime('%d.%m')
        url = get_url(action='list_program', id = id, day_min = int(day_min) - 1, label = label + ' / ' + den_label)  
        list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'next_arrow.png'), 'icon' : os.path.join(icons_dir , 'next_arrow.png') })
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle, updateListing = True, cacheToDisc = False)