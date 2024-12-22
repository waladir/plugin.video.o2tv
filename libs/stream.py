# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import ssl
from xml.dom import minidom
try:
    from urllib2 import urlopen, Request
except ImportError:
    from urllib.request import urlopen, Request

from datetime import datetime
import time

from libs.session import Session
from libs.channels import Channels
from libs.o2tv import O2API, o2tv_list_api
from libs.epg import get_channel_epg, get_live_epg, epg_api
from libs.utils import clientTag, apiVersion, get_partnerId, PY2

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def play_catchup(id, start_ts, end_ts):
    start_ts = int(start_ts)
    end_ts = int(end_ts)
    epg = get_channel_epg(id = id, from_ts = start_ts, to_ts = end_ts + 60*60*12)
    if start_ts in epg:
        if epg[start_ts]['endts'] > int(time.mktime(datetime.now().timetuple()))-10:
            play_startover(id = epg[start_ts]['id'], epg = epg[start_ts], channel_id = id, md_dialog = True)
        else:
            play_archive(id = epg[start_ts]['id'], epg = epg[start_ts], channel_id = id, startts = epg[start_ts]['startts'], endts = epg[start_ts]['endts'])
    else:
        play_live(id)

def play_startover(id, epg, channel_id, md_dialog):
    session = Session()
    if md_dialog == True and epg['md'] is not None:
        items = []
        ids = []
        epgs = []
        post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_ASC","kSql":"(and IsMosaicEvent='1' MosaicInfo='mosaic' (or externalId='" + str(epg['md']) + "'))"},"pager":{"objectType":"KalturaFilterPager","pageSize":200,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
        md_epg = o2tv_list_api(post = post, type = 'multidimenze', nolog = True)
        for md_epg_item in md_epg:
            md_ids = []
            if 'MosaicChannelsInfo' in md_epg_item['tags']:
                for mditem in md_epg_item['tags']['MosaicChannelsInfo']['objects']:
                    if 'ProgramExternalID' in mditem['value']:
                        md_ids.append(mditem['value'].split('ProgramExternalID=')[1])
                for md_id in md_ids:
                    post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_ASC","kSql":"(or externalId='" + str(md_id) + "')"},"pager":{"objectType":"KalturaFilterPager","pageSize":200,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
                    epg_md_item = o2tv_list_api(post = post, type = 'multidimenze', nolog = True)
                    if len(epg) > 0:
                        item = epg_md_item[0]
                        epg = epg_api(post,'id')
                        epgs.append(epg[item['id']])
                        items.append(item['name'])
                        ids.append(item['id'])
        if len(items) > 0:
            response = xbmcgui.Dialog().select(heading = 'Multidimenze - výběr streamu', list = items, preselect = 0)
            if response < 0:
                return
            epg = epgs[response]
            id = ids[response]
    post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"epg_internal","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"epg","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"START_OVER","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":get_partnerId()}    
    play_stream(post, channel_id)

