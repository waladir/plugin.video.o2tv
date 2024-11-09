# -*- coding: utf-8 -*-
import sys
import os
import signal
import platform

import json
try:
    from urllib2 import urlopen, Request
except ImportError:
    from urllib.request import urlopen, Request
from xml.dom import minidom

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon

import subprocess
import time
from datetime import datetime

from libs.o2tv import O2API, o2tv_list_api
from libs.session import Session
from libs.settings import Settings
from libs.epg import get_item_epg, epg_api
from libs.utils import check_settings, encode, decode, plugin_id, get_url, get_partnerId, clientTag, apiVersion, day_translation_short

iso639map = {'aa':'aar','ae':'ave','af':'afr','ak':'aka','am':'amh','an':'arg','ar':'ara','as':'asm','av':'ava','ay':'aym','az':'aze','ba':'bak','be':'bel','bg':'bul','bi':'bis','bm':'bam','bn':'ben','bo':'bod','br':'bre','bs':'bos','ca':'cat','ce':'che','co':'cos','cr':'cre','cs':'ces','cu':'chu','cv':'chv','cy':'cym','da':'dan','de':'deu','dv':'div','dz':'dzo','ee':'ewe','el':'ell','en':'eng','eo':'epo','es':'spa','et':'est','eu':'eus','fa':'fas','ff':'ful','fi':'fin','fj':'fij','fo':'fao','fr':'fra','fy':'fry','ga':'gle','gd':'gla','gl':'glg','gn':'grn','gu':'guj','gv':'glv','ha':'hau','he':'heb','hi':'hin','ho':'hmo','hr':'hrv','ht':'hat','hu':'hun','hy':'hye','hz':'her','ch':'cha','ia':'ina','id':'ind','ie':'ile','ig':'ibo','ii':'iii','ik':'ipk','io':'ido','is':'isl','it':'ita','iu':'iku','ja':'jpn','jv':'jav','ka':'kat','kg':'kon','ki':'kik','kj':'kua','kk':'kaz','kl':'kal','km':'khm','kn':'kan','ko':'kor','kr':'kau','ks':'kas','ku':'kur','kv':'kom','kw':'cor','ky':'kir','la':'lat','lb':'ltz','lg':'lug','li':'lim','ln':'lin','lo':'lao','lt':'lit','lu':'lub','lv':'lav','mg':'mlg','mh':'mah','mi':'mri','mk':'mkd','ml':'mal','mn':'mon','mr':'mar','ms':'msa','mt':'mlt','my':'mya','na':'nau','nb':'nob','nd':'nde','ne':'nep','ng':'ndo','nl':'nld','nn':'nno','no':'nor','nr':'nbl','nv':'nav','ny':'nya','oc':'oci','oj':'oji','om':'orm','or':'ori','os':'oss','pa':'pan','pi':'pli','pl':'pol','ps':'pus','pt':'por','qu':'que','rm':'roh','rn':'run','ro':'ron','ru':'rus','rw':'kin','sa':'san','sc':'srd','sd':'snd','se':'sme','sg':'sag','si':'sin','sk':'slk','sl':'slv','sm':'smo','sn':'sna','so':'som','sq':'sqi','sr':'srp','ss':'ssw','st':'sot','su':'sun','sv':'swe','sw':'swa','ta':'tam','te':'tel','tg':'tgk','th':'tha','ti':'tir','tk':'tuk','tl':'tgl','tn':'tsn','to':'ton','tr':'tur','ts':'tso','tt':'tat','tw':'twi','ty':'tah','ug':'uig','uk':'ukr','ur':'urd','uz':'uzb','ve':'ven','vi':'vie','vo':'vol','wa':'wln','wo':'wol','xh':'xho','yi':'yid','yo':'yor','za':'zha','zh':'zho','zu':'zul'}

def get_filename(title, startts):
    import unicodedata
    import re
    try:
        unicode('')
    except NameError:
        unicode = str
    starttime = datetime.fromtimestamp(startts).strftime('%Y-%m-%d_%H-%M')
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore')
    title = title.decode('utf-8')
    title = unicode(re.sub(r'[^\w\s-]', '', title).strip())
    title = unicode(re.sub(r'[-\s]+', '-', title))
    return title + '_' + starttime + '.ts'

