#!/usr/bin/python3

"""blah!"""

import json

class Users(object):
    """ Store logbook details in a class """

    accountid = 0
    username = ""
    accountguid = ""
    avatarimage = ""
    findcount = 0
    hidecount = 0

    def __init__(self):
        pass

    def __str__(self):

        output = {}
        output['accountid'] = self.accountid
        output['username'] = self.username
        output['accountguid'] = self.accountguid
        output['avatarimage'] = self.avatarimage
        output['findcount'] = self.findcount
        output['hidecount'] = self.hidecount

        return json.dumps(output)
