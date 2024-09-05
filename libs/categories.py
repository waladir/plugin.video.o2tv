# -*- coding: utf-8 -*-
import sys
import xbmcplugin
import xbmcgui

from datetime import datetime
import time
import json

from libs.session import Session
from libs.o2tv import O2API, o2tv_list_api
from libs.channels import Channels
from libs.epg import epg_api, epg_listitem
from libs.utils import get_url, day_translation_short, clientTag, apiVersion, get_partnerId

_handle = int(sys.argv[1])

def getid(name):
    session = Session()
    o2api = O2API()
    post = {"language":"ces","ks":session.ks,"deviceFamilyId":5,"clientTag":clientTag,"apiVersion":apiVersion}
    data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/categorytree/action/getByVersion?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or len(data['result']) == 0 or 'children' not in data['result'] or len(data['result']['children']) == 0:
        xbmcgui.Dialog().notification('O2TV','Problém při načtení kategorií', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit() 
    for item in data['result']['children']:
        if item['name'] == name:
            return item['id']
    return -1

def list_categories(label):
    xbmcplugin.setPluginCategory(_handle, label)
    categories = [
        {'id' : getid(name = 'Kids'), 'title' : 'Dětské', 'subcategories' : True, 'image' : ''},       
        {'id' : 359022, 'title' : 'Nejlepší filmy', 'subcategories' : False, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/5af997402e454447942c4fae6a8d316f/version/0/height/320/width/570'},
        {'id' : getid(name = 'HP / Category Series'), 'title' : 'Seriály', 'subcategories' : True, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/136803eb36e148f69494e07e9cea3da7/version/1/height/320/width/570'},
        {'id' : getid(name = 'Dokumenty'), 'title' : 'Dokumenty', 'subcategories' : True, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/45abcd0514ed4e19a091631f07f9458b/version/0/height/320/width/570'},
        {'id' : 354992, 'title' : 'Akční a dobrodružné', 'subcategories' : False, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/b41491e591514f1eb849a673e2b43831/version/0/height/320/width/570'},
        {'id' : 354993, 'title' : 'Dětské a rodinné', 'subcategories' : False, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/db018cead90c449f93748de8dec0c476/version/0/height/320/width/570'},
        {'id' : 354994, 'title' : 'Komedie', 'subcategories' : False, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/6025ed6b8bfa4b708b2573a0b2b4e6f6/version/0/height/320/width/570'},
        {'id' : 354988, 'title' : 'Sci-fi a fantasy', 'subcategories' : False, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/8356af551bec4541b00c93386b701e31/version/0/height/320/width/570'},
        {'id' : 354995, 'title' : 'Thrillery', 'subcategories' : False, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/12489519e32e4cb386c72bc4680e4f7f/version/1/height/320/width/570'},
        {'id' : 354996, 'title' : 'Romantické', 'subcategories' : False, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/0c1dd5d82a284db3917b14c98b894c54/version/0/height/320/width/570'},
        {'id' : 357179, 'title' : 'Krimi', 'subcategories' : False, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/d9b43ca784ac44898fabe13c5e1c5393/version/0/height/320/width/570'},
        {'id' : 355131, 'title' : 'Drama', 'subcategories' : False, 'image' : 'https://images.frp1.ott.kaltura.com/Service.svc/GetImage/p/' + get_partnerId() + '/entry_id/b57b594f4f894b37bb2ef4bd86017521/version/0/height/320/width/570'},
    ]
    list_item = xbmcgui.ListItem(label = 'Sport')
    list_item.setArt({'thumb' : '', 'icon' : ''})
    url = get_url(action='list_sport_categories', id = 355153, label = label + ' / Sport')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    for category in categories:
        list_item = xbmcgui.ListItem(label = category['title'])
        list_item.setArt({'thumb' : category['image'], 'icon' : category['image']})
        if category['subcategories'] == True:
            if category['title'] == 'Dětské':
                url = get_url(action='list_children_categories', id = category['id'], label = label + ' / ' + category['title'])  
            else:
                url = get_url(action='list_subcategories', id = category['id'], label = label + ' / ' + category['title'])  
        else:
            url = get_url(action='list_category', id = category['id'], label = label + ' / ' + category['title'])  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)              

def list_subcategories(id, label):
    id = int(id)
    xbmcplugin.setPluginCategory(_handle, label)
    categories = []
    session = Session()
    o2api = O2API()
    post = {"language":"ces","ks":session.ks,"deviceFamilyId":5,"clientTag":clientTag,"apiVersion":apiVersion}
    data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/categorytree/action/getByVersion?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or len(data['result']) == 0 or 'children' not in data['result'] or len(data['result']['children']) == 0:
        xbmcgui.Dialog().notification('O2TV','Problém při načtení kategorií', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit() 
    for item in data['result']['children']:
        if item['id'] == id:
            for category in item['children']:
                if 'unifiedChannels' in category and len(category['unifiedChannels']) > 0:
                    if 'seriál' in category['unifiedChannels'][0]['name']:
                        series = 1
                    else:
                        series = 0
                    categories.append({'id' : category['id'], 'category_id' : category['unifiedChannels'][0]['id'], 'name' : category['name'], 'series' : series})
    for category in categories:
        list_item = xbmcgui.ListItem(label = category['name'])
        url = get_url(action='list_category', id = category['category_id'], series = category['series'], label = label + ' / ' + category['name'])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)              
    
def list_sport_categories(id, label):
    id = int(id)
    session = Session()
    o2api = O2API()
    post = {"language":"ces","ks":session.ks,"deviceFamilyId":5,"clientTag":clientTag,"apiVersion":apiVersion}
    data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/categorytree/action/getByVersion?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or len(data['result']) == 0 or 'children' not in data['result'] or len(data['result']['children']) == 0:
        xbmcgui.Dialog().notification('O2TV','Problém při načtení kategorií', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit() 
    category_tree = data
    post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaChannelFilter","kSql":"","idEqual":id},"pager":{"objectType":"KalturaFilterPager","pageSize":20,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}    
    result = o2tv_list_api(post = post, type = 'kategorie')
    for item in result:
        list_item = xbmcgui.ListItem(label = item['name'].capitalize())
        for item2 in category_tree['result']['children']:
            if item2['referenceId'] == item['metas']['in_app_link']['value']:
                for category in item2['children']:
                    if category['name'] == 'Ze záznamu':
                        list_item = xbmcgui.ListItem(label = item['name'].capitalize())
                        if 'images' in item and len(item['images']) > 0 and 'url' in item['images'][0]:
                            if id == 355178:
                                list_item.setArt({'thumb' : item['images'][0]['url'] + '/height/560/width/374', 'icon' : item['images'][0]['url'] + '/height/560/width/374'})
                            else:
                                list_item.setArt({'thumb' : item['images'][0]['url'] + '/height/320/width/570', 'icon' : item['images'][0]['url'] + '/height/320/width/570'})
                        url = get_url(action='list_category', id = category['unifiedChannels'][0]['id'], series = 0, label = label + ' / ' + item['name'].capitalize())  
                        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    if id != 355178:
        list_item = xbmcgui.ListItem(label='Soutěže')
        list_item.setArt({'thumb' : '', 'icon' : ''})
        url = get_url(action='list_sport_categories', id = 355178, label = label + ' / Soutěže')  
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)              

def list_children_categories(id, label):
    id = int(id)
    xbmcplugin.setPluginCategory(_handle, label)
    categories = []
    session = Session()
    o2api = O2API()
    post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaChannelFilter","kSql":"","idEqual":354900},"pager":{"objectType":"KalturaFilterPager","pageSize":300,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
    data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/asset/action/list?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers, nolog = False)

    post = {"language":"ces","ks":session.ks,"deviceFamilyId":5,"clientTag":clientTag,"apiVersion":apiVersion}
    data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/categorytree/action/getByVersion?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or len(data['result']) == 0 or 'children' not in data['result'] or len(data['result']['children']) == 0:
        xbmcgui.Dialog().notification('O2TV','Problém při načtení kategorií', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit() 
    for item in data['result']['children']:
        if item['id'] == id:
            for category in item['children']:
                if 'unifiedChannels' in category and len(category['unifiedChannels']) > 0 and category['name'] in ['Dětské filmy', 'Dětské seriály']:
                    if 'seriál' in category['unifiedChannels'][0]['name']:
                        series = 1
                    else:
                        series = 0
                    categories.append({'id' : category['id'], 'category_id' : category['unifiedChannels'][0]['id'], 'name' : category['name'], 'series' : series})
    for category in categories:
        list_item = xbmcgui.ListItem(label = category['name'])
        url = get_url(action='list_category', id = category['category_id'], series = category['series'], label = label + ' / ' + category['name'])
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = True)              

def list_category(id, series, label):
    xbmcplugin.setPluginCategory(_handle, label)
    session = Session()
    channels = Channels()
    channels_list = channels.get_channels_list('id', visible_filter = True)            
    if series == 0:
        post = {"language":"ces","ks":session.ks,"responseProfile":{"objectType":"KalturaOnDemandResponseProfile","relatedProfiles":[{"objectType":"KalturaDetachedResponseProfile","name":"group_result","filter":{"objectType":"KalturaAggregationCountFilter"}}],"retrievedProperties":"assetId, assetType, duration, finishedWatching, position, watchedDate, mediaFiles,description,objectType,name,id,images,tags,metas,epgChannelId,enableCatchUp,enableCdvr,enableStartOver,enableTrickPlay,linearAssetId,type,updateDate,externalId,epgId,endDate,createDate,crid,startDate"},"filter":{"objectType":"KalturaChannelFilter","kSql":"","groupBy":[{"objectType":"KalturaAssetMetaOrTagGroupBy","value":"name"}],"idEqual":id},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
    else:
        post = {"language":"ces","ks":session.ks,"responseProfile":{"objectType":"KalturaOnDemandResponseProfile","relatedProfiles":[{"objectType":"KalturaDetachedResponseProfile","name":"group_result","filter":{"objectType":"KalturaAggregationCountFilter"}}],"retrievedProperties":"assetId, assetType, duration, finishedWatching, position, watchedDate, mediaFiles,description,objectType,name,id,images,tags,metas,epgChannelId,enableCatchUp,enableCdvr,enableStartOver,enableTrickPlay,linearAssetId,type,updateDate,externalId,epgId,endDate,createDate,crid,startDate"},"filter":{"objectType":"KalturaChannelFilter","kSql":"","groupBy":[{"objectType":"KalturaAssetMetaOrTagGroupBy","value":"SeriesID"}],"idEqual":id},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
    epg = epg_api(post = post, key = 'startts_channel_number')
    for key in epg:
        if epg[key]['channel_id'] in channels_list:
            list_item = xbmcgui.ListItem(label = epg[key]['title'] + ' (' + channels_list[epg[key]['channel_id']]['name'] + ' | ' + day_translation_short[datetime.fromtimestamp(epg[key]['startts']).strftime('%w')] + ' ' + datetime.fromtimestamp(epg[key]['startts']).strftime('%d.%m. %H:%M') + ' - ' + datetime.fromtimestamp(epg[key]['endts']).strftime('%H:%M') + ')')        
            if epg[key]['isSeries'] == True:
                url = get_url(action='list_series', id = epg[key]['seriesId'], label = label + ' / ' + epg[key]['title'])
                if 'cover' in epg[key] and len(epg[key]['cover']) > 0:
                    if 'poster' in epg[key] and len(epg[key]['poster']) > 0:
                        list_item.setArt({'poster': epg[key]['poster'], 'icon': epg[key]['cover']})
                    else:
                        list_item.setArt({'thumb': epg[key]['cover'], 'icon': epg[key]['cover']})
                else:
                    list_item.setArt({'thumb': channels_list[epg[key]['channel_id']]['logo'], 'icon': channels_list[epg[key]['channel_id']]['logo']})    
                xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
            elif epg[key]['endts'] < int(time.time()):
                list_item = epg_listitem(list_item = list_item, epg = epg[key], logo = '')
                list_item.setProperty('IsPlayable', 'true')
                list_item.setContentLookup(False)          
                url = get_url(action='play_archive', id = epg[key]['id'], epg = json.dumps(epg[key]), channel_id = epg[key]['channel_id'], startts = epg[key]['startts']-1, endts = epg[key]['endts'])
                xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def list_series(id, label):
    xbmcplugin.setPluginCategory(_handle, label)
    session = Session()
    channels = Channels()
    channels_list = channels.get_channels_list('id', visible_filter = True)            
    post = {"language":"ces","ks":session.ks,"responseProfile":{"objectType":"KalturaOnDemandResponseProfile","relatedProfiles":[{"objectType":"KalturaDetachedResponseProfile","name":"group_result","filter":{"objectType":"KalturaAggregationCountFilter"}}],"retrievedProperties":"assetId, assetType, duration, finishedWatching, position, watchedDate, mediaFiles,description,objectType,name,id,images,tags,metas,epgChannelId,enableCatchUp,enableCdvr,enableStartOver,enableTrickPlay,linearAssetId,type,updateDate,externalId,epgId,endDate,createDate,crid,startDate"},"filter":{"objectType":"KalturaSearchAssetFilter","dynamicOrderBy":{"objectType":"KalturaDynamicOrderBy","name":"EpisodeNumber","orderBy":"META_ASC"},"kSql":"(and SeriesId='" + str(id) + "')","typeIn":"0"},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
    epg = epg_api(post = post, key = 'startts_channel_number')
    for key in sorted(epg.keys()):
        if epg[key]['channel_id'] in channels_list and epg[key]['endts'] < int(time.time()):
            title = epg[key]['episodeName']
            if len(title) == 0:
                title = epg[key]['title']
                if epg[key]['episodeNumber'] > 0:
                    if epg[key]['seasonNumber']  > 0:
                        title = title + ' S' + str(epg[key]['seasonNumber']) + 'E' + str(epg[key]['seasonNumber'])
                    else:
                        title = title + ' E' + str(epg[key]['episodeNumber'])
            list_item = xbmcgui.ListItem(label = title + ' (' + channels_list[epg[key]['channel_id']]['name'] + ' | ' + day_translation_short[datetime.fromtimestamp(epg[key]['startts']).strftime('%w')] + ' ' + datetime.fromtimestamp(epg[key]['startts']).strftime('%d.%m. %H:%M') + ' - ' + datetime.fromtimestamp(epg[key]['endts']).strftime('%H:%M') + ')')        
            list_item = epg_listitem(list_item = list_item, epg = epg[key], logo = '')
            list_item.setProperty('IsPlayable', 'true')
            list_item.setContentLookup(False)          
            url = get_url(action='play_archive', id = epg[key]['id'], epg = json.dumps(epg[key]), channel_id = epg[key]['channel_id'], startts = epg[key]['startts']-1, endts = epg[key]['endts'])
            xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

