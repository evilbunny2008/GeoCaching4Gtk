#!/usr/bin/python3

"""blah!"""

import json

class LogBook(object):
    """ Store logbook details in a class """

    cacheid = ""
    logid = 0
    accountid = 0
    logtype = ""
    logimage = ""
    logtext = ""
    created = -1
    visited = -1

    def __init__(self):
        pass

    def __str__(self):

        output = {}
        output['cacheid'] = self.cacheid
        output['logid'] = self.logid
        output['accountid'] = self.accountid
        output['logtype'] = self.logtype
        output['logimage'] = self.logimage
        output['logtext'] = self.logtext
        output['created'] = self.created
        output['visited'] = self.visited

        return json.dumps(output)

    # found_it = "2"
    # didnt_find_it = "3"
    # note = "4"
    # archive = "5"
    # will_attend = "9"
    # attended = "10"
    # webcam_photo_taken = "11"
    # unarchive = "12"
    # retrieved_it = "13"
    # placed_it = "14"
    # post_reviewer_note = "18"
    # temp_disable_listing = "22"
    # enable_listing = "23"
    # publish_listing = "24"
    # retract = "25"
    # needs_maintenance = "45"
    # owner_maintenance = "46"
    # update_coordinates = "47"
    # discovered_it = "48"
    # announcement = "74"
    # visit = "75"
    # submit_for_review = "76"
    # oc_team_comment = "83"