def add_to_download_queue(id, title, channel, isrec):
    id = int(id)
    isrec = int(isrec)
    settings = Settings()
    data = settings.load_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'})
    if data is None:
        data = {}
    else:
        data = json.loads(data)
    if id in data.keys():
        xbmcgui.Dialog().notification('O2TV', 'Pořad už je ve frontě ke stažení!', xbmcgui.NOTIFICATION_ERROR, 5000)
    else:
        if isrec == 0:
            epg = get_item_epg(id)
            data.update({id : {'id' : id, 'title' : title, 'channel' : channel, 'isrec' : isrec, 'startts' : epg['startts'], 'endts' : epg['endts'], 'recid' : -1, 'status' : 'ke stažení'}})
            settings.save_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'}, json.dumps(data))
            xbmcgui.Dialog().notification('O2TV', 'Pořad byl přidaný do fronty ke stažení', xbmcgui.NOTIFICATION_INFO, 5000)           
        else:
            session = Session()
            post = {"language":"ces","ks":session.ks,"responseProfile":{"objectType":"KalturaOnDemandResponseProfile","relatedProfiles":[{"objectType":"KalturaDetachedResponseProfile","name":"group_result","filter":{"objectType":"KalturaAggregationCountFilter"}}]},"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_DESC","kSql":"(and asset_type='recording' start_date <'0' end_date < '-900')","groupingOptionEqual":"Include"},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
            epg_data = epg_api(post = post, key = 'id', no_md_title = True)
            if id in epg_data:
                epg = epg_data[id]
                data.update({isrec : {'id' : isrec, 'title' : title, 'channel' : channel, 'isrec' : 1, 'startts' : epg['startts'], 'endts' : epg['endts'], 'recid' : -1, 'status' : 'ke stažení'}})
                settings.save_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'}, json.dumps(data))
                xbmcgui.Dialog().notification('O2TV', 'Pořad byl přidaný do fronty ke stažení', xbmcgui.NOTIFICATION_INFO, 5000)           
            else:
                xbmcgui.Dialog().notification('O2TV', 'Nahrávka nenalezena!', xbmcgui.NOTIFICATION_ERROR, 5000)

def remove_from_download_queue(id):
    settings = Settings()
    data = settings.load_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'})
    if data is None:
        data = {}
    else:
        data = json.loads(data)
    
    if id in data.keys():
        if data[id]['status'] == 'stahování':
            clear_process()
        del data[id]
        settings.save_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'}, json.dumps(data))
        xbmcgui.Dialog().notification('O2TV', 'Pořad byl z fronty smazaný', xbmcgui.NOTIFICATION_INFO, 5000)           
    else:
        xbmcgui.Dialog().notification('O2TV', 'Pořad nebyl ve frontě nalezený!', xbmcgui.NOTIFICATION_ERROR, 5000)
    xbmc.executebuiltin('Container.Refresh')

