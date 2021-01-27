#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import codecs
import sys
import json
import time
import gi
import files
import util

gi.require_version('Gtk', "3.0")
gi.require_version('Notify', '0.7')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk
from gi.repository import Notify
from gi.repository import WebKit2

Notify.init("Geocaching Details")

ICON_FILE = "/usr/share/pixmaps/geocachingapp.png"

class cacheScreen(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        self.set_title('GeoCaching Details')
        self.set_default_size(400, 650)

        self.set_icon_from_file(ICON_FILE)

        mycache = json.loads(util.get_json_row(cacheid))

        header = Gtk.HeaderBar(title=mycache['cachename'])
        header.set_show_close_button(False)

        self.set_titlebar(header)

        button = Gtk.Button(label="<")
        button.connect("clicked", self.on_button_clicked) 
        header.pack_start(button)

        grid1 = Gtk.Grid()
        row = 0

        mystr = "<big><b>" + mycache['cachename'] + "</b></big>"
        row = self.add_grid_row("Cache Name:", mystr, grid1, row)

        mystr = "<big>" + mycache['cachetype'] + "</big>"
        row = self.add_grid_row("Cache Type:", mystr, grid1, row)

        mystr = "<big>" + mycache['cachesize'] + "</big>"
        row = self.add_grid_row("Cache Size:", mystr, grid1, row)

        mystr = "<big>" + mycache['cacheid'] + "</big>"
        row = self.add_grid_row("Cache ID:", mystr, grid1, row)

        fwd_az = util.get_azimuth(lat, lon, mycache['lat'], mycache['lon'])
        dist = util.distance_on_unit_sphere(lat, lon, mycache['lat'], mycache['lon'])
        mystr = "<big>" + str(int(round(dist * 1000, 0))) + "m @ " + \
                            str(int(round(fwd_az, 0))) + "&#176;</big>"
        row = self.add_grid_row("Distance:", mystr, grid1, row)

        mystr = "<big>" + str(float(mycache['diff'])) + "/5.0</big>"
        row = self.add_grid_row("Difficulty:", mystr, grid1, row)

        mystr = "<big>" + str(float(mycache['terr'])) + "/5.0</big>"
        row = self.add_grid_row("Terrain:", mystr, grid1, row)

        mystr = "<big>" + mycache['cacheowner'] + "</big>"
        row = self.add_grid_row("Owner:", mystr, grid1, row)

        mystr = time.strftime('%d %b %Y', time.localtime(mycache['hidden']))
        row = self.add_grid_row("Hidden:", mystr, grid1, row)

        date = time.strftime('%d %b %Y', time.localtime(mycache['lastfound']))
        mystr = "<big>" + date + "</big>"
        row = self.add_grid_row("Last Found:", mystr, grid1, row)

        mystr = util.from_decimal(mycache['lat'], 'lat') + " - " + \
                    util.from_decimal(mycache['lon'], 'lon')
        row = self.add_grid_row("Cache Location:", mystr, grid1, row)

        row = self.show_icons(grid1, row)

        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        agetext = util.stored_age(mycache['dltime'])
        label.set_markup("Stored in Device: " + agetext)
        grid1.attach(label, 0, row, 2, 1)
        row += 1

        logdesc = "<html><body>"
        logdesc += mycache['short'] + mycache['body'] + "<br/>\n<br/>\n"

        if mycache['hint'] != "":
            logdesc += "<b><big>Hint:</big></b><br/>\n"
            logdesc += "<div id='enc_hint' onClick='update()'>" + mycache['hint'] + "</div>"
            logdesc += "<div id='dec_hint' onClick='update()' style='display:none'>"
            logdesc += codecs.encode(mycache['hint'], 'rot_13') + "</div>"
            logdesc += "<br/><br/>"
            logdesc += """
<script type="text/javascript">
function update()
{

    if(document.getElementById('enc_hint').style.display == '')
    {
        document.getElementById('enc_hint').style.display = 'none';
        document.getElementById('dec_hint').style.display = '';
    } else {
        document.getElementById('enc_hint').style.display = '';
        document.getElementById('dec_hint').style.display = 'none';
    }
}
</script>
"""

        logdesc += "</body></html>"

        base_uri = "file:///"
        webkit1 = WebKit2.WebView()
        webkit1.load_html(logdesc, base_uri)

        logs = util.get_html_logs(cacheid)
        # print(logs)

        self.webkit = WebKit2.WebView()
        self.webkit.load_html(logs, base_uri)

        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.dlabel = Gtk.Label(label="Details")
        self.desclabel = Gtk.Label(label="Description")
        self.lblabel = Gtk.Label(label="Logbook")

        self.notebook.append_page(grid1, self.dlabel)
        self.notebook.append_page(webkit1, self.desclabel)
        self.notebook.append_page(self.webkit, self.lblabel)
        self.add(self.notebook)

    def add_grid_row(self, label1str, label2str, grid1, row):
        label1 = Gtk.Label()
        label2 = Gtk.Label()

        label1.set_markup(label1str)
        label2.set_markup(label2str)

        label1.set_halign(Gtk.Align.START)
        label2.set_halign(Gtk.Align.START)

        grid1.attach(label1, 0, row, 1, 1)
        grid1.attach(label2, 1, row, 1, 1)
        row += 1

        return row

    def show_icons(self, grid1, row):
        icons = json.loads(util.get_json_attributes(cacheid))
        counter = 0
        for icon in icons:
            if counter % 7 == 0:
                hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                grid1.attach(hbox1, 0, row, 2, 1)
                row += 1

            image = Gtk.Image()
            picfile = files.APPBASE + "/assets/attribute_" + icon.lower() + ".png"
            image.set_from_file(picfile)
            hbox1.pack_start(image, False, False, 1)
            counter += 1

        row += 1

        return row

    def on_button_clicked(self, widget):
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    n = len(sys.argv)
    if n != 4:
        print("This program isn't designed to be stand-alone")
        sys.exit(0)

    cacheid = sys.argv[1]
    lat = float(sys.argv[2])
    lon = float(sys.argv[3])

    win = cacheScreen()
    win.show_all()
    Gtk.main()
