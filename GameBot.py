#

import sys
from typing import KeysView

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gio, Gtk

import argparse

'''
from Device.AndroidDevice import AndroidDevice
from Device.ScrCpyDevice import ScrCpyDevice
from Bot.Script import Script
'''

from UI.BotAppWindow import BotAppWindow


class BotApplication(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="github.lsarrazin.AndroidGameBot",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.window = None


    def do_startup(self):
        Gtk.Application.do_startup(self)


    def do_activate(self):
        # Only a single window allowed
        if not self.window:
            self.window = BotAppWindow(application=self, title="AndroidGameBot")
            

    def do_command_line(self, command_line):
        parser = argparse.ArgumentParser(description="Android application bot")
        '''
        devgrp1 = parser.add_mutually_exclusive_group()
        devgrp1.add_argument("-m1", "--adb", help="interact with device using ADB", action="store_true")
        devgrp1.add_argument("-m2", "--scr", help="interact with device using SCRCPY", action="store_true")
        '''
        parser.add_argument("-v", "--verbosity", action="count", help="increase output verbosity", default=0)
        parser.add_argument("-t", "--test", help="test for Android connectivity", action="store_true")
        devgrp2 = parser.add_mutually_exclusive_group()
        devgrp2.add_argument("-i", "--ui", help="start with user interface", action="store_true")
        devgrp2.add_argument("-s", "--script", type=str, help="name of script to run on device")

        args = parser.parse_args()

        if args.test:
            # This is printed on the main instance
            print("Test argument recieved")

        if args.ui:
            self.activate()
            
        return 0        


if __name__ == '__main__':
    app = BotApplication()
    app.run(sys.argv)
    