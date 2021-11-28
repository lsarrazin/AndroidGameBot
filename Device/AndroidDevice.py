##

"""
import PIL

import mss, mss.tools

from Xlib import display, X

from Bot.Script import Script
import pyautogui
"""

import time
import subprocess

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gio, Gtk, Gdk, GdkPixbuf

from Xlib.display import Display

import numpy as np
from PIL import Image


class AndroidDevice:

    started = False

    devp_pid = 0
    devp_proc = None
    devp_cmdline = '/snap/bin/scrcpy'
    devp_width = 2280
    devp_height = 1080
    devp_cmdargs = ['-w', '--window-title', 'GameBot', '--window-width', str(devp_width), '--window_height', str(devp_height), '--window-borderless'] ## , '--always-on-top'
    
    devw_name = b'GameBot'
    devw_obj = None
    devw_geo = (0, 0, 0, 0)


    def __init__(self):
        self.display = Display()
        self.root = self.display.screen().root

    
    def start_device(self) -> bool:
        """
        Starts ScrCpy
        """
        if self.fetch_window():
            # scrcpy is already running
            return True
        else:
            # Issue scrcpy -S -w --window-title GameBot
            # scrcpy -w --window-title GameBot --window-borderless
            cmdline = [self.scrcpy_cmdline] + self.scrcpy_cmdargs
            self.scrcpy = subprocess.Popen(cmdline)
            time.sleep(2)
            self.scrpid = self.scrcpy.pid
            if self.fetch_window():
                subprocess.Popen(['wmctl', '-ir', str(self.scrwid), '-t', '1'])
            return True


    def find_window_by_name(self, name):
        NET_WM_NAME = self.display.intern_atom('_NET_WM_NAME')
        WM_NAME = self.display.intern_atom('WM_NAME') 

        screen = Gdk.get_default_root_window().get_screen()
        stack = screen.get_window_stack()
        
        for w in stack:
            win_id = w.get_xid()
            win_obj = self.display.create_resource_object('window', win_id)
            for atom in (NET_WM_NAME, WM_NAME):
                wname = win_obj.get_full_property(atom, 0)
                if wname is not None and wname.value == name:
                    self.devw_geo = w.get_geometry()
                    return w

        return None


    def find_device_window(self):
        if self.devw_obj is None:
            self.devw_obj = self.find_window_by_name(self.devw_name)
        return self.devw_obj


    def get_screenshot(self) -> GdkPixbuf:

        device_window = self.find_device_window()
        if device_window is None:
            print('not found!')
            return None

        (x, y, w, h) = self.devw_geo
        bbox = (0, 0, w, h)
        return Gdk.pixbuf_get_from_window(device_window, *bbox)


    '''
    def fetch_window(self) -> bool:
        """
        Locates, configure and bring to top scrcpy window so that it will be able to receive events
        Returns True if window located, False else
        """

        def get_absolute_geometry(win):
            """
            Returns the (x, y, height, width) of a window relative to the top-left of the screen.
            """
            geom = win.get_geometry()
            (x, y) = (geom.x, geom.y)
            while True:
                parent = win.query_tree().parent
                pgeom = parent.get_geometry()
                x += pgeom.x
                y += pgeom.y
                if parent.id == self.root.id:
                    break
                win = parent
            return (x, y, geom.height, geom.width)


        def find_window(win):
            children = win.query_tree().children
            for w in children:
                name = w.get_wm_name()
                if name == 'GameBot':
                    w.set_input_focus(X.RevertToParent, X.CurrentTime)
                    w.configure(stack_mode=X.Above)

                    self.scrwin = w
                    self.scrwid = w.id
                    self.scrgeo = get_absolute_geometry(w)
                    return True

                elif find_window(w):
                    return True

            return False
        
        return find_window(self.root)


    def fireApplication(self, name):
        # Issue adb shell monkey -p com.kingsgroup.sos 1
        pass


    def start(self, script):
        ## Todo
        pass


    def takeScreenshot(self):
        if self.fetch_window():
            time.sleep(1)
            (x, y, w, h) = self.scrgeo
            print(x, y, w, h)
            with mss.mss() as sct:
                bbox = (x, y, x+h, y+w)

                # Grab the picture
                im = sct.grab(bbox)

                image = Image.frombytes("RGB", (h, w), im.bgra, "raw", "BGRX")
                image.save('screenshot.png', 'png')
                return image
                
            return None

        else:
            print("Scrcpy window not found!")
            return None


    def touch(self, x, y):
        (xs, ys, ws, hs) = self.scrgeo
        print(xs, ys, ws, hs, x, y)
        pyautogui.click(xs+x, ys+y)
        pass
    '''