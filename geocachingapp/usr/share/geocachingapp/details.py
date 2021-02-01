#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import codecs
import sys
import json
import time
import gi
import files
import util

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', "3.0")
gi.require_version('Notify', '0.7')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Notify
from gi.repository import WebKit2

Notify.init("Geocaching Details")

ICON_FILE = "/usr/share/pixmaps/geocachingapp.png"

class cacheScreen(Gtk.ApplicationWindow):
    def __init__(self):
        Gtk.ApplicationWindow.__init__(self)

        self.set_title('GeoCaching Details')
        self.set_default_size(400, 650)

        self.set_icon_from_file(ICON_FILE)

        mycache = json.loads(util.get_json_row(cacheid))

        header = Gtk.HeaderBar(title=mycache['cachename'])
        header.set_show_close_button(False)

        self.set_titlebar(header)

        button = Gtk.MenuButton()
        header.pack_end(button)

        menumodel = Gio.Menu()
        menumodel.append("Log Visit", "win.log_visit")
        menumodel.append("Open in Browser", "win.browser")
        # menumodel.append("Quit", "win.quit")
        button.set_menu_model(menumodel)

        log_visit_action = Gio.SimpleAction.new("log_visit", None)
        log_visit_action.connect("activate", self.log_visit_callback)
        self.add_action(log_visit_action)

        browser_action = Gio.SimpleAction.new("browser", None)
        browser_action.connect("activate", self.browser_callback)
        self.add_action(browser_action)

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

    def log_visit_callback(self, action, parameter):
        log = logScreen()
        log.show_all()

    def browser_callback(self, action, parameter):
        Gtk.show_uri_on_window(None,
                               "https://www.geocaching.com/geocache/" + cacheid,
                               Gdk.CURRENT_TIME)

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

class logScreen(Gtk.ApplicationWindow):
    def __init__(self):
        Gtk.ApplicationWindow.__init__(self)

        self.set_title('GeoCaching Log')
        self.set_default_size(400, 650)

        self.set_icon_from_file(ICON_FILE)

        mycache = json.loads(util.get_json_row(cacheid))

        header = Gtk.HeaderBar(title=mycache['cachename'])
        header.set_show_close_button(False)

        self.set_titlebar(header)

        button = Gtk.Button(label="<")
        button.connect("clicked", self.on_button_clicked)
        header.pack_start(button)

        self.placeholderStr = "Log text goes here..."

        vbox = Gtk.VBox()
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, True, 0)
        self.add(vbox)

        store = Gtk.ListStore(str)
        store.append(["Found It"])
        store.append(["Didn't Find It"])
        store.append(["Write Note"])

        renderer_text = Gtk.CellRendererText()
        self.combobox1 = Gtk.ComboBox.new_with_model(store)
        self.combobox1.set_name('combobox1')
        self.combobox1.pack_start(renderer_text, True)
        self.combobox1.add_attribute(renderer_text, "text", 0)
        self.combobox1.set_active(0)
        hbox.pack_start(self.combobox1, True, False, 6)

        store = Gtk.ListStore(str)
        store.append(["Today"])
        store.append(["Yesterday"])

        renderer_text = Gtk.CellRendererText()
        self.combobox2 = Gtk.ComboBox.new_with_model(store)
        self.combobox2.set_name('combobox2')
        self.combobox2.pack_start(renderer_text, True)
        self.combobox2.add_attribute(renderer_text, "text", 0)
        hbox.pack_start(self.combobox2, True, False, 6)
        self.combobox2.set_active(0)

        self.textview = Gtk.TextView()
        self.textview.set_name("textview1")
        self.textview.connect("focus-in-event", self.onFocusIn)
        self.textview.connect("focus-out-event", self.onFocusOut)

        self.textbuffer = self.textview.get_buffer()
        self.textbuffer.set_text(self.placeholderStr)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)

        vbox.pack_start(self.textview, True, True, 5)

        button = Gtk.Button.new_with_label("Submit Log")
        button.set_name("button1")
        button.connect("clicked", self.submit_log)
        vbox.pack_start(button, False, True, 0)

        screen = Gdk.Screen.get_default()
        gtk_provider = Gtk.CssProvider()
        gtk_context = Gtk.StyleContext()
        gtk_context.add_provider_for_screen(screen, gtk_provider,
                                            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        css = "#combobox1 { font-size: 18pt; }\n"
        css += "#combobox2 { font-size: 18pt; }\n"
        css += "#textview1 { font-size: 18pt; }\n"
        css += "#button1 { font-size: 18pt; }\n"
        gtk_provider.load_from_data(bytes(css.encode()))

        self.show_all()

    def onFocusIn(self, event, something):
        logtext = self.textbuffer.get_text(self.textbuffer.get_start_iter(),
                                           self.textbuffer.get_end_iter(), True)
        if logtext == self.placeholderStr:
            self.textbuffer.set_text("")
        return False

    def onFocusOut(self, event, something):
        logtext = self.textbuffer.get_text(self.textbuffer.get_start_iter(),
                                           self.textbuffer.get_end_iter(), True)
        if logtext == "":
            self.textbuffer.set_text(self.placeholderStr)
        return False

    def submit_log(self, event):
        logtext = self.textbuffer.get_text(self.textbuffer.get_start_iter(),
                                           self.textbuffer.get_end_iter(), True).strip()
        if logtext == "" or logtext == self.placeholderStr:
            progress = Notify.Notification.new("ERROR!", "Log text can't be empty")
            progress.show()
            return

        logtype = ""
        logdate = ""

        tree_iter = self.combobox1.get_active_iter()
        if tree_iter is not None:
            model = self.combobox1.get_model()
            logtype = model[tree_iter][:2][0]

        tree_iter = self.combobox2.get_active_iter()
        if tree_iter is not None:
            model = self.combobox2.get_model()
            logdate = model[tree_iter][:2][0]

        if logtype == "" or logdate == "":
            progress = Notify.Notification.new("ERROR!",
                                               "There was a problem with the logdate or logtype")
            progress.show()
            return

        # print("util.logvisit(" + cacheid + ", " + logtype + ", " + logdate + ", " + logtext + ")")
        util.logvisit(cacheid, logtype, logdate, logtext)
        self.destroy()

    def on_button_clicked(self, widget):
        self.destroy()

if __name__ == "__main__":
    n = len(sys.argv)
    if n != 4:
        print("This program isn't designed to be stand-alone")
        sys.exit(0)

    try:
        cacheid = sys.argv[1]
        lat = float(sys.argv[2])
        lon = float(sys.argv[3])

        win = cacheScreen()
        win.show_all()
        Gtk.main()
    except Exception as e:
        print(str(e))
        sys.exit(0)