def play_live(id):
    session = Session()
    epg_id = -1
    epg = get_live_epg()
    if int(id) in epg:
        epg = epg[int(id)]
    else:
        epg = {}
    if 'id' in epg:
        epg_id = epg['id']
    if 'md' in epg and epg['md'] is not None:
        items = []
        ids = []
        post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_ASC","kSql":"(and IsMosaicEvent='1' MosaicInfo='mosaic' (or externalId='" + str(epg['md']) + "'))"},"pager":{"objectType":"KalturaFilterPager","pageSize":200,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
        md_epg = o2tv_list_api(post = post, type = 'multidimenze', nolog = True)
        for md_epg_item in md_epg:
            md_ids = []
            md_titles = {}
            if 'MosaicChannelsInfo' in md_epg_item['tags']:
                for mditem in md_epg_item['tags']['MosaicChannelsInfo']['objects']:
                    if 'ChannelExternalId' in mditem['value']:
                        channel = mditem['value'].split('ChannelExternalId=')[1].split(',')[0]
                        md_ids.append(channel)
                        md_titles.update({channel : mditem['value'].split('Title=')[1].split(',')[0]})
                for id in md_ids:
                    post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_ASC","kSql":"(or externalId='" + str(id) + "')"},"pager":{"objectType":"KalturaFilterPager","pageSize":200,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
                    epg = o2tv_list_api(post = post, type = 'multidimenze', nolog = True)
                    if len(epg) > 0:
                        item = epg[0]
                        items.append(md_titles[id])
                        ids.append(item['id'])
        if len(items) > 0:
            response = xbmcgui.Dialog().select(heading = 'Multidimenze - výběr streamu', list = items, preselect = 0)
            if response < 0:
                return
            id = ids[response]
            epg = get_live_epg()[int(id)]
            if 'id' in epg:
                epg_id = epg['id']
    if epg_id > 0:
        post = {"1":{"service":"asset","action":"get","id":epg_id,"assetReferenceType":"epg_internal","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":epg_id,"assetType":"epg","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"START_OVER","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":get_partnerId()}    
    else:
        post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"media","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"media","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"PLAYBACK","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":get_partnerId()}
    play_stream(post, id)

def play_archive(id, epg, channel_id, startts, endts):
    session = Session()
    o2api = O2API()
    no_remove = False
    if epg['md'] is not None:
        items = []
        ids = []
        epgs = []
        post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_ASC","kSql":"(and IsMosaicEvent='1' MosaicInfo='mosaic' (or externalId='" + str(epg['md']) + "'))"},"pager":{"objectType":"KalturaFilterPager","pageSize":200,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
        md_epg = o2tv_list_api(post = post, type = 'multidimenze', nolog = True)
        for md_epg_item in md_epg:
            md_ids = []
            if 'MosaicChannelsInfo' in md_epg_item['tags']:
                for mditem in md_epg_item['tags']['MosaicChannelsInfo']['objects']:
                    if 'ProgramExternalID' in mditem['value']:
                        md_ids.append(mditem['value'].split('ProgramExternalID=')[1])
                for md_id in md_ids:
                    post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_ASC","kSql":"(or externalId='" + str(md_id) + "')"},"pager":{"objectType":"KalturaFilterPager","pageSize":200,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
                    epg_md_item = o2tv_list_api(post = post, type = 'multidimenze', nolog = True)
                    if len(epg) > 0:
                        item = epg_md_item[0]
                        epg = epg_api(post,'id')
                        epgs.append(epg[item['id']])
                        items.append(item['name'])
                        ids.append(item['id'])
        if len(items) > 0:
            response = xbmcgui.Dialog().select(heading = 'Multidimenze - výběr streamu', list = items, preselect = 0)
            if response < 0:
                return
            epg = epgs[response]
            id = ids[response]

    # post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"epg_internal","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"epg","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"START_OVER","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":partnerId}    
    # play_stream(post)
    if epg['endts'] > int(time.mktime(datetime.now().timetuple()))-10:
        play_startover(id = epg['id'], epg = epg, channel_id = channel_id, md_dialog = False)
    else:
        post = {"language":"ces","ks":session.ks,"responseProfile":{"objectType":"KalturaOnDemandResponseProfile","relatedProfiles":[{"objectType":"KalturaDetachedResponseProfile","name":"group_result","filter":{"objectType":"KalturaAggregationCountFilter"}}]},"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_DESC","kSql":"(and asset_type='recording' start_date <'0' end_date < '-900')","groupBy":[{"objectType":"KalturaAssetMetaOrTagGroupBy","value":"SeriesID"}],"groupingOptionEqual":"Include"},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
        result = o2tv_list_api(post = post, type = 'archiv - nahrávky', silent = True)
        for item in result:
            if int(item['id']) == int(id):
                no_remove = True
        post = {"language":"ces","ks":session.ks,"recording":{"objectType":"KalturaRecording","assetId":id},"clientTag":clientTag,"apiVersion":apiVersion}
        data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/recording/action/add?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or not 'status' in data['result'] or data['result']['status'] != 'RECORDED':
            post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"epg_internal","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"epg","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"CATCHUP","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":get_partnerId()}
            play_stream(post, channel_id)
        else:
            recording_id = data['result']['id']
            play_recording(recording_id, channel_id)
            if no_remove == False:
                post = {"language":"ces","ks":session.ks,"id":recording_id,"clientTag":clientTag,"apiVersion":apiVersion}
                data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/recording/action/delete?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
            
def play_recording(id, channel_id):
    session = Session()
    post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"npvr","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"recording","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"PLAYBACK","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":get_partnerId()}
    play_stream(post, channel_id)

