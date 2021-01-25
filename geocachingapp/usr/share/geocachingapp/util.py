#!/usr/bin/python3

""" code to download and display geocaching.com locations """

import time
import datetime
import math
from geographiclib.geodesic import Geodesic
from html.parser import HTMLParser
from html import unescape
import json
import mysqlite
import files
import htmlcode
import geocache
import images
import logbook
import users

SESSION = files.get_session()
TOKEN = ""

def gclogin(username, password):
    """ login in to geocaching.com """

    loginok = 0

    loginok, response = is_logged_in()

    if loginok == 0:
        data = do_auth(username, password)
        response = data.text
        if "li-user-info" in response:
            data = "username=" + username  + "\npassword=" + password + "\n"
            files.write_file("geocaching.ini", data)
            loginok = 1
            files.save_session(SESSION)
    else:
        loginok = 1

    return [loginok, response]

def get_log_types(cacheid):
    """ get the current types that can be logged """

    global TOKEN
    cacheid = cacheid.upper()
    url = "https://www.geocaching.com/play/geocache/" + cacheid.lower() + "/log"
    html = SESSION.get(url)
    data = html.text

    TOKEN = html.text.split('__RequestVerificationToken', 1)[1]
    TOKEN = TOKEN.split('value="', 1)[1].split('"', 1)[0].strip()

    logtypes = data.split('<select class="log-type" name="LogTypeId">', 1)[1]
    logtypes = logtypes.split('</select>', 1)[0].strip()

    logtypes = logtypes.split('<option value="')

    log_arr = []
    for line in logtypes:
        line.strip()
        if line == "":
            continue

        type_id = line.split('">', 1)[0].strip()
        type_text = unescape(line.split('">', 1)[1].split('</option>')[0].strip())
        log_arr.append({"type_id": type_id, "type_text": type_text})

    print(log_arr)
    return json.dumps(log_arr)

def logvisit(cacheid, logtype, logdate, logtext):
    """ Log a cache visit """

    cacheid = cacheid.upper()
    url = "https://www.geocaching.com/play/geocache/" + cacheid.lower() + "/log"

    now = datetime.datetime.now()

    if logdate == "Today":
        logdate = now.strftime("%Y-%m-%d")
    else:
        yesterday = now - datetime.timedelta(days=1)
        logdate = yesterday.strftime("%Y-%m-%d")

    logtypeid = get_log_type_id(logtype)

    data = {}
    data['__RequestVerificationToken'] = TOKEN
    data['LogTypeId'] = logtypeid
    data['LogDate'] = logdate
    data['LogText'] = logtext

    # print(url)
    # print(data)

    try:
        # TODO: check for reply in case of failure for whatever reason...
        SESSION.post(url, data=data)
        return True
        # response = SESSION.post(url, data=data)
        # print(response.html)
    except Exception as error:
        print("line 104")
        print(error)
        return error

def get_log_type_id(logtype):
    """ Convert name to id """

    print("logtype == " + logtype)

    if logtype == "Found It":
        return 2
    elif logtype == "Didn't Find It":
        return 3
    elif logtype == "Write note":
        return 4
    elif logtype == "Owner maintenance":
        return 5
    elif logtype == "Will attend":
        return 9
    elif logtype == "Attended":
        return 10
    elif logtype == "Disable":
        return 22
    elif logtype == "Publish Listing":
        return 24
    elif logtype == "Owner maintenance":
        return 46
    elif logtype == "Update coordinates":
        return 47
    return 4

def do_auth(username, password):
    """ Actual code to log in to geocaching.com """

    url = "https://www.geocaching.com/account/signin"
    html = SESSION.get(url)

    token_field = html.text.split('__RequestVerificationToken', 1)[1]
    token_field = token_field.split('value="', 1)[1].split('"', 1)[0].strip()

    data = {}
    data['UsernameOrEmail'] = username
    data['Password'] = password
    data['__RequestVerificationToken'] = token_field
    data['ReturnUrl'] = ""

    response = SESSION.post(url, data=data)
    print("line=151")
    return response

