#!/usr/bin/python3

"""blah!"""

import json

class GeoCache(object):
    """ Store cache details in a class """

    cacheid = ""
    dltime = 0
    cachename = ""
    cacheowner = ""
    cacheurl = ""
    cachesize = ""
    cachetype = ""
    lat = ""
    lon = ""
    diff = 0.0
    terr = 0.0
    hidden = 0
    lastfound = 0
    short = ""
    body = ""
    hint = ""
    found = 0

    def __init__(self):
        pass

    def __str__(self):

        output = {}
        output['cacheid'] = self.cacheid
        output['dltime'] = self.dltime
        output['cachename'] = self.cachename
        output['cacheowner'] = self.cacheowner
        output['cacheurl'] = self.cacheurl
        output['cachesize'] = self.cachesize
        output['cachetype'] = self.cachetype
        output['lat'] = self.lat
        output['lon'] = self.lon
        output['diff'] = self.diff
        output['terr'] = self.terr
        output['hidden'] = self.hidden
        output['lastfound'] = self.lastfound
        output['short'] = self.short
        output['body'] = self.body
        output['hint'] = self.hint
        output['found'] = self.found

        return json.dumps(output)
