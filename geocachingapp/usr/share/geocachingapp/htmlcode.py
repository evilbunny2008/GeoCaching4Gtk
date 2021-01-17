#!/usr/bin/python3

""" html functions wrapper """

import files
from bs4 import BeautifulSoup, NavigableString

def strip_html(src):
    """ strip html tags """

    parser = BeautifulSoup(src, "html.parser")
    text = parser.findAll(text=lambda text: isinstance(text, NavigableString))

    return u" ".join(text)

def remove_all_attrs_except(soup):
    """ Only allow a small number of html tags """

    whitelist = ['a', 'img', 'br', 'p'] #, 'span', 'strong', 'em', 'font']
    soup = BeautifulSoup(soup, "html.parser")
    for tag in soup.find_all(True):
        if tag.name not in whitelist:
            tag.hidden = True
    soup = str(soup)
    return soup

def cache_images(html, session):
    """ find all images and store them locally """

    data = BeautifulSoup(html, "html.parser")
    for image in data.findAll('img'):
        replacement = files.cache_image(image['src'], session)
        html = html.replace(image['src'], replacement)

    return html

def decdeg2dm(lat, lon):
    """ Decimal degrees to degrees and decimal minutes """

    lat = float(lat)
    lon = float(lon)

    if lat > 0:
        cardinal_lat = 'N'
    else:
        lat = -lat
        cardinal_lat = 'S'

    if lon > 0:
        cardinal_lon = 'E'
    else:
        lon = -lon
        cardinal_lon = 'W'

    latdeg = int(lat)
    latmin = (lat - int(lat)) * 60

    londeg = int(lon)
    lonmin = (lon - int(lon)) * 60

    loc = "%c+%2d°+%02.3f'+%c+%03d°+%02.3f'" % \
          (cardinal_lat, latdeg, latmin, cardinal_lon, londeg, lonmin)
    return loc

def switchem(from_ll, to_ll):
    """ rotate the from and to latlong """

    tmp = from_ll
    from_ll = to_ll
    to_ll = tmp
    return from_ll, to_ll
