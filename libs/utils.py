# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui
import string, random
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

plugin_id = 'plugin.video.o2tv'
day_translation = {'1' : 'Pondělí', '2' : 'Úterý', '3' : 'Středa', '4' : 'Čtvrtek', '5' : 'Pátek', '6' : 'Sobota', '0' : 'Neděle'}  
day_translation_short = {'1' : 'Po', '2' : 'Út', '3' : 'St', '4' : 'Čt', '5' : 'Pá', '6' : 'So', '0' : 'Ne'}  


_url = sys.argv[0]

def check_settings():
    addon = xbmcaddon.Addon()
    if not addon.getSetting('deviceid'):
        addon.setSetting('deviceid',''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(15)))

    if not addon.getSetting('username') or not addon.getSetting('password') or not addon.getSetting('deviceid'):
        xbmcgui.Dialog().notification('Sledování O2TV', 'V nastavení je nutné mít vyplněné všechny přihlašovací údaje', xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit()

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def decode(string_to_decode):
    if PY2:
        return string_to_decode.decode("utf-8")
    else:
        return string_to_decode

def encode(string_to_encode):
    if PY2:
        return string_to_encode.encode("utf-8")
    else:
        return string_to_encode  

# kod od listenera
def getNumbers(txt):
    newstr = ''.join((ch if ch in '0123456789' else ' ') for ch in txt)
    return [int(i) for i in newstr.split()]

def formatnum(num):
    num = str(num)
    return num if len(num) == 2 else '0' + num

def parsedatetime(_short, _long):
    ix = _short.find(' ')
    lnums = getNumbers(_long)
    snums = getNumbers(_short[:ix])
    year = max(lnums)
    day = min(lnums)
    snums.remove(day)
    day = formatnum(day)
    month = formatnum(min(snums))
    day_formated = '%s.%s.%i' % (day, month, year)
    time_formated = parsetime(_short[ix + 1:])
    return '%s %s' % (day_formated, time_formated)

def parsetime(txt):
    merid = xbmc.getRegion('meridiem')
    h, m = getNumbers(txt)
    if merid.__len__() > 2:
        AM, PM = merid.split('/')
        if txt.endswith(AM) and h == 12:
            h = 0
        elif txt.endswith(PM) and h < 12:
            h += 12
    return '%02d:%02d' % (h, m)