def is_logged_in():
    """ check to see if the app is logged in """

    url = "https://www.geocaching.com/play/search"
    html = SESSION.get(url)

    if "li-user-info" in html.text:
        print("User logged in, skipping re-auth")
        return [1, html.text]

    print("User not logged in, not skipping re-auth")
    return [0, html.text]

def get_row(conn, cacheid):
    """ get a geocache from the database """

    cacheid = cacheid.upper()
    ret = mysqlite.get_row(conn, cacheid)

    if ret is not None and ret[0] != "":
        g_arr = geocache.GeoCache()
        g_arr.cacheid = ret[0]
        g_arr.dltime = ret[1]
        g_arr.cachename = ret[2]
        g_arr.cacheowner = ret[3]
        g_arr.cacheurl = ret[4]
        g_arr.cachesize = ret[5]
        g_arr.cachetype = ret[6]
        g_arr.lat = ret[7]
        g_arr.lon = ret[8]
        g_arr.diff = ret[9]
        g_arr.terr = ret[10]
        g_arr.hidden = ret[11]
        g_arr.lastfound = ret[12]
        g_arr.short = ret[13]
        g_arr.body = htmlcode.cache_images(ret[14], SESSION)
        g_arr.hint = ret[15].replace("<br>", "\n")
        g_arr.found = ret[16]
        row = g_arr

    else:
        row = None

    return row

def get_json_attributes(cacheid):
    """ get attributes for a cache """

    cacheid = cacheid.upper()
    conn = mysqlite.check_db()
    a_out = mysqlite.get_attributes(conn, cacheid)
    close_db(conn)

    return json.dumps(a_out)

def close_db(conn):
    """ If the link to the db is open, close it """

    if conn:
        conn.close()

def clean_up(var):
    """ Convert dates to unix timestamps """

    if var == "-":
        var = -1
    else:
        date_format = "%Y-%m-%d"
        if "/" in var:
            date_format = "%m/%d/%Y"
        elif " " in var:
            date_format = "%d %b %y"
        try:
            var = time.mktime(datetime.datetime.strptime(var, date_format).timetuple())
        except:
            var = 0.0
        var = int(var)

    return var

def refresh_cache(cacheid):
    """ Update the stored cache info with new data if it exists """

    cacheid = cacheid.upper()
    conn = mysqlite.check_db()
    g_arr = get_row(conn, cacheid)

    ret = get_cache_page(conn, cacheid, g_arr.cacheurl)
    if ret is None:
        print("Failed to update cache details, are we logged in?")
        return

    lat, lon, short, body, hint, attributes, found = ret
    dltime = int(time.time())

    g_arr.dltime = dltime
    g_arr.lat = float(lat)
    g_arr.lon = float(lon)
    g_arr.short = short
    g_arr.body = body
    g_arr.hint = hint
    g_arr.found = found

    mysqlite.add_to_db(conn, g_arr, attributes)

def delete_cache(cacheid):
    """Remove deleted caches from the database"""

    conn = mysqlite.check_db()
    mysqlite.delete_row(conn, cacheid)

