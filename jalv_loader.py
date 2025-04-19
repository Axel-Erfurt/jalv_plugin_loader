#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_versions({'Gtk': '3.0', "Notify": "0.7"})
import subprocess
from gi.repository import Gtk, GdkPixbuf, Notify, GLib
import sys
import distutils.spawn
import warnings

warnings.filterwarnings("ignore")

Notify.init("Message")

jalv_exists = False
lv2ls_exists = False

### check jalv
if distutils.spawn.find_executable("jalv.gtk3"):
    jalv_exists = True
else:
    jalv_exists = False
    
### check lv2ls
if distutils.spawn.find_executable("lv2ls"):
    lv2ls_exists = True
else:
    lv2ls_exists = False
    
if jalv_exists == False or lv2ls_exists == False:
    n = Notify.Notification.new("Plugin Loader", "jalv or/and lv2ls not installed\nPlease install jalv and lv2ls", "dialog-error")
    Notify.Notification.set_timeout(n, 10000)
    n.show()
    sys.exit()

### get plugins
names_list = []
url_list = []

try:

    output = subprocess.check_output(['lv2ls', '-n'], text=True)
    name_list = output.splitlines()

except subprocess.CalledProcessError as e:
    print(f"Command failed with return code {e.returncode}")

try:

    output = subprocess.check_output(['lv2ls'], text=True)
    url_list = output.splitlines()

except subprocess.CalledProcessError as e:
    print(f"Command failed with return code {e.returncode}")

lv2_dict = dict(zip(name_list, url_list))


class Window(Gtk.ApplicationWindow):
    def __init__(self):
        super(Gtk.ApplicationWindow, self).__init__()
        
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        
        self.use_gtk3 = True
        
        self.set_icon_name('audio-card')
        self.connect("destroy",Gtk.main_quit)
        self.old_tag = ""

        self.header = Gtk.HeaderBar()
        self.header.set_title('Jalv Plugin Loader')
        self.header.set_subtitle(f"{len(lv2_dict)} plugins found")
        self.header.set_show_close_button(True)
        self.set_titlebar(self.header)

        self.plugin_button = Gtk.Button()
        self.plugin_button.add(
            Gtk.Image.new_from_icon_name('media-playback-start-symbolic', 2))
        self.plugin_button.set_relief(2)
        self.plugin_button.set_tooltip_text("open plugin")
        self.plugin_button.connect('clicked', self.open_plugin)
        
        ### gtk or qt5
        self.gtk_button = Gtk.Button(label="gtk3")
        self.gtk_button.set_tooltip_text("toggle jalv.gtk3 / jalv.qt5")
        self.gtk_button.connect('clicked', self.toggle_gtk)
        
        
        self.search_entry = Gtk.SearchEntry(placeholder_text = "find ...")
        self.search_entry.connect("changed", self.visible_cb)
        self.search_entry.connect("icon-press", self.read_channels)
        

        self.header.add(self.plugin_button) 
        self.header.add(self.gtk_button)        
        self.header.pack_end(self.search_entry)

        self.model = Gtk.ListStore(object)
        self.model.set_column_types((str, str, GdkPixbuf.Pixbuf))

        self.icon_view = Gtk.IconView()
        self.icon_view.set_model(model=self.model)
        self.icon_view.set_item_width(-1)
        self.icon_view.set_text_column(0)
        self.icon_view.set_pixbuf_column(2)
        self.icon_view.set_activate_on_single_click(True)
        self.icon_view.connect('item-activated', self.show_info)

        scroll = Gtk.ScrolledWindow()
        scroll.add(self.icon_view)
        
        vbox = Gtk.VBox(spacing=10)
        self.add(vbox)
        
        vbox.pack_start(scroll, True, True, 0)
        
        self.info_label = Gtk.Label()
        self.info_label.set_name("info_label")
        self.info_label.set_text("Info")
        self.info_label.set_line_wrap(True)
        self.info_label.set_line_wrap_mode(0)
        self.info_label.set_halign(Gtk.Align.CENTER)
        vbox.pack_end(self.info_label, False, True, 5)        
        
        self.read_channels()
        
        
    def toggle_gtk(self, *args):
        if self.gtk_button.get_label() == "gtk3":
            self.gtk_button.set_label("qt5")
            self.use_gtk3 = False
        else:
            self.gtk_button.set_label("gtk3")
            self.use_gtk3 = True


    def read_channels(self, *args):
        self.model.clear()
        for section in lv2_dict.items():
            icon = Gtk.IconTheme.get_default().load_icon(
                    'audio-card', 32, Gtk.IconLookupFlags.USE_BUILTIN)
            self.model.append((section[0], section[1], icon))

        
    def visible_cb(self, entry, *args):
        search_query = entry.get_text().lower()
        if search_query == "":
            self.read_channels()
        for row in self.model:
            if not search_query in row[0].lower():
                path = row.path
                iter = self.model.get_iter(path)
                self.model.remove(iter)

    def open_plugin(self, *args):
        name = self.plugin_name
        url = self.plugin_url
        print(name, url)
        self.info_label.set_text(f"... loading {name}")
        if self.use_gtk3:
            cmd = ["jalv.gtk3", url]
        else:
            cmd = ["jalv.qt5", url]
        print(cmd)
        
        try:
            r = GLib.spawn_async(cmd, flags=GLib.SPAWN_DO_NOT_REAP_CHILD | GLib.SpawnFlags.SEARCH_PATH, 
                             standard_output=True, standard_error=True)
        except GLib.Error as err:
            print("Error:", err.message)
            dialog = Gtk.MessageDialog(
                flags=0,
                title="Plugin Loader Error", 
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=err.message)
            dialog.run()
            print("Error dialog closed")

            dialog.destroy()        
        
    def show_info(self, view, path):
        self.plugin_name = self.model[path][0]
        self.plugin_url = self.model[path][1]
        self.info_label.set_text(f"{self.plugin_name} - {self.plugin_url}")
        self.header.set_subtitle(self.plugin_name)
        print(f"{self.plugin_name} - {self.plugin_url}")

        
if __name__ == '__main__':
    window = Window()
    window.resize(750, 520)
    window.move(0, 0)
    window.show_all()
    Gtk.main()
