# -*- coding: utf-8 -*-
import sys
import xbmcgui
import xbmcplugin

from datetime import datetime
import time

from libs.session import Session
from libs.o2tv import O2API
from libs.epg import get_channel_epg

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
            play_archive(id = epg[start_ts]['id'])
    else:
        play_live(id = id)

def play_startover(id):
    session = Session()
    post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"epg_internal","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"epg","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"START_OVER","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":3201}    
    play_stream(post)

def play_live(id):
    session = Session()
    post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"media","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"media","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"PLAYBACK","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":3201}
    play_stream(post)

def play_archive(id):
    session = Session()
    post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"epg_internal","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"epg","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"CATCHUP","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":3201}
    play_stream(post)

def play_recording(id):
    session = Session()
    post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"npvr","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"recording","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"PLAYBACK","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":"djJ8MzIwMXwfL4dq7dGdAjIGcffiB5xF3EJa-owKpoaAkSaoEXZEKA0zeK1OIUYS9wKW1bAfiYiAA3NR4iK0djikEiPi1vHAIOBMG6qK0nvo_3bTjnl4lGRx-6TI-HHPybgwbp3rZ9LY-UF_qg8nHFHu9jbIHPLKZ_64-bj9JYYAUrECTCBfHac8ZN4VvBSvb9_qZdl7VsuCeUrTufWFLGbTLsZzzAXeKeB--iuVbQiTVvYCmIjFsL2irzZC1GcSJm2QXlYYKmpf5X6nhS0ofG9yQ5Q_62QZSNCjuUEpoul8Cj7E2YQPX8lBon6b18N11SzPGfrjulVDVZLb59StJN9vFuD3mgPq3mZKpHYjRyNnv1Q8OpPd8XrliQHNT3jTv09t3ExQ5XwUimcwJvk7IpD5zpKlIHrO","partnerId":3201}
    play_stream(post)

def play_stream(post):
    o2api = O2API()
    data = o2api.call_o2_api(url = 'https://3201.frp1.ott.kaltura.com/api_v3/service/multirequest', data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or len(data['result']) == 0 or not 'sources' in data['result'][1]:
        xbmcgui.Dialog().notification('O2TV','Problém při přihrání', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        if len(data['result'][1]['sources']) > 0:
            url = data['result'][1]['sources'][1]['url']
            list_item = xbmcgui.ListItem(path = url)
            list_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            list_item.setProperty('inputstream', 'inputstream.adaptive')
            list_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            list_item.setMimeType('application/dash+xml')
            list_item.setContentLookup(False)       
            xbmcplugin.setResolvedUrl(_handle, True, list_item)
        elif 'messages' in data['result'][1] and len(data['result'][1]['messages']) > 0 and data['result'][1]['messages'][0]['code'] == 'ConcurrencyLimitation' :
            xbmcgui.Dialog().notification('O2TV','Překročený limit přehrávání', xbmcgui.NOTIFICATION_ERROR, 5000)
        else:
            xbmcgui.Dialog().notification('O2TV','Problém při přihrání', xbmcgui.NOTIFICATION_ERROR, 5000)