def play_stream(post, channel_id):
    addon = xbmcaddon.Addon()
    o2api = O2API()
    err = False
    if channel_id is not None:
        channels = Channels()
        channel_id = int(channel_id)
        channels_list = channels.get_channels_list('id')
        if channel_id in channels_list and channels_list[channel_id]['adult'] == True:
            session = Session()
            pin_post = {"language":"ces","ks":session.ks,"pin":str(addon.getSetting('pin')),"type":"parental","clientTag":clientTag,"apiVersion":apiVersion}
            data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/pin/action/validate?format=1&clientTag=' + clientTag, data = pin_post, headers = o2api.headers)
            if 'err' in data or not 'result' in data or data['result'] != True:
                err = True
            if err == True:
                err = False
                pin = xbmcgui.Dialog().numeric(type = 0, heading = 'Zadejte PIN', bHiddenInput = True)
                if len(str(pin)) > 0:
                    pin_post = {"language":"ces","ks":session.ks,"pin":str(pin),"type":"parental","clientTag":clientTag,"apiVersion":apiVersion}
                    data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/pin/action/validate?format=1&clientTag=' + clientTag, data = pin_post, headers = o2api.headers)
                    if 'err' in data or not 'result' in data or data['result'] != True:
                        xbmcgui.Dialog().notification('O2TV','Nesprávný PIN', xbmcgui.NOTIFICATION_ERROR, 5000)
                        err = True
                else:
                    xbmcgui.Dialog().notification('O2TV','Nezadaný PIN', xbmcgui.NOTIFICATION_ERROR, 5000)
                    err = True
    if err == False:
        data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/multirequest', data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or len(data['result']) == 0 or not 'sources' in data['result'][1]:
            if channel_id is not None and 'error' in data['result'][1] and 'message' and data['result'][1]['error'] and data['result'][1]['error']['message'] == 'ProgramStartOverNotEnabled' and post['2']['contextDataParams']['context'] == 'START_OVER':
                session = Session()
                post = {"1":{"service":"asset","action":"get","id":channel_id,"assetReferenceType":"media","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":channel_id,"assetType":"media","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"PLAYBACK","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":get_partnerId()}
                data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/multirequest', data = post, headers = o2api.headers)
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

                url = ''
                widevine = False
                if addon.getSetting('service') == 'o2tv.sk':
                    widevine = True
                if widevine == True:
                    if 'DASH_WV' in urls:
                        url = urls['DASH_WV']['url']
                else:
                    if 'DASH' in urls:
                        url = urls['DASH']['url']
                if len(url) > 0:
                    context=ssl.create_default_context()
                    context.set_ciphers('DEFAULT')
                    request = Request(url = url , data = None)
                    if addon.getSetting('log_request_url') == 'true':
                        xbmc.log('O2TV > ' + str(url))
                    response = urlopen(request)
                    if addon.getSetting('log_response') == 'true':
                        xbmc.log('O2TV > ' + str(response.status))
                    mpd = response.geturl()

                    list_item = xbmcgui.ListItem(path = mpd)
                    list_item.setProperty('inputstream', 'inputstream.adaptive')
                    if PY2:
                        list_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
                    list_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                    if widevine == True:
                        list_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                        from urllib.parse import urlencode
                        list_item.setProperty('inputstream.adaptive.license_key', urls['DASH_WV']['license'] + '|' + urlencode(o2api.headers) + '|R{SSM}|')                
                    list_item.setMimeType('application/dash+xml')
                    list_item.setContentLookup(False)       
                    xbmcplugin.setResolvedUrl(_handle, True, list_item)
                    keepalive = get_keepalive_url(mpd, response)
                    if keepalive is not None:
                        time.sleep(3)
                        while(xbmc.Player().isPlaying()):
                            request = Request(url = keepalive , data = None)
                            if addon.getSetting('log_request_url') == 'true':
                                xbmc.log('O2TV > ' + str(keepalive))
                            response = urlopen(request)
                            if addon.getSetting('log_response') == 'true':
                                xbmc.log('O2TV > ' + str(response.status))
                            time.sleep(5)
                else:
                    xbmcgui.Dialog().notification('O2TV','Problém při přehrání', xbmcgui.NOTIFICATION_ERROR, 5000)
            elif 'messages' in data['result'][1] and len(data['result'][1]['messages']) > 0 and data['result'][1]['messages'][0]['code'] == 'ConcurrencyLimitation' :
                xbmcgui.Dialog().notification('O2TV','Překročený limit přehrávání', xbmcgui.NOTIFICATION_ERROR, 5000)
            else:
                xbmcgui.Dialog().notification('O2TV','Problém při přehrání', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        xbmcgui.Dialog().notification('O2TV','Nesprávný PIN', xbmcgui.NOTIFICATION_ERROR, 5000)

def get_keepalive_url(mpd, response):
    keepalive = None
    dom = minidom.parseString(response.read())
    adaptationSets = dom.getElementsByTagName('AdaptationSet')
    for adaptationSet in adaptationSets:
        if adaptationSet.getAttribute('contentType') == 'video':
            maxBandwidth = adaptationSet.getAttribute('maxBandwidth')
            segmentTemplates = adaptationSet.getElementsByTagName('SegmentTemplate')
            for segmentTemplate in segmentTemplates:
                timelines = segmentTemplate.getElementsByTagName('S')
                for timeline in timelines:
                    if len(timeline.getAttribute('t')) > 0:
                        ts = timeline.getAttribute('t')
                uri = 'dash/' + segmentTemplate.getAttribute('media').replace('&amp;', '&').replace('$RepresentationID$', 'video=' + maxBandwidth).replace('$Time$', ts)
                keepalive = mpd.replace('manifest.mpd?bkm-query', uri)
    return keepalive