def dl_cache(cacheid):
    """ Download and parse a cache page """

    cacheid = cacheid.upper()
    conn = mysqlite.check_db()
    cache_url = "https://www.geocaching.com/geocache/" + cacheid
    print(cache_url)

    try:
        html = SESSION.get(cache_url)
        data = html.text
    except Exception as error:
        print("494 - bombed out, are we still logged in?")
        print(error)
        return "bombed out, are we still logged in?"

    # TODO: check if cache is not found, 404 page doesnt show logged in user menu
    if "li-user-info" not in data:
        print("bombed out, are we still logged in?")
        return "bombed out, are we still logged in?"

    if data.find("<strong id=\"ctl00_ContentBody_GeoNav_logText\">Found It!</strong>") != -1:
        found = 1
    else:
        found = 0

    print("Found cacheid: " + cacheid)
    cachename = data.split('<span id="ctl00_ContentBody_CacheName">', 1)[1]
    cachename = cachename.split('</span>', 1)[0].strip()
    cachesize = data.split('" title="Size: ', 1)[1].split(' ', 1)[0].strip()

    cacheowner = data.split('<div id="ctl00_ContentBody_mcd1">', 1)[1]
    cacheowner = cacheowner.split('">', 1)[1].split('</a>', 1)[0].strip()
    cachetype = data.split('<a href="/about/cache_types.aspx" target="_blank" title="', 1)[1]
    cachetype = cachetype.split('"', 1)[0].strip()

    diff = data.split('<span id="ctl00_ContentBody_uxLegendScale" title="', 1)[1]
    diff = diff.split('alt="', 1)[1].split(' ', 1)[0].strip()
    diff = float(diff)
    terr = data.split('<span id="ctl00_ContentBody_Localize12" title="', 1)[1]
    terr = terr.split('alt="', 1)[1].split(' ', 1)[0].strip()
    terr = float(terr)

    hidden = data.split('<div id="ctl00_ContentBody_mcd2">', 1)[1]
    hidden = hidden.split('</div>', 1)[0].split(':', 1)[1].strip()
    hidden = hidden.split('\n', 1)[0].strip()
    hidden = clean_up(hidden)

    bits = data.split("var lat=", 1)[1].split(", guid='")[0].strip()
    lat = bits.split(", lng=", 1)[0].strip()
    lon = bits.split(", lng=", 1)[1].strip()

    short = data.split('<span id="ctl00_ContentBody_ShortDescription">', 1)[1]
    short = short.split("</span>", 1)[0].strip()

    body = data.split('<span id="ctl00_ContentBody_LongDescription">', 1)[1]
    body = body.split('<p id="ctl00_ContentBody_hints">', 1)[0].strip()
    body = '<span id="ctl00_ContentBody_LongDescription">' + body

    hint = data.split('<div id="div_hint" class="span-8 WrapFix">', 1)[1]
    hint = hint.split('</div>', 1)[0].strip()

    attributes = []

    tmpstr = data.split('<div class="WidgetBody">', 1)[1]
    tmpstr = tmpstr.split('<p class="NoBottomSpacing">', 1)[0]
    for line in tmpstr.split('<img src="/images/attributes/'):
        line = line.strip()
        if line == "":
            continue

        line = line.split('.png"', 1)[0]
        if line == "attribute-blank":
            continue

        attributes.append(line)
        print("attribute == " + line)

    tmpstr = "{" + data.split('initialLogs = {', 1)[1]
    tmpstr = tmpstr.split('};', 1)[0] + "}"
    user_token = data.split("userToken = '", 1)[1].split("';", 1)[0].strip()
    save_logs(conn, cacheid, tmpstr, user_token)

    cursor = conn.cursor()
    cursor.execute("SELECT visited FROM logbook WHERE cacheid=? and logtype='Found it' " + \
                    "ORDER BY logid DESC LIMIT 1", (cacheid,))
    ret = cursor.fetchone()
    cursor.close()
    if ret is not None:
        lastfound = ret[0]
    else:
        lastfound = -1

    g_arr = geocache.GeoCache()
    g_arr.cacheid = cacheid
    g_arr.dltime = int(time.time())
    g_arr.cachename = cachename
    g_arr.cacheowner = cacheowner
    g_arr.cachesize = cachesize
    g_arr.cacheurl = cache_url
    g_arr.cachetype = cachetype
    g_arr.lat = float(lat)
    g_arr.lon = float(lon)
    g_arr.diff = diff
    g_arr.terr = terr
    g_arr.hidden = hidden
    g_arr.lastfound = lastfound
    g_arr.short = short
    g_arr.body = body
    g_arr.hint = hint
    g_arr.found = found

    mysqlite.add_to_db(conn, g_arr, attributes)

    close_db(conn)

    return True

