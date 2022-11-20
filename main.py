# -*- coding: utf-8 -*-
import os
import sys 
import xbmcgui
import xbmcplugin
import xbmcaddon

try:
    from urlparse import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

from libs.utils import get_url, check_settings
from libs.live import list_live
from libs.archive import list_archive, list_archive_days, list_program
from libs.iptvsc import generate_playlist, generate_epg, iptv_sc_rec
from libs.stream import play_live, play_archive, play_catchup
from libs.channels import Channels, manage_channels, list_channels_list_backups, list_channels_edit, edit_channel, delete_channel, change_channels_numbers
from libs.channels import list_channels_groups, add_channel_group, edit_channel_group, edit_channel_group_list_channels, edit_channel_group_add_channel, edit_channel_group_add_all_channels, edit_channel_group_delete_channel, select_channel_group, delete_channel_group
from libs.recordings import list_recordings, delete_recording, delete_future_recording, list_future_recordings, list_planning_recordings, list_rec_days, future_program, add_recording
from libs.categories import list_categories, list_category
from libs.search import list_search, delete_search, program_search
from libs.settings import list_settings
from libs.session import Session

if len(sys.argv) > 1:
    _handle = int(sys.argv[1])

def main_menu():
    addon = xbmcaddon.Addon()
    icons_dir = os.path.join(addon.getAddonInfo('path'), 'resources','images')

    list_item = xbmcgui.ListItem(label='Živé vysílání')
    url = get_url(action='list_live', page = 1, label = 'Živé vysílání')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'livetv.png'), 'icon' : os.path.join(icons_dir , 'livetv.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label='Archiv')
    url = get_url(action='list_archive', label = 'Archiv')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'archive.png'), 'icon' : os.path.join(icons_dir , 'archive.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label='Kategorie')
    url = get_url(action='list_categories', label = 'Kategorie')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'categories.png'), 'icon' : os.path.join(icons_dir , 'categories.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)    

    list_item = xbmcgui.ListItem(label='Nahrávky')
    url = get_url(action='list_recordings', label = 'Nahrávky')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'recordings.png'), 'icon' : os.path.join(icons_dir , 'recordings.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label='Vyhledávání')
    url = get_url(action='list_search', label = 'Vyhledávání')  
    list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'search.png'), 'icon' : os.path.join(icons_dir , 'search.png') })
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    if addon.getSetting('hide_settings') != 'true':
        list_item = xbmcgui.ListItem(label='Nastavení O2TV')
        url = get_url(action='list_settings', label = 'Nastavení O2TV')  
        list_item.setArt({ 'thumb' : os.path.join(icons_dir , 'settings.png'), 'icon' : os.path.join(icons_dir , 'settings.png') })
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    check_settings() 
    if params:
        if params['action'] == 'list_live':
            list_live(params['label'])

        elif params['action'] == 'list_archive':
            list_archive(params['label'])
        elif params['action'] == 'list_archive_days':
            list_archive_days(params['id'], params['label'])
        elif params['action'] == 'list_program':
            list_program(params['id'], params['day_min'], params['label'])

        elif params['action'] == 'list_categories':
            list_categories(params['label'])
        elif params['action'] == 'list_category':
            list_category(params['id'], params['label'])

        elif params['action'] == 'list_recordings':
            list_recordings(params['label'])
        elif params['action'] == 'list_future_recordings':
            list_future_recordings(params['label'])
        elif params['action'] == 'delete_recording':
            delete_recording(params['id'])
        elif params['action'] == 'delete_future_recording':
            delete_future_recording(params['id'])
        elif params['action'] == 'list_planning_recordings':
            list_planning_recordings(params['label'])
        elif params['action'] == 'list_rec_days':
            list_rec_days(params['id'], params['label'])
        elif params['action'] == 'future_program':
            future_program(params['id'], params['day'], params['label'])
        elif params['action'] == 'add_recording':
            add_recording(params['id'])

        elif params['action'] == 'list_search':
            list_search(params['label'])
        elif params['action'] == 'program_search':
            program_search(params['query'], params['label'])
        elif params['action'] == 'delete_search':
            delete_search(params['query'])

        elif params['action'] == 'play_live':
            play_live(params['id'])
        elif params['action'] == 'play_archive':
            play_archive(params['id'])
        elif params['action'] == 'play_recording':
            play_archive(params['id'])

        elif params['action'] == 'list_settings':
            list_settings(params['label'])
        elif params['action'] == 'addon_settings':
            xbmcaddon.Addon().openSettings()
        elif params['action'] == 'reset_session':
           session = Session()
           session.remove_session()

        elif params['action'] == 'manage_channels':
            manage_channels(params['label'])
        elif params['action'] == 'reset_channels_list':
            channels = Channels()
            channels.reset_channels()      
        elif params['action'] == 'restore_channels':
            channels = Channels()
            channels.restore_channels(params['backup'])        
        elif params['action'] == 'list_channels_list_backups':
            list_channels_list_backups(params['label'])

        elif params['action'] == 'list_channels_edit':
            list_channels_edit(params['label'])
        elif params['action'] == 'edit_channel':
            edit_channel(params['id'])
        elif params['action'] == 'delete_channel':
            delete_channel(params['id'])
        elif params['action'] == 'change_channels_numbers':
            change_channels_numbers(params['from_number'], params['direction'])

        elif params['action'] == 'list_channels_groups':
            list_channels_groups(params['label'])
        elif params['action'] == 'add_channel_group':
            add_channel_group(params['label'])
        elif params['action'] == 'edit_channel_group':
            edit_channel_group(params['group'], params['label'])
        elif params['action'] == 'delete_channel_group':
            delete_channel_group(params['group'])
        elif params['action'] == 'select_channel_group':
            select_channel_group(params['group'])

        elif params['action'] == 'edit_channel_group_list_channels':
            edit_channel_group_list_channels(params['group'], params['label'])
        elif params['action'] == 'edit_channel_group_add_channel':
            edit_channel_group_add_channel(params['group'], params['channel'])
        elif params['action'] == 'edit_channel_group_add_all_channels':
            edit_channel_group_add_all_channels(params['group'])
        elif params['action'] == 'edit_channel_group_delete_channel':
            edit_channel_group_delete_channel(params['group'], params['channel'])

        elif params['action'] == 'generate_playlist':
            if 'output_file' in params:
                generate_playlist(params['output_file'])
                xbmcplugin.addDirectoryItem(_handle, '1', xbmcgui.ListItem())
                xbmcplugin.endOfDirectory(_handle, succeeded = True)
            else:
                generate_playlist()
        elif params['action'] == 'generate_epg':
            if 'output_file' in params:
                generate_epg(params['output_file'])
                xbmcplugin.addDirectoryItem(_handle, '1', xbmcgui.ListItem())
                xbmcplugin.endOfDirectory(_handle, succeeded = True)
            else:
                generate_epg()
        elif params['action'] == 'iptsc_play_stream':
            if 'catchup_start_ts' in params and 'catchup_end_ts' in params:
                play_catchup(id = params['id'], start_ts = params['catchup_start_ts'], end_ts = params['catchup_end_ts'])
            # else:
                # if len(xbmc.getInfoLabel('ListItem.ChannelName')) > 0 and len(xbmc.getInfoLabel('ListItem.Date')) > 0:
                #     iptv_sc_play(xbmc.getInfoLabel('ListItem.ChannelName'), parsedatetime(xbmc.getInfoLabel('ListItem.Date'), xbmc.getInfoLabel('ListItem.StartDate')), 0)            
                # else:
            else:
                play_live(params['id'])
        elif params['action'] == 'iptv_sc_rec':
            iptv_sc_rec(params['channel'], params['startdatetime'])

        else:
            raise ValueError('Neznámý parametr: {0}!'.format(paramstring))
    else:
        main_menu()

if __name__ == '__main__':
    router(sys.argv[2][1:])
