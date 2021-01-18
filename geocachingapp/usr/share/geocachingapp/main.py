#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import codecs
import files
import json
import os
import util
import time
import gi

gi.require_version('Champlain', '0.12')
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', "3.0")
gi.require_version('GtkChamplain', '0.12')
gi.require_version('GtkClutter', '1.0')
gi.require_version('Notify', '0.7')

from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import Notify
from gi.repository import GtkClutter, Clutter
from gi.repository import Champlain, GtkChamplain

GtkClutter.init([])
Notify.init("Geocaching App")

CACHE_SIZE = 100000000
MEMORY_CACHE_SIZE = 100

ICON_FILE = "/usr/share/pixmaps/geocachingapp.png"

class cacheScreen(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.ApplicationWindow.__init__(self, application=app)

        self.set_title('GeoCaching Details')
        self.set_default_size(400, 650)

        self.set_icon_from_file(ICON_FILE)

        mycache = json.loads(util.get_json_row(app.gcid))

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

        fwd_az = util.get_azimuth(app.lat, app.lon, mycache['lat'], mycache['lon'])
        dist = util.distance_on_unit_sphere(app.lat, app.lon, mycache['lat'], mycache['lon'])
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

        sc = Gtk.ScrolledWindow()
        vbox = Gtk.VBox()
        label1 = Gtk.Label()
        label1.set_hexpand(True)
        label1.set_halign(Gtk.Align.START)
        label1.set_line_wrap(True)
        label1.set_markup(util.html_filter(mycache['short']))
        vbox.pack_start(label1, False, True, 0)

        label2 = Gtk.Label()
        label2.set_hexpand(True)
        label2.set_halign(Gtk.Align.START)
        label2.set_line_wrap(True)
        label2.set_markup(util.html_filter(mycache['body']))
        vbox.pack_start(label2, False, True, 0)

        if mycache['hint'] != "":
            label3 = Gtk.Label()
            label3.set_halign(Gtk.Align.START)
            label3.set_line_wrap(True)
            label3.set_markup("<b><big>Hint:</big></b>")

            vbox.pack_start(label3, False, True, 0)

            self.hint = Gtk.Button(label=mycache['hint'])
            self.hint.set_halign(Gtk.Align.START)
            self.hint.connect("clicked", self.encode_decode)
            vbox.pack_start(self.hint, False, True, 0)

            label4 = Gtk.Label()
            label4.set_markup("\n\n")
            vbox.pack_start(label4, False, True, 0)

        sc.add_with_viewport(vbox)

        logs = json.loads(util.get_json_logs(app.gcid))
        print(logs)

        content = "<span size='x-large'>Please wait, loading " + app.gcid + "</span>"

        label = Gtk.Label()
        label.set_markup(content)

        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.dlabel = Gtk.Label(label="Details")
        self.desclabel = Gtk.Label(label="Description")
        self.lblabel = Gtk.Label(label="Logbook")

        self.notebook.append_page(grid1, self.dlabel)
        self.notebook.append_page(sc, self.desclabel)
        self.notebook.append_page(label, self.lblabel)
        self.add(self.notebook)

    def encode_decode(self, event):
        mystr = self.hint.get_label()
        secret = codecs.encode(mystr, 'rot_13')
        self.hint.set_label(secret)

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
        icons = json.loads(util.get_json_attributes(app.gcid))
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
        app.cache = None
        self.destroy()

class LoginScreen(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.ApplicationWindow.__init__(self, title="GeoCaching Login", application=app)
        self.set_title('GeoCaching Login')
        self.set_default_size(400, 650)

        self.set_icon_from_file(ICON_FILE)

        header = Gtk.HeaderBar(title="GeoCaching Login")
        header.set_show_close_button(False)

        login_button = Gtk.Button(label="Login")
        login_button.connect("clicked", self.on_login_button_clicked)

        header.pack_end(login_button)

        self.set_titlebar(header)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        label1 = Gtk.Label(label="Enter your username:")
        vbox.add(label1)

        self.username = Gtk.Entry()
        vbox.add(self.username)

        label2 = Gtk.Label(label="Enter your password:")
        vbox.add(label2)

        self.password = Gtk.Entry()
        self.password.set_visibility(False)
        vbox.add(self.password)

        if os.path.exists(files.userFile('authCreds.json')):
            with open(files.userFile('authCreds.json')) as lastone:
                auth_creds = json.loads(lastone.read())
                self.username.set_text(auth_creds['username'])
                self.password.set_text(auth_creds['password'])

    def on_login_button_clicked(self, widget):
        ret = util.gclogin(self.username.get_text(), self.password.get_text())
        if ret[0] == 1:
            state_obj = {
                'username': self.username.get_text(),
                'password': self.password.get_text()
            }
            with open(files.userFile('authCreds.json'), 'w') as outfile:
                outfile.write(json.dumps(state_obj))
            self.destroy()
        else:
            my_notify = Notify.Notification.new("Geocaching App", ret[1])
            my_notify.show()

class mainScreen(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.ApplicationWindow.__init__(self, title="GeoCaching App", application=app)
        self.set_title('Geocaching App')
        self.set_default_size(400, 650)
        self.connect('destroy', self.cleanup)

        self.set_icon_from_file(ICON_FILE)

        header = Gtk.HeaderBar(title="Geocaching App")
        header.set_show_close_button(False)
        self.set_titlebar(header)

        button = Gtk.MenuButton()
        header.pack_end(button)

        menumodel = Gio.Menu()
        menumodel.append("Download", "win.download")
        # menumodel.append("About", "win.about")
        menumodel.append("Quit", "win.quit")
        button.set_menu_model(menumodel)

        download_action = Gio.SimpleAction.new("download", None)
        download_action.connect("activate", self.download_callback)
        self.add_action(download_action)

        # about_action = Gio.SimpleAction.new("about", None)
        # about_action.connect("activate", self.about_callback)
        # self.add_action(about_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.quit_callback)
        self.add_action(quit_action)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.vbox)

        if os.path.exists(files.userFile('lastPosition.json')):
            with open(files.userFile('lastPosition.json')) as lastone:
                lastposition = json.loads(lastone.read())
                print(lastposition)
                app.lat = lastposition['lat']
                app.lon = lastposition['lon']
                app.zoom = lastposition['zoom']

        bbox = Gtk.HBox(homogeneous=False, spacing=10)
        button = Gtk.Button(stock=Gtk.STOCK_ZOOM_IN)
        button.connect("clicked", self.zoom_in)
        bbox.add(button)

        button = Gtk.Button(stock=Gtk.STOCK_ZOOM_OUT)
        button.connect("clicked", self.zoom_out)
        bbox.add(button)

        self.osmmap = GtkChamplain.Embed()
        self.view = self.osmmap.get_view()
        self.view.set_map_source(self.create_cached_source())

        self.view.center_on(app.lat, app.lon)
        self.view.set_property('zoom-level', app.zoom)

        self.vbox.add(bbox)
        self.vbox.add(self.osmmap)

        self.view.connect("notify::zoom-level", self.map_zoom_changed)
        self.view.connect("notify::state", self.map_state_changed)

        self.layer = self.create_marker_layer(self.view)
        self.view.add_layer(self.layer)

        self.display_markers()

    def add_marker(self, lat, lon, gcid, icon):
        marker = Champlain.Label.new_from_file(
            "/usr/share/geocachingapp/assets/" + icon + ".png")
        marker.set_draw_background(False)
        marker.set_location(lat, lon)
        self.layer.add_marker(marker)

        marker.set_reactive(True)
        marker.connect("button-release-event", self.marker_button_release_cb, gcid)
        marker.connect("touch-event", self.marker_touch_release_cb, gcid)

    def marker_button_release_cb(self, actor, event, gcid):
        if app.cache is not None:
            return False

        print("ID '" + gcid + "' was clicked")

        app.gcid = gcid
        app.cache = cacheScreen(app)
        app.cache.show_all()

    def marker_touch_release_cb(self, actor, event, gcid):
        if app.cache is not None:
            return False

        print("ID '" + gcid + "' was touched")

        app.gcid = gcid
        app.cache = cacheScreen(app)
        app.cache.show_all()

    def create_marker_layer(self, view):
        layer = Champlain.MarkerLayer()
        layer.set_all_markers_draggable()
        layer.show()

        return layer

    def zoom_in(self, widget):
        self.view.zoom_in()

    def zoom_out(self, widget):
        self.view.zoom_out()

    def map_zoom_changed(self, view, value):
        self.zoom = view.get_property("zoom-level")

        app.lat1 = self.view.y_to_latitude(0)
        app.lon1 = self.view.x_to_longitude(0)

        width, height = view.get_size()
        app.lat2 = self.view.y_to_latitude(height)
        app.lon2 = self.view.x_to_longitude(width)

    def map_state_changed(self, view, value):
        app.lat = view.get_property("latitude")
        app.lon = view.get_property("longitude")

        app.lat1 = self.view.y_to_latitude(0)
        app.lon1 = self.view.x_to_longitude(0)

        width, height = view.get_size()
        app.lat2 = self.view.y_to_latitude(height)
        app.lon2 = self.view.x_to_longitude(width)

    def download_callback(self, action, parameter):
        util.get_cache_list(app.lat, app.lon)
        self.display_markers()

    def display_markers(self):
        ret = util.get_markers()
        ret = json.loads(ret)

        for row in ret:
            cachetype = row['cachetype']
            if cachetype.lower() == "cache in trash out event":
                icon = "marker_type_cito"
            elif row['found'] == 1:
                icon = "marker_found"
            else:
                icon = "marker_type_" + cachetype.lower().split("-")[0].split(" ")[0]

            self.add_marker(row['lat'], row['lon'], row['cacheid'], icon)

    def quit_callback(self, action, parameter):
        self.cleanup(None)
        app.quit()

    def cleanup(self, obj):
        state_obj = {
            'lat': app.lat,
            'lon': app.lon,
            'zoom': app.zoom
        }
        with open(files.userFile('lastPosition.json'), 'w') as outfile:
            outfile.write(json.dumps(state_obj))

    def create_cached_source(self):
        map_tile_url = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/256/#Z#/#X#/#Y#"
        map_tile_url += "?access_token=pk.eyJ1IjoiZGVsdGFmb3h0cm90IiwiYSI6ImNramg2OXo1ZzRpd2Qyem5"
        map_tile_url += "wOXR5Mm01MWUifQ.5KGdqcPnw-SPU8dfn29a_Q"

        factory = Champlain.MapSourceFactory.dup_default()
        tile_source = Champlain.NetworkTileSource.new_full(
            "mapbox", "mapbox",
            " (c) mapbox (c) openstreet map contributors",
            "https://www.mapbox.com/tos",
            2, 19, 256, Champlain.MapProjection.MERCATOR,
            map_tile_url, Champlain.ImageRenderer())

        tile_size = tile_source.get_tile_size()
        error_source = factory.create_error_source(tile_size)
        file_cache = Champlain.FileCache.new_full(CACHE_SIZE, None, Champlain.ImageRenderer())

        memory_cache = Champlain.MemoryCache.new_full(MEMORY_CACHE_SIZE, Champlain.ImageRenderer())

        source_chain = Champlain.MapSourceChain()
        source_chain.push(error_source)
        source_chain.push(tile_source)
        source_chain.push(file_cache)
        source_chain.push(memory_cache)

        return source_chain

class Application(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):
        self.win = mainScreen(self)
        self.win.show_all()
        # self.login = LoginScreen(self)
        # self.login.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

if __name__ == "__main__":
    app = Application()
    app.cache = None
    app.lat = -33.8665593
    app.lon = 151.2086631
    app.zoom = 14
    app.run()