def get_cache_list2(lat1, lon1, lat2, lon2, lat3, lon3):
    """ Grab a quick list of locations """

    lat1 = str(lat1)
    lon1 = str(lon1)
    lat2 = str(lat2)
    lon2 = str(lon2)
    lat3 = str(lat3)
    lon3 = str(lon3)

    url = "https://www.geocaching.com/api/proxy/web/search?box=" + lat1 + "%2C" + lon1 + \
          "%2C" + lat2 + "%2C" + lon2 + "&take=500&asc=true&skip=0&sort=distance&origin=" + \
          lat3 + "%2C" + lon3

    print(url)

def get_cache_list(lat, lon):
    """ Search for the nearest 50 unfound caches not owned by the app """

    loc = htmlcode.decdeg2dm(lat, lon)
    url = "https://www.geocaching.com/play/search?lat=" + str(lat) + "&lng=" + str(lon) + \
          "&origin=" + loc + "&radius=100km&o=2&sort=Distance&asc=True"

    print(url)
    conn = mysqlite.check_db()

    try:
        html = SESSION.get(url)
        data = html.text
    except Exception as error:
        print("606 - bombed out, are we still logged in?")
        print(error)
        return None

    if "li-user-info" not in data:
        print("bombed out, are we still logged in?")
        return None

    data = data.split('<tbody id="geocaches">', 1)[1].split("</tbody>", 1)[0].strip()
    rows = data.split('<tr  data-rownumber="')
    for row in rows:
        try:
            row = row.strip()
            if row == "":
                continue

            lat = 0.0
            lon = 0.0
            short = ""
            body = ""
            hint = ""
            dltime = 0
            found = 0

            if row.find("cache-types.svg#icon-found") != -1:
                found = 1

            cacheid = row.split('data-id="', 1)[1].split('"', 1)[0].strip()
            print("Found cacheid: " + cacheid)
            cachename = row.split('data-name="', 1)[1].split('"', 1)[0].strip()
            cachesize = row.split('data-column="ContainerSize">', 1)[1].split('</td>', 1)[0].strip()

            cacheowner = row.split('<span class="owner">', 1)[1].split('</span>', 1)[0].strip()
            cachetype = row.split('<span class="cache-details">', 1)[1].split('|', 1)[0].strip()

            diff = row.split('data-column="Difficulty">', 1)[1].split('</td>', 1)[0].strip()
            diff = float(diff)
            terr = row.split('data-column="Terrain">', 1)[1].split('</td>', 1)[0].strip()
            terr = float(terr)
            hidden = row.split('data-column="PlaceDate">', 1)[1].split('</td>', 1)[0].strip()
            hidden = clean_up(hidden)
            lastfound = row.split('data-column="DateLastVisited">', 1)[1].split('</td>', 1)[0]
            lastfound = clean_up(lastfound.strip())
            cacheurl = "https://www.geocaching.com" + row.split('<a href="', 1)[1]
            cacheurl = cacheurl.split('"', 1)[0].strip()

            cache = get_row(conn, cacheid)
            if cache is None or (cache.lat == 0.0 and cache.lon == 0.0):
                ret = get_cache_page(conn, cacheid, cacheurl)
                if ret is None:
                    print("Failed to update cache details, are we logged in?")
                    return

                lat, lon, short, body, hint, attributes, found = ret
            else:
                print(cacheid + ": Already exists in the db, skipping...")
                lat = cache.lat
                lon = cache.lon
                short = cache.short
                body = cache.body
                hint = cache.hint
                attributes = mysqlite.get_attributes(conn, cacheid)

            g_arr = geocache.GeoCache()
            g_arr.cacheid = cacheid
            g_arr.dltime = int(time.time())
            g_arr.cachename = cachename
            g_arr.cacheowner = cacheowner
            g_arr.cachesize = cachesize
            g_arr.cacheurl = cacheurl
            g_arr.cachetype = cachetype
            g_arr.lat = float(lat)
            g_arr.lon = float(lon)
            g_arr.diff = diff
            g_arr.terr = terr
            g_arr.hidden = hidden
            g_arr.lastfound = lastfound
            g_arr.short = short
            g_arr.body = body
            g_arr.hint = hint
            g_arr.found = found

            mysqlite.add_to_db(conn, g_arr, attributes)
        except Exception as error:
            print("459 - Failed to parse cache info.")
            print(error)

    close_db(conn)