def list_downloads(label):
    _handle = int(sys.argv[1])
    xbmcplugin.setPluginCategory(_handle, label)
    settings = Settings()
    data = settings.load_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'})
    if data is None:
        data = {}
    else:
        data = json.loads(data)
    for item in dict(reversed(list(data.items()))):
        id = int(data[item]['id'])
        if encode(data[item]['status']) == 'stahování':
            pct = float(int(time.mktime(datetime.now().timetuple()))-int(data[item]['downloadts']))/(int(data[item]['endts'])-int(data[item]['startts'])+16*60+2)*100
            status = decode('[COLOR=red]stahování (' + str(int(pct)) + '%)[/COLOR]')
        else:
            status = '[COLOR=red]' + data[item]['status'] + '[/COLOR]'
        list_item = xbmcgui.ListItem(label = data[item]['title'] + ' | ' + data[item]['channel'] + ' | ' + decode(day_translation_short[datetime.fromtimestamp(data[item]['startts']).strftime('%w')]) + ' ' + datetime.fromtimestamp(data[item]['startts']).strftime('%d.%m. %H:%M') + ' - ' + datetime.fromtimestamp(data[item]['endts']).strftime('%H:%M') + '\n' + status)          
        list_item.setProperty('IsPlayable', 'false')
        list_item.setContentLookup(False)   
        list_item.addContextMenuItems([('Smazat z fronty', 'RunPlugin(plugin://' + plugin_id + '?action=remove_from_download_queue&id=' + str(id) + ')')])  
        url = get_url(action='list_downloads', label=label)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def download_stream(id, title, isrec):
    settings = Settings()
    err = False
    addon = xbmcaddon.Addon()
    downloads_dir = addon.getSetting('downloads_dir')
    ffmpeg_bin = addon.getSetting('ffmpeg_bin')       
    session = Session()
    o2api = O2API()
    no_remove = False
    if isrec == 0:
        post = {"language":"ces","ks":session.ks,"responseProfile":{"objectType":"KalturaOnDemandResponseProfile","relatedProfiles":[{"objectType":"KalturaDetachedResponseProfile","name":"group_result","filter":{"objectType":"KalturaAggregationCountFilter"}}]},"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_DESC","kSql":"(and asset_type='recording' start_date <'0' end_date < '-900')","groupBy":[{"objectType":"KalturaAssetMetaOrTagGroupBy","value":"SeriesID"}],"groupingOptionEqual":"Include"},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
        result = o2tv_list_api(post = post, type = 'archiv - nahrávky', silent = True)
        for item in result:
            if item['id'] == id:
                no_remove = True
        post = {"language":"ces","ks":session.ks,"recording":{"objectType":"KalturaRecording","assetId":id},"clientTag":clientTag,"apiVersion":apiVersion}
        data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/recording/action/add?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
        if 'err' in data or not 'result' in data or not 'status' in data['result'] or data['result']['status'] != 'RECORDED':
            post = {"1":{"service":"asset","action":"get","id":id,"assetReferenceType":"epg_internal","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":id,"assetType":"epg","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"CATCHUP","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":get_partnerId()}
            recid = -1
        else:
            recid = data['result']['id']
            post = {"1":{"service":"asset","action":"get","id":recid,"assetReferenceType":"npvr","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":recid,"assetType":"recording","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"PLAYBACK","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":get_partnerId()}
            if no_remove == True:
                recid = -1
    else:
        recid = id
        post = {"1":{"service":"asset","action":"get","id":recid,"assetReferenceType":"npvr","ks":session.ks},"2":{"service":"asset","action":"getPlaybackContext","assetId":recid,"assetType":"recording","contextDataParams":{"objectType":"KalturaPlaybackContextOptions","context":"PLAYBACK","streamerType":"mpegdash","urlType":"DIRECT"},"ks":session.ks},"apiVersion":"7.8.1","ks":session.ks,"partnerId":get_partnerId()}
        recid = -1

    data = o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/multirequest', data = post, headers = o2api.headers)
    if 'err' in data or not 'result' in data or len(data['result']) == 0 or not 'sources' in data['result'][1]:
        err = True
        xbmcgui.Dialog().notification('O2TV','Problém při stažení streamu', xbmcgui.NOTIFICATION_ERROR, 5000)
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
            if 'DASH' in urls:
                url = urls['DASH']['url']
            if len(url) > 0:
                request = Request(url = url , data = None, headers = o2api.headers)
                response = urlopen(request)
                url = response.url
                video_stream_index = ''
                map_audio = '' 
                dom = minidom.parseString(response.read())
                adaptationSets = dom.getElementsByTagName('AdaptationSet')
                a = 0
                audio_tracks = []
                for adaptationSet in adaptationSets:
                    if adaptationSet.getAttribute('contentType') == 'video':
                        v = 0
                        maxBandwidth = adaptationSet.getAttribute('maxBandwidth')
                        Representations = adaptationSet.getElementsByTagName('Representation')
                        for Representation in Representations:
                            if Representation.getAttribute('bandwidth') == maxBandwidth:
                                video_stream_index = str(v)
                            v += 1
                    if adaptationSet.getAttribute('contentType') == 'audio':
                        if adaptationSet.getAttribute('lang') in iso639map:
                            lang = iso639map[adaptationSet.getAttribute('lang')]
                        else:
                            lang = 'mul'
                        if lang == 'ces':
                            audio_tracks.insert(0, {a : lang})
                        else:
                            audio_tracks.append({a : lang})
                        a =+ 1
                a = 0
                for lang in audio_tracks:
                    for key in lang:
                        map_audio += ' -map 0:a:' + str(key) + ' -metadata:s:a:' + str(a) + ' language=' + lang[key]
                    a += 1

                xbmcgui.Dialog().notification('O2TV', 'Stahování ' + encode(title) + ' začalo', xbmcgui.NOTIFICATION_INFO, 5000)   
                data = settings.load_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'})
                if data is None:
                    data = {}
                else:
                    data = json.loads(data)
                for item in data:
                    if id == data[item]['id']:
                        data.update({item : {'id' : data[item]['id'], 'title' : data[item]['title'], 'channel' : data[item]['channel'], 'isrec' : data[item]['isrec'], 'startts' : data[item]['startts'], 'endts' : data[item]['endts'], 'recid' : data[item]['recid'], 'status' : 'stahování', 'recid' : recid, 'downloadts' : int(time.mktime(datetime.now().timetuple()))}})
                        filename = get_filename(data[item]['title'], data[item]['startts'])
                    settings.save_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'}, json.dumps(data))
                ffmpeg_params = '-re -y -i "' + url + '" -f mpegts -map 0:v:' + video_stream_index + map_audio + ' -c:v copy -c:a copy -mpegts_service_type digital_tv -metadata service_provider=O2TV -c:v copy -c:a copy -loglevel error ' + downloads_dir + filename
                cmd = ffmpeg_bin + ' ' + ffmpeg_params
                osname = platform.system()
                xbmc.log(cmd)
                try:
                    if osname == 'Windows':
                        proc = subprocess.Popen(cmd,stdin=None,stdout=None,stderr=None,shell=False,creationflags=0x08000000)
                    else:
                        proc = subprocess.Popen(cmd,stdin=None,stdout=None,stderr=None,shell=True)
                    return proc
                except Exception:
                    err = True
            else:
                err = True
                xbmcgui.Dialog().notification('O2TV','Problém při stažení streamu', xbmcgui.NOTIFICATION_ERROR, 5000)
        elif 'messages' in data['result'][1] and len(data['result'][1]['messages']) > 0 and data['result'][1]['messages'][0]['code'] == 'ConcurrencyLimitation' :
            err = True
            xbmcgui.Dialog().notification('O2TV','Překročený limit přehrávání', xbmcgui.NOTIFICATION_ERROR, 5000)
        else:
            err = True
            xbmcgui.Dialog().notification('O2TV','Problém při stažení streamu', xbmcgui.NOTIFICATION_ERROR, 5000)
    if err == True:
        data = settings.load_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'})
        if data is None:
            data = {}
        else:
            data = json.loads(data)
        for item in data:
            if id == data[item]['id']:
                if data[item]['recid'] > 0:
                    post = {"language":"ces","ks":session.ks,"id":data[item]['recid'],"clientTag":clientTag,"apiVersion":apiVersion}
                    o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/recording/action/delete?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
                data.update({item : {'id' : data[item]['id'], 'title' : data[item]['title'], 'channel' : data[item]['channel'], 'isrec' : data[item]['isrec'], 'startts' : data[item]['startts'], 'endts' : data[item]['endts'], 'recid' : data[item]['recid'], 'status' : 'chyba', 'downloadts' : int(time.mktime(datetime.now().timetuple()))}})
            settings.save_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'}, json.dumps(data))

def clear_process():
    settings = Settings()
    session = Session()
    o2api = O2API()
    osname = platform.system()
    if osname == 'Linux':
        cmd = 'pgrep -f "ffmpeg.*O2TV"'
        procs = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
        pids = procs.communicate()[0].split()
        for pid in pids:
            try:
                os.kill(int(pid),signal.SIGTERM)
            except OSError:
                pass
    if osname == 'Windows':
        cmd = 'taskkill /f /im ffmpeg.exe'
        subprocess.call(cmd,stdin=None,stdout=None,stderr=None,shell=False,creationflags=0x08000000) 
    data = settings.load_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'})
    if data is None:
        data = {}
    else:
        data = json.loads(data)
    for item in data:
        if encode(data[item]['status']) == 'stahování':
            if int(data[item]['recid']) > 0:
                post = {"language":"ces","ks":session.ks,"id":int(data[item]['recid']),"clientTag":clientTag,"apiVersion":apiVersion}
                o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/recording/action/delete?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
            data.update({item : {'id' : data[item]['id'], 'title' : data[item]['title'], 'channel' : data[item]['channel'], 'isrec' : data[item]['isrec'], 'startts' : data[item]['startts'], 'endts' : data[item]['endts'], 'recid' : data[item]['recid'], 'status' : 'chyba', 'downloadts' : int(time.mktime(datetime.now().timetuple()))}})
        settings.save_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'}, json.dumps(data))

def read_queue():
    settings = Settings()
    next = time.time() + float(10)
    check_settings()
    clear_process()
    download_process = None
    while not xbmc.Monitor().abortRequested():
        if xbmc.Monitor().waitForAbort(10):
            break
        if(next < time.time()):
            xbmc.log('Kontroluji frontu pro stahování')
            data = settings.load_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'})
            if data is None:
                data = {}
            else:
                data = json.loads(data)
            downloading = False
            for item in list(data):
                if encode(data[item]['status']) == 'stahování':
                    downloading = True
                if 'downloadts' in data[item] and data[item]['downloadts'] < int(time.mktime(datetime.now().timetuple()))-7*60*60*24:
                    del data[item]
            settings.save_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'}, json.dumps(data))
            if downloading == False and download_process is None:
                for item in data:
                    if downloading == False and encode(data[item]['status']) == 'ke stažení' and data[item]['endts'] + 20*60 < int(time.mktime(datetime.now().timetuple())):
                        downloading = True
                        download_process = download_stream(data[item]['id'], data[item]['title'], data[item]['isrec'])
            next = time.time() + float(60)
        if download_process is not None:
            poll = download_process.poll()
            if poll is not None:
                download_process = None
                data = settings.load_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'})
                if data is None:
                    data = {}
                else:
                    data = json.loads(data)
                for item in data:
                    if encode(data[item]['status']) == 'stahování':
                        if data[item]['recid'] > 0:
                            session = Session()
                            o2api = O2API()
                            post = {"language":"ces","ks":session.ks,"id":data[item]['recid'],"clientTag":clientTag,"apiVersion":apiVersion}
                            o2api.call_o2_api(url = 'https://' + get_partnerId() + '.frp1.ott.kaltura.com/api_v3/service/recording/action/delete?format=1&clientTag=' + clientTag, data = post, headers = o2api.headers)
                        if poll == 0:
                            data.update({item : {'id' : data[item]['id'], 'title' : data[item]['title'], 'channel' : data[item]['channel'], 'isrec' : data[item]['isrec'], 'startts' : data[item]['startts'], 'endts' : data[item]['endts'], 'recid' : data[item]['recid'], 'status' : 'staženo', 'downloadts' : int(time.mktime(datetime.now().timetuple()))}})
                        else:                                    
                            data.update({item : {'id' : data[item]['id'], 'title' : data[item]['title'], 'channel' : data[item]['channel'], 'isrec' : data[item]['isrec'], 'startts' : data[item]['startts'], 'endts' : data[item]['endts'], 'recid' : data[item]['recid'], 'status' : 'chyba', 'downloadts' : int(time.mktime(datetime.now().timetuple()))}})
                        title = data[item]['title']
                        xbmcgui.Dialog().notification('O2TV', 'Stahování ' + encode(title) + ' bylo dokončeno', xbmcgui.NOTIFICATION_INFO, 5000)       
                    settings.save_json_data({'filename' : 'downloads.txt', 'description' : 'fronty stahování'}, json.dumps(data))                    
        time.sleep(5)
    clear_process()
