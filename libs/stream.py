# -*- coding: utf-8 -*-
import sys
import xbmcgui
import xbmcplugin

from datetime import datetime
import time

from libs.session import Session
from libs.o2tv import O2API, o2tv_list_api
from libs.epg import get_channel_epg
from libs.utils import clientTag, apiVersion, partnerId

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def play_catchup(id, start_ts, end_ts):
    start_ts = int(start_ts)
    end_ts = int(end_ts)
    epg = get_channel_epg(id = id, from_ts = start_ts, to_ts = end_ts + 60*60*12)
    if start_ts in epg:
        if epg[start_ts]['endts'] > int(time.mktime(datetime.now().timetuple()))-10:
            play_startover(id = epg[start_ts]['id'])
        else:
            play_archive(id = epg[start_ts]['id'], channel_id = id, startts = epg[start_ts]['startts'], endts = epg[start_ts]['endts'])
    else:
        play_live(id = id)

def play_startover(id):
    session = Session()
    post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"epg_internal","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"epg","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"START_OVER","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":partnerId}    
    play_stream(post)

def play_live(id):
    session = Session()
    post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"media","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"media","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"PLAYBACK","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":partnerId}
    play_stream(post)

def play_archive(id, channel_id, startts, endts):
    session = Session()
    o2api = O2API()
    no_remove = False

    # post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"epg_internal","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"epg","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"START_OVER","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":partnerId}    
    # play_stream(post)

    post = {"language":"ces","ks":session.ks,"responseProfile":{"objectType":"KalturaOnDemandResponseProfile","relatedProfiles":[{"objectType":"KalturaDetachedResponseProfile","name":"group_result","filter":{"objectType":"KalturaAggregationCountFilter"}}]},"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_DESC","kSql":"(and asset_type='recording' start_date <'0' end_date < '-900')","groupBy":[{"objectType":"KalturaAssetMetaOrTagGroupBy","value":"SeriesID"}],"groupingOptionEqual":"Include"},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
    result = o2tv_list_api(post = post, silent = True)
    for item in result:
        if int(item['id']) == int(id):
            no_remove = True
    post = {"language":"ces","ks":session.ks,"recording":{"objectType":"KalturaRecording","assetId":id},"clientTag":clientTag,"apiVersion":apiVersion}
    data = o2api.call_o2_api(url = 'https://' + partnerId + '.frp1.ott.kaltura.com/api_v3/service/recording/action/add?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or not 'status' in data['result'] or data['result']['status'] != 'RECORDED':
        post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"epg_internal","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"epg","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"CATCHUP","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":partnerId}
        play_stream(post)
    else:
        recording_id = data['result']['id']
        play_recording(recording_id)
        if no_remove == False:
            post = {"language":"ces","ks":session.ks,"id":recording_id,"clientTag":clientTag,"apiVersion":apiVersion}
            data = o2api.call_o2_api(url = 'https://' + partnerId + '.frp1.ott.kaltura.com/api_v3/service/recording/action/delete?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
            
def play_recording(id):
    session = Session()
    post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"npvr","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"recording","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"PLAYBACK","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":partnerId}
    play_stream(post)

def play_stream(post):
    o2api = O2API()
    data = o2api.call_o2_api(url = 'https://' + partnerId + '.frp1.ott.kaltura.com/api_v3/service/multirequest', data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or len(data['result']) == 0 or not 'sources' in data['result'][1]:
        xbmcgui.Dialog().notification('O2TV','Problém při přehrání', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        if len(data['result'][1]['sources']) > 0:
            urls = {}
            for stream in data['result'][1]['sources']:
                license = None
                for drm in stream['drm']:
                    if drm['scheme'] == 'WIDEVINE_CENC':
                        license = drm['licenseURL']
                urls.update({stream['type'] : { 'url' : stream['url'], 'license' : license}})

            if 'DASH_WV' in urls and 1 == 0:
                url = urls['DASH_WV']['url']
                list_item = xbmcgui.ListItem(path = url)
                # list_item.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')
                list_item.setProperty('inputstream', 'inputstream.adaptive')
                list_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                list_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                from urllib.parse import urlencode
                list_item.setProperty('inputstream.adaptive.license_key', urls['DASH_WV']['license'] + '|' + urlencode(o2api.headers) + '|R{SSM}|')                
                list_item.setMimeType('application/dash+xml')
                list_item.setContentLookup(False)       
                xbmcplugin.setResolvedUrl(_handle, True, list_item)

            if 'DASH' in urls:
                url = urls['DASH']['url']
                list_item = xbmcgui.ListItem(path = url)
                # list_item.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')
                list_item.setProperty('inputstream', 'inputstream.adaptive')
                list_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                list_item.setMimeType('application/dash+xml')
                list_item.setContentLookup(False)       
                xbmcplugin.setResolvedUrl(_handle, True, list_item)
            else:
                xbmcgui.Dialog().notification('O2TV','Problém při přehrání', xbmcgui.NOTIFICATION_ERROR, 5000)
        elif 'messages' in data['result'][1] and len(data['result'][1]['messages']) > 0 and data['result'][1]['messages'][0]['code'] == 'ConcurrencyLimitation' :
            xbmcgui.Dialog().notification('O2TV','Překročený limit přehrávání', xbmcgui.NOTIFICATION_ERROR, 5000)
        else:
            xbmcgui.Dialog().notification('O2TV','Problém při přehrání', xbmcgui.NOTIFICATION_ERROR, 5000)