def get_cache_page(conn, cacheid, url):
    """ download and parse cache info... """

    cacheid = cacheid.upper()
    try:
        html = SESSION.get(url)
        data = html.text

        if "li-user-info" not in data:
            print("bombed out, are we still logged in?")
            return None

        bits = data.split("var lat=", 1)[1].split(", guid='")[0].strip()
        lat = bits.split(", lng=", 1)[0].strip()
        lon = bits.split(", lng=", 1)[1].strip()

        short = data.split('<span id="ctl00_ContentBody_ShortDescription">', 1)[1]
        short = short.split("</span>", 1)[0].strip()

        body = data.split('<span id="ctl00_ContentBody_LongDescription">', 1)[1]
        body = body.split('<p id="ctl00_ContentBody_hints">', 1)[0].strip()
        body = '<span id="ctl00_ContentBody_LongDescription">' + body

        hint = data.split('<div id="div_hint" class="span-8 WrapFix">', 1)[1]
        hint = hint.split('</div>', 1)[0].strip()

        if data.find("<strong id=\"ctl00_ContentBody_GeoNav_logText\">Found It!</strong>") != -1:
            found = 1
        else:
            found = 0

        attributes = []

        tmpstr = data.split('<div class="WidgetBody">', 1)[1]
        tmpstr = tmpstr.split('<p class="NoBottomSpacing">', 1)[0]
        for line in tmpstr.split('<img src="/images/attributes/'):
            line = line.strip()
            if line == "":
                continue

            line = line.split('.png"')[0]
            if line == "attribute-blank":
                continue

            attributes.append(line)
            print("attribute == " + line)

        tmpstr = "{" + data.split('initialLogs = {', 1)[1]
        tmpstr = tmpstr.split('};', 1)[0] + "}"
        user_token = data.split("userToken = '", 1)[1].split("';", 1)[0].strip()
        save_logs(conn, cacheid, tmpstr, user_token)

    except Exception as error:
        print("734 - Failed to download cache details, most likely not logged in.")
        print(error)
        return None

    return [float(lat), float(lon), short, body, hint, attributes, found]

def get_more_logs(index, size, user_token):
    """ download more logbook entries """

    url = "https://www.geocaching.com/seek/geocache.logbook?tkn=" + user_token + "&idx=" + \
          str(index) + "&num=" + str(size)
    print(url)

    try:
        html = SESSION.get(url)
        data = html.text
        json_object = json.loads(data)
        json_array = json_object['data']
        return json_array
    except Exception as error:
        print("line 752")
        print(error)

    return None

def save_logs(conn, cacheid, logstr, user_token):
    """ Save logs to the database """

    cacheid = cacheid.upper()
    json_object = json.loads(logstr)
    page_info = json_object['pageInfo']
    size = page_info['size']
    total_rows = page_info['totalRows']
    pages = math.ceil(total_rows / size)
    if pages > 5:
        pages = 5
    json_array = json_object['data']

    for i in range(1, pages + 1):
        if i > 1:
            json_array = get_more_logs(i, size, user_token)
            if json_array is None:
                return

        for log in json_array:
            l_b = logbook.LogBook()
            l_b.cacheid = cacheid
            l_b.logid = log['LogID']
            l_b.accountid = log['AccountID']
            l_b.logtype = log['LogType']
            l_b.logimage = log['LogTypeImage']
            l_b.logtext = htmlcode.cache_images(log['LogText'], SESSION)
            l_b.created = clean_up(log['Created'])
            l_b.visited = clean_up(log['Visited'])

            save_log(conn, l_b)

            user = users.Users()
            user.accountid = log['AccountID']
            user.username = log['UserName']
            user.accountguid = log['AccountGuid']
            user.avatarimage = log['AvatarImage']
            user.findcount = log['GeocacheFindCount']
            user.hidecount = log['GeocacheHideCount']

            save_user(conn, user)

            for img in log['Images']:
                image = images.Images()
                image.cacheid = cacheid
                image.accountid = log['AccountID']
                image.imageid = img['ImageID']
                image.logid = log['LogID']
                image.filename = img['FileName']
                image.created = clean_up(img['Created'])
                image.name = img['Name']
                image.descr = img['Descr']

                save_image(conn, image)

