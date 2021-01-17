#!/usr/bin/python3

""" Sqlite wrapper """

import os
import sqlite3
import util

DBBASE = os.environ.get("HOME", "/tmp") + "/.config/geocachingapp/"

def check_db():
    """ check if the database exists and create if it doesn't exist """
    os.makedirs(DBBASE, exist_ok=True)
    filename = DBBASE + "/geocaches.db"

    if not os.path.exists(filename):
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS geocaches " +
                       "(cacheid TEXT NOT NULL PRIMARY KEY, " +
                       "dltime INTEGER, cachename TEXT, cacheowner TEXT, " +
                       "cacheurl TEXT, cachesize TEXT, cachetype TEXT, lat REAL, lon REAL, " +
                       "diff REAL, terr REAL, hidden INTEGER, lastfound INTEGER, " +
                       "short TEXT, body TEXT, hint TEXT, found INTEGER NOT NULL)")

        cursor.execute("CREATE TABLE IF NOT EXISTS attributes " +
                       "(cacheid TEXT NOT NULL, attribute TEXT NOT NULL)")

        cursor.execute("CREATE TABLE IF NOT EXISTS logbook (cacheid TEXT NOT NULL, " +
                       "logid INTEGER NOT NULL, accountid INTEGER, logtype TEXT, " +
                       "logimage TEXT, logtext TEXT, created INTEGER, visited INTEGER)")

        cursor.execute("CREATE TABLE IF NOT EXISTS users (accountid INTEGER PRIMARY KEY, " +
                       "username TEXT, accountguid TEXT, avatarimage TEXT, findcount INTEGER, " +
                       "hidecount INTEGER)")

        cursor.execute("CREATE TABLE IF NOT EXISTS cacheimages (cacheid TEXT NOT NULL, " +
                       "accountid INTEGER, logid INTEGER, imageid INTEGER PRIMARY KEY, " +
                       "filename TEXT, created INTEGER, name TEXT, descr TEXT)")

        cursor.execute("CREATE INDEX IF NOT EXISTS attributes_cacheid ON attributes(cacheid)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS attributes_unique ON " +
                       "attributes(cacheid, attribute)")
        cursor.execute("CREATE INDEX IF NOT EXISTS logbook_cacheid ON logbook(cacheid)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS logbook_unique ON " +
                       "logbook(cacheid, logid)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS cacheimages_unique ON " +
                       "cacheimages(cacheid, logid, imageid)")
        conn.commit()
        cursor.close()
    else:
        conn = sqlite3.connect(filename)

    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE geocaches ADD COLUMN found INTEGER NOT NULL")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    cursor.close()

    return conn

def get_row(conn, cacheid):
    """ get one row from the geocaches table """

    cursor = conn.cursor()
    cursor.execute("SELECT * from geocaches where cacheid=?", (cacheid,))
    ret = cursor.fetchone()
    cursor.close()
    return ret

def delete_row(conn, cacheid):
    """ delete row from the geocaches table """

    cursor = conn.cursor()
    cursor.execute("DELETE from geocaches where cacheid=?", (cacheid,))
    cursor.execute("DELETE FROM attributes WHERE cacheid = ?", (cacheid,))
    conn.commit()
    cursor.close()
    return "Delete cache ID: " + cacheid

def add_to_db(conn, cache, attributes):
    """ Add or update the database with new data """

    cursor = conn.cursor()
    row = util.get_row(conn, cache.cacheid)
    if row is not None and row.cacheid != "":
        cursor.execute("UPDATE geocaches set dltime = ?, cachename = ?, cacheowner = ?, " +
                       "cacheurl = ?, cachesize = ?, cachetype = ?, lat = ?, lon = ?, " +
                       "diff = ?, terr = ?, lastfound = ?, short = ?, body = ?, hint = ?, " +
                       "found = ? WHERE cacheid = ?", \
                       (cache.dltime, cache.cachename, cache.cacheowner, cache.cacheurl, \
                       cache.cachesize, cache.cachetype, cache.lat, cache.lon, \
                       cache.diff, cache.terr, cache.lastfound, cache.short, cache.body, \
                       cache.hint, cache.found, cache.cacheid))
    else:
        cursor.execute("INSERT INTO geocaches (cacheid, dltime, cachename, cacheowner, " +
                       "cacheurl, cachesize, cachetype, lat, lon, diff, terr, lastfound, " +
                       "hidden, short, body, hint, found) " +
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", \
                       (cache.cacheid, cache.dltime, cache.cachename, cache.cacheowner, \
                       cache.cacheurl, cache.cachesize, cache.cachetype, cache.lat, \
                       cache.lon, cache.diff, cache.terr, cache.lastfound, \
                       cache.hidden, cache.short, cache.body, cache.hint, cache.found))

    if attributes is not None:
        cursor.execute("DELETE FROM attributes WHERE cacheid = ?", (cache.cacheid,))
        for attribute in attributes:
            cursor.execute("INSERT INTO attributes (cacheid, attribute) VALUES (?, ?)", \
                           (cache.cacheid, attribute))

    conn.commit()
    cursor.close()


def get_attributes(conn, cacheid):
    """ return all attributes for a geocache """

    cacheid = cacheid.upper()
    attributes = []
    cursor = conn.cursor()

    cursor.execute("SELECT attribute from attributes where cacheid=?", (cacheid,))
    for row in cursor.fetchall():
        attributes.append(row[0])

    cursor.close()
    return attributes
