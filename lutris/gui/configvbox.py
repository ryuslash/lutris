###############################################################################
## project
##
## Copyright (C) 2009 Mathieu Comandon strycore@gmail.com
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
###############################################################################

"""Widget generators and their signal handlers"""

# pylint: disable=E0611
from gi.repository import Gtk, GObject, Gdk

PADDING = 10


# pylint: disable=R0904
class Label(Gtk.Label):
    """ Standardised label for config vboxes"""
    def __init__(self, message=None):
        """ Custom init of label """
        super(Label, self).__init__(message)
        self.set_size_request(200, 30)
        self.set_alignment(0.0, 0.5)
        self.set_line_wrap(True)


# pylint: disable=R0904
# I know there are too many public methods, go complain to the Gtk developers
class ConfigVBox(Gtk.VBox):
    """ Dynamically generates a vbox built upon on a python dict. """
    def __init__(self, save_in_key, caller):
        GObject.GObject.__init__(self)
        self.options = None
        #Section of the configuration file to save options in. Can be "game",
        #"runner" or "system" self.save_in_key= save_in_key
        self.save_in_key = save_in_key
        self.caller = caller

    def generate_widgets(self):
        """ Parses the config dict and generates widget accordingly."""
        #Select what data to load based on caller.
        if self.caller == "system":
            self.real_config = self.lutris_config.system_config
        elif self.caller == "runner":
            self.real_config = self.lutris_config.runner_config
        elif self.caller == "game":
            self.real_config = self.lutris_config.game_config

        #Select part of config to load or create it.
        if self.save_in_key in self.real_config:
            config = self.real_config[self.save_in_key]
        else:
            config = self.real_config[self.save_in_key] = {}

        #Go thru all options.
        for option in self.options:
            option_key = option["option"]

            #Load value if there is one.
            if option_key in config:
                value = config[option_key]
            else:
                value = None

            #Different types of widgets.
            if option["type"] == "one_choice":
                self.generate_combobox(option_key,
                                       option["choices"],
                                       option["label"], value)
            elif option["type"] == "bool":
                self.generate_checkbox(option_key, option["label"], value)
            elif option["type"] == "range":
                self.generate_range(option_key,
                                    option["min"],
                                    option["max"],
                                    option["label"], value)
            elif option["type"] == "string":
                self.generate_entry(option_key,
                                    option["label"], value)
            elif option["type"] == "directory_chooser":
                self.generate_directory_chooser(option_key,
                                                option["label"],
                                                value)
            elif option["type"] in ("file_chooser", "single"):
                self.generate_file_chooser(option_key, option["label"], value)
            elif option["type"] == "multiple":
                self.generate_multiple_file_chooser(option_key,
                                                    option["label"], value)
            elif option["type"] == "label":
                self.generate_label(option["label"])
            else:
                raise ValueError("Unknown widget type %s" % option["type"])

    def generate_label(self, text):
        """ Generates a simple label. """
        label = Label(text)
        label.show()
        self.pack_start(label, True, True, PADDING)

    #Checkbox
    def generate_checkbox(self, option_name, label, value=None):
        """ Generates a checkbox. """
        checkbox = Gtk.CheckButton(label)
        checkbox.set_alignment(0.1, 0.5)
        if value:
            checkbox.set_active(value)
        checkbox.connect("toggled", self.checkbox_toggle, option_name)
        checkbox.show()
        self.pack_start(checkbox, True, True, PADDING * 2)

    def checkbox_toggle(self, widget, option_name):
        """ Action for the checkbox's toggled signal."""
        self.real_config[self.save_in_key][option_name] = widget.get_active()

    #Entry
    def generate_entry(self, option_name, label, value=None):
        """ Generates an entry box. """
        hbox = Gtk.HBox()
        entry_label = Label(label)
        entry_label.set_size_request(200, 30)
        entry = Gtk.Entry()
        if value:
            entry.set_text(value)
        entry.connect("changed", self.entry_changed, option_name)
        hbox.pack_start(entry_label, False, False, PADDING)
        hbox.pack_start(entry, True, True, PADDING)
        hbox.show_all()
        self.pack_start(hbox, False, True, PADDING)

    def entry_changed(self, entry, option_name):
        """ Action triggered for entry 'changed' signal. """
        entry_text = entry.get_text()
        self.real_config[self.save_in_key][option_name] = entry_text

    #ComboBox
    def generate_combobox(self, option_name, choices, label, value=None):
        """ Generates a combobox (drop-down menu). """
        hbox = Gtk.HBox()
        liststore = Gtk.ListStore(str, str)
        for choice in choices:
            if type(choice) is str:
                choice = [choice, choice]
            liststore.append(choice)
        combobox = Gtk.ComboBox.new_with_model(liststore)
        combobox.set_size_request(200, 30)
        cell = Gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)
        index = selected_index = -1
        if value:
            for choice in choices:
                if choice[1] == value:
                    selected_index = index + 1
                index = index + 1
        combobox.set_active(selected_index)
        combobox.connect('changed', self.on_combobox_change, option_name)
        label = Label(label)
        label.set_size_request(200, 30)
        hbox.pack_start(label, False, False, PADDING)
        hbox.pack_start(combobox, True, True, PADDING)
        hbox.show_all()
        self.pack_start(hbox, False, True, PADDING)

    def on_combobox_change(self, combobox, option):
        """ Action triggered on combobox 'changed' signal. """
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        option_value = model[active][1]
        self.real_config[self.save_in_key][option] = option_value

    def generate_range(self, option_name, min_val, max_val, label, value=None):
        """ Generates a ranged spin button. """
        adjustment = Gtk.Adjustment(float(min_val), float(min_val),
                                    float(max_val), 1, 0, 0)
        spin_button = Gtk.SpinButton()
        spin_button.set_adjustment(adjustment)
        if value:
            spin_button.set_value(value)
        spin_button.connect('changed',
                            self.on_spin_button_changed, option_name)
        hbox = Gtk.HBox()
        label = Label(label)
        label.set_size_request(200, 30)
        hbox.pack_start(label, True, True, 0)
        hbox.pack_start(spin_button, True, True, 0)
        hbox.show_all()
        self.pack_start(hbox, False, True, 5)

    def on_spin_button_changed(self, spin_button, option):
        """ Action triggered on spin button 'changed' signal """
        value = spin_button.get_value_as_int()
        self.real_config[self.save_in_key][option] = value

    def generate_file_chooser(self, option_name, label, value=None):
        """Generates a file chooser button to select a file"""
        hbox = Gtk.HBox()
        Gtklabel = Label(label)
        file_chooser = Gtk.FileChooserButton("Choose a file for %s" % label)
        file_chooser.set_size_request(200, 30)

        file_chooser.set_action(Gtk.FileChooserAction.OPEN)
        file_chooser.connect("file-set", self.on_chooser_file_set, option_name)
        if value:
            file_chooser.unselect_all()
            file_chooser.select_filename(value)
        hbox.pack_start(Gtklabel, False, False, PADDING)
        hbox.pack_start(file_chooser, True, True, PADDING)
        self.pack_start(hbox, False, True, PADDING)

    def generate_directory_chooser(self, option_name, label, value=None):
        """Generates a file chooser button to select a directory"""
        hbox = Gtk.HBox()
        Gtklabel = Label(label)
        directory_chooser = Gtk.FileChooserButton("Choose a directory for %s"\
                                                  % label)
        directory_chooser.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        if value:
            directory_chooser.set_current_folder(value)
        directory_chooser.connect("file-set",
                                  self.on_chooser_file_set, option_name)
        hbox.pack_start(Gtklabel, False, False, PADDING)
        hbox.pack_start(directory_chooser, True, True, PADDING)
        self.pack_start(hbox, False, True, PADDING)

    def on_chooser_file_set(self, filechooser_widget, option):
        """ Action triggered on file select dialog 'file-set' signal. """
        filename = filechooser_widget.get_filename()
        self.real_config[self.save_in_key][option] = filename

    def generate_multiple_file_chooser(self, option_name, label, value=None):
        """ Generates a multiple file selector. """
        hbox = Gtk.HBox()
        label = Label(label)
        hbox.pack_start(label, False, False, PADDING)
        self.files_chooser_dialog = Gtk.FileChooserDialog(
            title="Select files",
            parent=self.get_parent_window(),
            action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CLOSE,
                     Gtk.ResponseType.CLOSE,
                     Gtk.STOCK_ADD, Gtk.ResponseType.OK)
        )
        self.files_chooser_dialog.set_select_multiple(True)
        self.files_chooser_dialog.connect('response',
                                          self.add_files_callback, option_name)

        files_chooser_button = Gtk.FileChooserButton(self.files_chooser_dialog)
        game_path = self.lutris_config.get_path(self.runner_class)
        if game_path:
            files_chooser_button.set_current_folder(game_path)
        if value:
            files_chooser_button.set_filename(value[0])

        hbox.pack_start(files_chooser_button, True, True, 0)
        self.pack_start(hbox, False, True, PADDING)
        if value:
            self.files = value
        else:
            self.files = []
        self.files_list_store = Gtk.ListStore(str)
        for filename in self.files:
            self.files_list_store.append([filename])
        cell_renderer = Gtk.CellRendererText()
        files_treeview = Gtk.TreeView(self.files_list_store)
        files_column = Gtk.TreeViewColumn("Files", cell_renderer, text=0)
        files_treeview.append_column(files_column)
        #files_treeview.set_size_request(10, 100)
        files_treeview.connect('key-press-event', self.on_files_treeview_event)
        treeview_scroll = Gtk.ScrolledWindow()
        treeview_scroll.set_min_content_height(200)
        treeview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC,
                                   Gtk.PolicyType.AUTOMATIC)
        treeview_scroll.add(files_treeview)
        self.add(treeview_scroll)

    def on_files_treeview_event(self, _, event):
        """ Action triggered when a row is deleted from the filechooser. """
        key = event.keyval
        if key == Gdk.KEY_Delete:
            #TODO : Delete selected row
            print "you don't wanna delete this ... yet"

    def add_files_callback(self, dialog, response, option):
        """Add several files to the configuration"""
        if response == Gtk.ResponseType.OK:
            filenames = dialog.get_filenames()
            for filename in filenames:
                self.files_list_store.append([filename])
                if not filename in self.files:
                    self.files.append(filename)
        self.real_config[self.save_in_key][option] = self.files
        self.files_chooser_dialog = None