def save_log(conn, l_b):
    """ create or update the logbook entries """

    g_l = get_log(conn, l_b.logid)
    cursor = conn.cursor()
    if g_l is None:
        cursor.execute("INSERT INTO logbook (cacheid, logid, accountid, logtype, logimage, " +
                       "logtext, created, visited) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", \
                       (l_b.cacheid, l_b.logid, l_b.accountid, l_b.logtype, l_b.logimage,
                        l_b.logtext, l_b.created, l_b.visited))
    else:
        cursor.execute("UPDATE logbook set logtype = ?, logimage = ?, logtext = ?, " +
                       "created = ?, visited = ? WHERE logid = ?", \
                       (l_b.logtype, l_b.logimage, l_b.logtext, l_b.created, l_b.visited, \
                        l_b.logid))
    cursor.close()
    conn.commit()

def save_user(conn, user):
    """ Save or update user to the db """

    ret = get_user(conn, user.accountid)
    cursor = conn.cursor()
    if ret is None:
        cursor.execute("INSERT INTO users (accountid, username, accountguid, avatarimage, " +
                       "findcount, hidecount) VALUES (?, ?, ?, ?, ?, ?)", (user.accountid, \
                       user.username, user.accountguid, user.avatarimage, user.findcount, \
                       user.hidecount))
    else:
        cursor.execute("UPDATE users set username = ?, avatarimage = ?, findcount = ?, " +
                       "hidecount = ? WHERE accountid = ?", \
                       (user.username, user.avatarimage, user.findcount, user.hidecount, \
                        user.accountid))
    cursor.close()
    conn.commit()

def save_image(conn, image):
    """ save image metadata to the DB """

    img = get_image(conn, image.imageid)
    if img is None:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cacheimages (cacheid, accountid, imageid, " +
                       "logid, filename, created, name, descr) VALUES " +
                       "(?, ?, ?, ?, ?, ?, ?, ?)", (image.cacheid, image.accountid, \
                        image.imageid, image.logid, image.filename, image.created, \
                        image.name, image.descr))
        cursor.close()
        conn.commit()

def get_image(conn, imageid):
    """ return image array from db """

    cursor = conn.cursor()
    cursor.execute("SELECT * from cacheimages where imageid = ?", (imageid,))
    ret = cursor.fetchone()
    cursor.close()

    if ret is not None and ret[0] != "":
        image = images.Images()
        image.cacheid = ret[0]
        image.accountid = ret[1]
        image.imageid = ret[2]
        image.logid = ret[3]
        image.filename = ret[4]
        image.created = ret[5]
        image.name = ret[6]
        image.descr = ret[7]
        row = image

    else:
        row = None

    return row

def get_images(conn, logid):
    """ get image details from the DB """

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cacheimages where logid = ?", (logid,))

    arr = []
    for row in cursor:
        output = {}
        output['cacheid'] = row[0]
        output['accountid'] = row[1]
        output['imageid'] = row[2]
        output['logid'] = row[3]
        url = "https://img.geocaching.com/cache/log/large/" + row[4]
        filename = files.cache_image(url, SESSION)
        output['filename'] = filename
        output['created'] = row[5]
        output['name'] = row[6]
        output['descr'] = row[7]
        arr.append(output)

    return arr

def get_json_user(accountid):
    """ get user details from DB """
    conn = mysqlite.check_db()
    user = get_user(conn, accountid)
    close_db(conn)

    return str(user)

def get_json_logs(cacheid):
    """ returns logs in json format """

    cacheid = cacheid.upper()
    conn = mysqlite.check_db()
    g_l = get_logs(conn, cacheid)
    close_db(conn)

    return g_l

