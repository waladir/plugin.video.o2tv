# -*- coding: utf-8 -*-
import sys

import xbmcgui
import xbmcaddon
import xbmcvfs

from datetime import datetime
import time

from libs.channels import Channels
from libs.channels import Session
from libs.utils import plugin_id, clientTag, apiVersion
from libs.epg import get_channel_epg, epg_api
from libs.recordings import add_recording
tz_offset = int((time.mktime(datetime.now().timetuple())-time.mktime(datetime.utcnow().timetuple()))/3600)

def save_file_test():
    addon = xbmcaddon.Addon()  
    try:
        content = ''
        output_dir = addon.getSetting('output_dir')      
        test_file = output_dir + 'test.fil'
        file = xbmcvfs.File(test_file, 'w')
        file.write(bytearray(('test').encode('utf-8')))
        file.close()
        file = xbmcvfs.File(test_file, 'r')
        content = file.read()
        if len(content) > 0 and content == 'test':
            file.close()
            xbmcvfs.delete(test_file)
            return 1  
        file.close()
        xbmcvfs.delete(test_file)
        return 0
    except Exception:
        file.close()
        xbmcvfs.delete(test_file)
        return 0 

def generate_playlist(output_file = ''):
    addon = xbmcaddon.Addon()
    if addon.getSetting('output_dir') is None or len(addon.getSetting('output_dir')) == 0:
        xbmcgui.Dialog().notification('O2TV', 'Nastav adresář pro playlist a EPG!', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit() 
             
    channels = Channels()
    channels_list = channels.get_channels_list('channel_number')

    if len(output_file) > 0:
        filename = output_file
    else:
        filename = addon.getSetting('output_dir') + 'playlist.m3u'

    if save_file_test() == 0:
        xbmcgui.Dialog().notification('O2TV', 'Chyba při uložení playlistu', xbmcgui.NOTIFICATION_ERROR, 5000)
        return
    try:
        file = xbmcvfs.File(filename, 'w')
        if file == None:
            xbmcgui.Dialog().notification('O2TV', 'Chyba při uložení playlistu', xbmcgui.NOTIFICATION_ERROR, 5000)
        else:
            file.write(bytearray(('#EXTM3U\n').encode('utf-8')))
            for number in sorted(channels_list.keys()):  
                logo = channels_list[number]['logo']
                if logo is None:
                    logo = ''
                if addon.getSetting('catchup_mode') == 'default':
                    line = '#EXTINF:-1 catchup="default" catchup-days="7" catchup-source="plugin://plugin.video.archivo2tv/?action=iptsc_play_stream&id=' + str(channels_list[number]['id']) + '&catchup_start_ts={utc}&catchup_end_ts={utcend}" tvg-chno="' + str(number) + '" tvg-id="' + channels_list[number]['name'] + '" tvh-epg="0" tvg-logo="' + logo + '",' + channels_list[number]['name']
                else:
                    line = '#EXTINF:-1 catchup="append" catchup-days="7" catchup-source="&catchup_start_ts={utc}&catchup_end_ts={utcend}" tvg-chno="' + str(number) + '" tvg-id="' + channels_list[number]['name'] + '" tvh-epg="0" tvg-logo="' + logo + '",' + channels_list[number]['name']
                file.write(bytearray((line + '\n').encode('utf-8')))
                line = 'plugin://' + plugin_id + '/?action=iptsc_play_stream&id=' + str(channels_list[number]['id'])
                file.write(bytearray(('#KODIPROP:inputstream=inputstream.ffmpegdirect\n').encode('utf-8')))
                file.write(bytearray(('#KODIPROP:inputstream.ffmpegdirect.stream_mode=timeshift\n').encode('utf-8')))
                file.write(bytearray(('#KODIPROP:inputstream.ffmpegdirect.is_realtime_stream=true\n').encode('utf-8')))
                file.write(bytearray(('#KODIPROP:mimetype=video/mp2t\n').encode('utf-8')))
                file.write(bytearray((line + '\n').encode('utf-8')))
            file.close()
            xbmcgui.Dialog().notification('O2TV', 'Playlist byl uložený', xbmcgui.NOTIFICATION_INFO, 5000)    
    except Exception:
        file.close()
        xbmcgui.Dialog().notification('O2TV', 'Chyba při uložení playlistu', xbmcgui.NOTIFICATION_ERROR, 5000)

def generate_epg(output_file = ''):
    addon = xbmcaddon.Addon()
    channels = Channels()
    channels_list = channels.get_channels_list('channel_number', visible_filter = False)
    channels_list_by_id = channels.get_channels_list('id', visible_filter = False)

    if len(channels_list) > 0:
        if save_file_test() == 0:
            xbmcgui.Dialog().notification('O2TV', 'Chyba při uložení EPG', xbmcgui.NOTIFICATION_ERROR, 5000)
            return
        output_dir = addon.getSetting('output_dir') 
        try:
            if len(output_file) > 0:
                file = xbmcvfs.File(output_file, 'w')
            else:
                file = xbmcvfs.File(output_dir + 'o2tv_epg.xml', 'w')
            if file == None:
                xbmcgui.Dialog().notification('O2TV', 'Chyba při uložení EPG', xbmcgui.NOTIFICATION_ERROR, 5000)
            else:
                file.write(bytearray(('<?xml version="1.0" encoding="UTF-8"?>\n').encode('utf-8')))
                file.write(bytearray(('<tv generator-info-name="EPG grabber">\n').encode('utf-8')))
                content = ''
                for number in sorted(channels_list.keys()):
                    logo = channels_list[number]['logo']
                    if logo is None:
                        logo = ''
                    channel = channels_list[number]['name']
                    content = content + '    <channel id="' + channel.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'","&apos;").replace('"',"&quot") + '">\n'
                    content = content + '            <display-name lang="cs">' + channel.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'","&apos;").replace('"',"&quot") + '</display-name>\n'
                    content = content + '            <icon src="' + logo + '" />\n'
                    content = content + '    </channel>\n'
                file.write(bytearray((content).encode('utf-8')))
                today_date = datetime.today() 
                today_start_ts = int(time.mktime(datetime(today_date.year, today_date.month, today_date.day) .timetuple()))
                today_end_ts = today_start_ts + 60*60*24 - 1
                session = Session()
                channels_ids = []
                for number in sorted(channels_list.keys()):
                    channels_ids.append("linear_media_id:'" + str(channels_list[number]['id']) + "'")
                for i in range(0, len(channels_ids), 10):
                    channels_query = ' '.join(channels_ids[i:i+10])
                    cnt = 0
                    content = ''
                    post = {"language":"ces","ks":session.ks,"filter":{"objectType":"KalturaSearchAssetFilter","orderBy":"START_DATE_ASC","kSql":"(and (or " + channels_query + ") start_date >= '" + str(today_start_ts - 60*60*24*7) + "' end_date  <= '" + str(today_end_ts + 60*60*24*7) + "' asset_type='epg' auto_fill= true)"},"pager":{"objectType":"KalturaFilterPager","pageSize":500,"pageIndex":1},"clientTag":clientTag,"apiVersion":apiVersion}
                    epg =  epg_api(post = post, key = 'startts_channel_number')
                    for ts in sorted(epg.keys()):
                        epg_item = epg[ts]
                        starttime = datetime.fromtimestamp(epg_item['startts']).strftime('%Y%m%d%H%M%S')
                        endtime = datetime.fromtimestamp(epg_item['endts']).strftime('%Y%m%d%H%M%S')
                        content = content + '    <programme start="' + starttime + ' +0' + str(tz_offset) + '00" stop="' + endtime + ' +0' + str(tz_offset) + '00" channel="' + channels_list_by_id[epg_item['channel_id']]['name'].replace('&','&amp;').replace('<','&lt;').replace('<','&gt;') + '">\n'
                        content = content + '       <title lang="cs">' + epg_item['title'].replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'","&apos;").replace('"',"&quot") + '</title>\n'
                        if epg_item['original'] != None and len(epg_item['original']) > 0:
                            content = content + '       <title>' + epg_item['original'].replace('&','&amp;').replace('<','&lt;').replace('<','&gt;').replace("'","&apos;").replace('"',"&quot") + '</title>\n'
                        if epg_item['description'] != None and len(epg_item['description']) > 0:
                            content = content + '       <desc lang="cs">' + epg_item['description'].replace('&','&amp;').replace('<','&lt;').replace('<','&gt;').replace("'","&apos;").replace('"',"&quot") + '</desc>\n'
                        if epg_item['episodeName'] != None and len(epg_item['episodeName']) > 0:
                            content = content + '       <sub-title lang="cs">' + epg_item['episodeName'].replace('&','&amp;').replace('<','&lt;').replace('<','&gt;').replace("'","&apos;").replace('"',"&quot") + '</sub-title>\n'
                        if epg_item['episodeNumber'] != None and epg_item['seasonNumber'] != None and epg_item['episodeNumber'] > 0 and epg_item['seasonNumber'] > 0:
                            if epg_item['episodesInSeason'] != None and epg_item['episodesInSeason'] > 0:
                                content = content + '       <episode-num system="xmltv_ns">' + str(epg_item['seasonNumber']-1) + '.' + str(epg_item['episodeNumber']-1) + '/' + str(epg_item['episodesInSeason']) + '.0/0"</episode-num>\n'
                            else:
                                content = content + '       <episode-num system="xmltv_ns">' + str(epg_item['seasonNumber']-1) + '.' + str(epg_item['episodeNumber']-1) + '.0/0"</episode-num>\n'
                        content = content + '       <icon src="' + epg_item['poster'] + '"/>\n'
                        content = content + '       <credits>\n'
                        for person in epg_item['cast']: 
                            content = content + '         <actor role="' + person[1].replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'","&apos;").replace('"',"&quot") + '">' + person[0].replace('&','&amp;').replace('<','&lt;').replace('>','&gt;') + '</actor>\n'
                        for director in epg_item['directors']: 
                            content = content + '         <director>' + director.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'","&apos;").replace('"',"&quot") + '</director>\n'
                        content = content + '       </credits>\n'
                        for category in epg_item['genres']:
                            content = content + '       <category>' + category.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'","&apos;").replace('"',"&quot") + '</category>\n'
                        if len(str(epg_item['year'])) > 0 and int(epg_item['year']) > 0:
                            content = content + '       <date>' + str(epg_item['year']) + '</date>\n'
                        if len(epg_item['country']) > 0:
                            content = content + '       <country>' + epg_item['country'].replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'","&apos;").replace('"',"&quot") + '</country>\n'
                        content = content + '    </programme>\n'
                        cnt = cnt + 1
                        if cnt > 20:
                            file.write(bytearray((content).encode('utf-8')))
                            content = ''
                            cnt = 0
                    file.write(bytearray((content).encode('utf-8')))                          
                file.write(bytearray(('</tv>\n').encode('utf-8')))
                file.close()
                xbmcgui.Dialog().notification('O2TV', 'EPG bylo uložené', xbmcgui.NOTIFICATION_INFO, 5000)    
        except Exception:
            file.close()
            xbmcgui.Dialog().notification('O2TV', 'Chyba při generování EPG!', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit()
    else:
        xbmcgui.Dialog().notification('O2TV', 'Nevrácena žádná data!', xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit()

def iptv_sc_rec(channelName, startdatetime):
    channels = Channels()
    channels_list = channels.get_channels_list('name', visible_filter = False)
    from_ts = int(time.mktime(time.strptime(startdatetime, '%d.%m.%Y %H:%M')))
    epg = get_channel_epg(id = channels_list[channelName]['id'], from_ts = from_ts, to_ts = from_ts + 60*60*12)
    if len(epg) > 0 and from_ts in epg:
        add_recording(epg[from_ts]['id'])
    else:
        xbmcgui.Dialog().notification('O2TV', 'Pořad v O2TV nenalezen! Používáte EPG z doplňku O2TV?', xbmcgui.NOTIFICATION_ERROR, 10000)
