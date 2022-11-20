# -*- coding: utf-8 -*-
import sys

import xbmc
import xbmcgui
import xbmcplugin

from datetime import date, datetime, timedelta
import time

from libs.session import Session
from libs.channels import Channels
from libs.epg import epg_api, epg_listitem, get_channel_epg
from libs.o2tv import O2API
from libs.utils import get_url, plugin_id, encode, decode, day_translation, day_translation_short

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def list_recordings(label):
    xbmcplugin.setPluginCategory(_handle, label)

    list_item = xbmcgui.ListItem(label='Plánování nahrávek')
    url = get_url(action='list_planning_recordings', label = label + ' / ' + 'Plánování')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    list_item = xbmcgui.ListItem(label='Naplánované nahrávky')
    url = get_url(action='list_future_recordings', label = label + ' / ' + 'Naplánované nahrávky')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    recording_ids = {}
    session = Session()
    post = {"language":"ces","ks":session.ks,"responseProfile":{"objectType":"KalturaOnDemandResponseProfile","relatedProfiles":[{"objectType":"KalturaDetachedResponseProfile","name":"group_result","filter":{"objectType":"KalturaAggregationCountFilter"}}]},"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_DESC","kSql":"(and asset_type='recording' start_date <'0' end_date < '-900')","groupBy":[{"objectType":"KalturaAssetMetaOrTagGroupBy","value":"SeriesID"}],"groupingOptionEqual":"Include"},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":"1.16.1-PC","apiVersion":"5.4.0"}
    o2api = O2API()
    data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/asset/action/list?format=1&clientTag=1.16.1-PC', data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaAssetListResponse':
        xbmcgui.Dialog().notification('O2TV','Problém při stažení EPG', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit() 
    if 'objects' in data['result']:
        for item in data['result']['objects']:
            recording_ids.update({item['id'] : item['recordingId']})
    channels = Channels()
    channels_list = channels.get_channels_list('id', visible_filter = False)            
    epg = epg_api(post = post, key = 'startts')
    for key in sorted(epg.keys(), reverse = False):
        list_item = xbmcgui.ListItem(label = epg[key]['title'] + ' (' + channels_list[epg[key]['channel_id']]['name'] + ' | ' + decode(day_translation_short[datetime.fromtimestamp(epg[key]['startts']).strftime('%w')]) + ' ' + datetime.fromtimestamp(epg[key]['startts']).strftime('%d.%m %H:%M') + ' - ' + datetime.fromtimestamp(epg[key]['endts']).strftime('%H:%M') + ')')

        list_item = epg_listitem(list_item = list_item, epg = epg[key], logo = '')
        list_item.setProperty('IsPlayable', 'true')
        list_item.setContentLookup(False)          
        menus = [('Smazat nahrávku', 'RunPlugin(plugin://' + plugin_id + '?action=delete_recording&id=' + str(recording_ids[epg[key]['id']]) + ')')]
        list_item.addContextMenuItems(menus)         
        url = get_url(action='play_recording', id = epg[key]['id'], start = epg[key]['startts'], end = epg[key]['endts'])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def delete_recording(id):
    id = int(id)
    session = Session()
    post = {"language":"ces","ks":session.ks,"id":id,"clientTag":"1.16.1-PC","apiVersion":"5.4.0"}
    o2api = O2API()
    data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/recording/action/delete?format=1&clientTag=1.16.1-PC', data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or not 'status' in data['result'] or data['result']['status'] != 'DELETED':
        xbmcgui.Dialog().notification('O2TV', 'Problém se smazáním nahrávky', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        xbmcgui.Dialog().notification('O2TV', 'Nahrávka smazána', xbmcgui.NOTIFICATION_INFO, 5000)
    xbmc.executebuiltin('Container.Refresh')

def delete_future_recording(id):
    id = int(id)
    session = Session()
    post = {"language":"ces","ks":session.ks,"id":id,"clientTag":"1.16.1-PC","apiVersion":"5.4.0"}
    o2api = O2API()
    data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/recording/action/cancel?format=1&clientTag=1.16.1-PC', data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or not 'status' in data['result'] or data['result']['status'] != 'CANCELED':
        xbmcgui.Dialog().notification('O2TV', 'Problém se smazáním nahrávky', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        xbmcgui.Dialog().notification('O2TV', 'Nahrávka smazána', xbmcgui.NOTIFICATION_INFO, 5000)
    xbmc.executebuiltin('Container.Refresh')

def list_future_recordings(label):
    xbmcplugin.setPluginCategory(_handle, label)
    recording_ids = {}
    session = Session()
    o2api = O2API()
    post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaScheduledRecordingProgramFilter","orderBy":"START_DATE_ASC","recordingTypeEqual":"single"},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":"1.16.1-PC","apiVersion":"5.4.0"}
    data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/asset/action/list?format=1&clientTag=1.16.1-PC', data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaAssetListResponse':
        xbmcgui.Dialog().notification('O2TV','Problém při stažení EPG', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit() 
    if 'objects' in data['result']:
        for item in data['result']['objects']:
            recording_ids.update({item['id'] : item['recordingId']})
    epg = epg_api(post = post, key = 'startts')
    for key in sorted(epg.keys(), reverse = False):
        list_item = xbmcgui.ListItem(label = epg[key]['title'])
        list_item = epg_listitem(list_item = list_item, epg = epg[key], logo = '')
        list_item.setProperty('IsPlayable', 'true')
        list_item.setContentLookup(False)          
        menus = [('Smazat nahrávku', 'RunPlugin(plugin://' + plugin_id + '?action=delete_future_recording&id=' + str(recording_ids[epg[key]['id']]) + ')')]
        list_item.addContextMenuItems(menus)         
        url = get_url(action='play_recording', id = epg[key]['id'], start = epg[key]['startts'], end = epg[key]['endts'])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def list_planning_recordings(label):
    xbmcplugin.setPluginCategory(_handle, label)
    channels = Channels()
    channels_list = channels.get_channels_list('channel_number')
    for number in sorted(channels_list.keys()):  
        list_item = xbmcgui.ListItem(label = channels_list[number]['name'])
        list_item.setArt({'thumb': channels_list[number]['logo'], 'icon': channels_list[number]['logo']})
        url = get_url(action='list_rec_days', id = channels_list[number]['id'], label = label + ' / ' + encode(channels_list[number]['name']))  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)
    
def list_rec_days(id, label):
    xbmcplugin.setPluginCategory(_handle, label)
    for i in range (8):
        day = date.today() + timedelta(days = i)
        if i == 0:
            den_label = 'Dnes'
            den = 'Dnes'
        elif i == 1:
            den_label = 'Zítra'
            den = 'Zítra'
        else:
            den_label = day_translation_short[day.strftime('%w')] + ' ' + day.strftime('%d.%m')
            den = decode(day_translation[day.strftime('%w')]) + ' ' + day.strftime('%d.%m.%Y')
        list_item = xbmcgui.ListItem(label=den)
        url = get_url(action='future_program', id = id, day = i, label = label + ' / ' + den_label)  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)

def future_program(id, day, label):
    label = label.replace('Nahrávky / Plánování /', '')
    xbmcplugin.setPluginCategory(_handle, label)
    id = int(id)
    today_date = datetime.today() 
    today_start_ts = int(time.mktime(datetime(today_date.year, today_date.month, today_date.day) .timetuple()))
    today_end_ts = today_start_ts + 60*60*24 -1
    if int(day) == 0:
        from_ts = int(time.mktime(datetime.now().timetuple()))
        to_ts = today_end_ts
    else:
        from_ts = today_start_ts + int(day)*60*60*24
        to_ts = today_end_ts + int(day)*60*60*24 
    epg = get_channel_epg(id, from_ts, to_ts)
    for key in sorted(epg.keys()):
        start = epg[key]['startts']
        end = epg[key]['endts']
        list_item = xbmcgui.ListItem(label= decode(day_translation_short[datetime.fromtimestamp(start).strftime('%w')]) + ' ' + datetime.fromtimestamp(start).strftime('%d.%m %H:%M') + ' - ' + datetime.fromtimestamp(end).strftime('%H:%M') + ' | ' + epg[key]['title'])
        list_item = epg_listitem(list_item, epg[key], '')
        list_item.setProperty('IsPlayable', 'false')
        list_item.addContextMenuItems([('Přidat nahrávku', 'RunPlugin(plugin://' + plugin_id + '?action=add_recording&id=' + str(epg[key]['id']) + ')',)])       
        url = get_url(action='add_recording', id = epg[key]['id'])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle)

def add_recording(id):
    id = int(id)
    session = Session()
    o2api = O2API()
    post = {"language":"ces","ks":session.ks,"recording":{"objectType":"KalturaRecording","assetId":id},"clientTag":"1.16.1-PC","apiVersion":"5.4.0"}
    data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/recording/action/add?format=1&clientTag=1.16.1-PC', data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or not 'status' in data['result'] or (data['result']['status'] != 'SCHEDULED' and data['result']['status'] != 'RECORDED'):
        xbmcgui.Dialog().notification('O2TV', 'Problém s přidáním nahrávky', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        xbmcgui.Dialog().notification('O2TV', 'Nahrávka přidána', xbmcgui.NOTIFICATION_INFO, 5000)
    