def get_logs(conn, cacheid):
    """ get logs from db """

    cacheid = cacheid.upper()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logbook, users where logbook.accountid = users.accountid and " +
                   "cacheid = ? ORDER BY logid DESC", (cacheid,))

    g_arr = "["
    for row in cursor:
        output = {}
        output['cacheid'] = row[0]
        output['logid'] = row[1]
        output['accountid'] = row[2]
        output['logtype'] = row[3]
        output['logimage'] = row[4]
        output['logtext'] = htmlcode.cache_images(row[5], SESSION)
        output['created'] = datetime.datetime.fromtimestamp(row[6]).strftime('%Y-%m-%d')
        output['visited'] = datetime.datetime.fromtimestamp(row[7]).strftime('%Y-%m-%d')
        output['accountid'] = row[8]
        output['username'] = row[9]
        output['accountguid'] = row[10]
        output['avatarimage'] = row[11]
        output['findcount'] = row[12]
        output['hidecount'] = row[13]
        output['images'] = get_images(conn, row[1])

        g_arr += json.dumps(output) + ","

    cursor.close()
    close_db(conn)

    if g_arr[-1:] == ",":
        g_arr = g_arr[:-1]
    g_arr += "]"

    return g_arr

def get_user(conn, accountid):
    """ Get user from the database """

    cursor = conn.cursor()
    cursor.execute("SELECT * from users where accountid = ?", (accountid,))
    ret = cursor.fetchone()
    cursor.close()

    if ret is not None and ret[0] != "":
        user = users.Users()
        user.accountid = ret[0]
        user.username = ret[1]
        user.accountguid = ret[2]
        user.avatarimage = ret[3]
        user.findcount = ret[4]
        user.hidecount = ret[5]
        row = user

    else:
        row = None

    return row

def get_log(conn, logid):
    """ Get a logbook entry """

    cursor = conn.cursor()
    cursor.execute("SELECT * from logbook where logid = ?", (logid,))
    ret = cursor.fetchone()
    cursor.close()

    if ret is not None and ret[0] != "":
        l_b = logbook.LogBook()
        l_b.cacheid = ret[0]
        l_b.logid = ret[1]
        l_b.accountid = ret[2]
        l_b.logtype = ret[3]
        l_b.logimage = ret[4]
        l_b.logtext = htmlcode.cache_images(ret[5], SESSION)
        l_b.created = ret[6]
        l_b.visited = ret[7]
        row = l_b

    else:
        row = None

    return row

def get_markers():
    """ Get all marker locations from the sqlite db """
    conn = mysqlite.check_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM geocaches")

    startcol = -1

    g_arr = "["
    for row in cursor:
        html = HTMLParser()
        g_c = geocache.GeoCache()
        # print(row[startcol + 1])
        g_c.cacheid = row[startcol + 1]
        g_c.dltime = int(time.time()) - int(row[startcol + 2])
        try:
            g_c.cachename = unescape(row[startcol + 3])
        except AttributeError as ae:
            g_c.cachename = row[startcol + 3]
        g_c.cacheowner = row[startcol + 4]
        g_c.cacheurl = row[startcol + 5]
        g_c.cachesize = row[startcol + 6]
        g_c.cachetype = row[startcol + 7]
        g_c.lat = row[startcol + 8]
        g_c.lon = row[startcol + 9]
        g_c.diff = row[startcol + 10]
        g_c.terr = row[startcol + 11]
        g_c.hidden = row[startcol + 12]
        g_c.lastfound = row[startcol + 13]
        g_c.short = "" #row[startcol + 14]
        g_c.body = "" #row[startcol + 15]
        g_c.hint = "" #row[startcol + 16]
        g_c.found = row[startcol + 17]
        g_arr += str(g_c) + ","

    cursor.close()
    close_db(conn)

    if g_arr[-1:] == ",":
        g_arr = g_arr[:-1]
    g_arr += "]"

    return g_arr

def get_json_row(cacheid):
    """ return a row as json """

    cacheid = cacheid.upper()
    conn = mysqlite.check_db()
    g_c = get_row(conn, cacheid)
    close_db(conn)

    if g_c is None:
        return "{}"

    html = HTMLParser()
    g_c.cachename = unescape(g_c.cachename)
    g_c.dltime = int(time.time()) - int(g_c.dltime)
    g_c.body = htmlcode.remove_all_attrs_except(g_c.body)

    return str(g_c)

def distance_on_unit_sphere(lat1, lon1, lat2, lon2):
    """ Distance in km between 2 points on a sphere """

    degrees_to_radians = math.pi / 180.0
    rho = 6373.00224

    phi1 = (90.0 - lat1) * degrees_to_radians
    phi2 = (90.0 - lat2) * degrees_to_radians

    theta1 = lon1 * degrees_to_radians
    theta2 = lon2 * degrees_to_radians

    cos = (math.sin(phi1) * math.sin(phi2) * math.cos(theta1 - theta2) + 
           math.cos(phi1) * math.cos(phi2))
    arc = math.acos(cos)

    return rho * arc

def get_azimuth(lat1, lon1, lat2, lon2):
    return Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)['azi1']

def from_decimal(deg, ll):
    sign = ""

    if deg >= 0:
        degrees = math.floor(deg)
    else:
        degrees = math.ceil(deg)

    minutes = round((deg - degrees) * 60, 3)

    if ll == "lat":
        if degrees < 0:
            sign = "S"
        else:
            sign = "N"
    else:
        if degrees < 0:
            sign = "W"
        else:
            sign = "E"

    return sign + " " + str(abs(degrees)) + "° " + str(abs(minutes)) + "'"

def stored_age(dlage):
    age = ""

    if dlage < 3600:
        age = str(int(round(dlage / 60)))
        age = age + " minutes ago"
    elif dlage < 86400:
        age = str(int(round(dlage / 3600)))
        age = age + " hours ago"
    else:
        age = str(int(round(dlage / 86400)))
        age = age + " days ago"

    return age

def html_filter(mystr):
    mystr = mystr.replace("\n", "")
    mystr = mystr.replace("\r", "")
    mystr = mystr.replace("<br>", "\n")
    mystr = mystr.replace("<br />", "\n")
    mystr = mystr.replace("</br>", "")
    mystr = mystr.replace("<br/>", "\n")
    mystr = mystr.replace('rel="nofollow"', "")
    mystr = mystr.replace('target="_blank"', "")
    mystr = mystr.replace("<p>", "")
    mystr = mystr.replace("</p>", "\n\n")

    return mystr

def html_log(log):
    fnfcolor = "#f0e442"

    if log['logtype'] == "Found it":
        fnfcolor = "#3eb34f"
    elif log['logtype'] == "Didn't find it":
        fnfcolor = "#ed3146"
    elif log['logtype'] == "Temporarily Disable Listing":
        log['logtype'] = "Disabled"
    elif log['logtype'] == "Owner Maintenance":
        log['logtype'] = "Maintainance"
    elif log['logtype'] == "Enable Listing":
        log['logtype'] = "Enabled"
    elif log['logtype'] == "Publish Listing":
        log['logtype'] = "Published"

    html = "<tr><td colspan='3'><b>" + log['username'] + "</b></td></tr>\n"
    html += "<tr><td style='white-space:nowrap'>" + log['visited'] + "</td>\n"
    html += "<td rowspan='3' style='width:10px;background-color:" + fnfcolor + "'>&nbsp;</td>\n"
    html += "<td rowspan='4'>" + log['logtext'] + "</td></tr>\n"
    html += "<tr><td style='white-space:nowrap'>" + log['logtype'] + "</td></tr>\n"
    html += "<tr><td style='white-space:nowrap'>" + str(log['findcount']) + " caches</td>"
    html += "<tr><td>&nbsp;</td><td>&nbsp;</td></tr>\n"
    return html

def get_html_logs(cacheid):
    html = "<html><body><table>"
    logs = json.loads(get_json_logs(cacheid))
    for log in logs:
        html += html_log(log)

    html += "</table></body></html>"
    return html
