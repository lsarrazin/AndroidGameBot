#!/usr/bin/python3
# This program is licensed under GPLv3.
from os import path
import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import GObject, Gst, Gtk

# Needed for get_xid(), set_window_handle()
from gi.repository import GdkX11, GstVideo

# Needed for timestamp on file output
from datetime import datetime
#GObject.threads_init()

Gst.init(None)
location = '/dev/video0'

class Player(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Liveview")
        self.connect('destroy', self.quit)
        self.set_default_size(800, 450)

        # Create DrawingArea for video widget
        self.drawingarea = Gtk.DrawingArea()

        # Create a grid for the DrawingArea and buttons
        grid = Gtk.Grid()
        self.add(grid)
        grid.attach(self.drawingarea, 0, 1, 2, 1)
        # Needed or else the drawing area will be really small (1px)
        self.drawingarea.set_hexpand(True)
        self.drawingarea.set_vexpand(True)

        # Quit button
        quit = Gtk.Button(label="Quit")
        quit.connect("clicked", Gtk.main_quit)
        grid.attach(quit, 0, 0, 1, 1)

        # Record/Stop button
        self.record = Gtk.Button(label="Record")
        self.record.connect("clicked", self.record_button)
        grid.attach(self.record, 1, 0, 1, 1)

        # Create GStreamer pipeline
        self.pipeline = Gst.parse_launch("v4l2src device=" + location + " ! tee name=tee ! queue name=videoqueue ! deinterlace ! xvimagesink")

        # Create bus to get events from GStreamer pipeline
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::eos', self.on_eos)
        bus.connect('message::error', self.on_error)

        # This is needed to make the video output in our DrawingArea:
        bus.enable_sync_message_emission()
        bus.connect('sync-message::element', self.on_sync_message)

    def run(self):
        self.show_all()
        self.xid = self.drawingarea.get_property('window').get_xid()
        self.pipeline.set_state(Gst.State.PLAYING)
        Gtk.main()

    def quit(self, window):
        self.pipeline.set_state(Gst.State.NULL)
        Gtk.main_quit()

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            msg.src.set_window_handle(self.xid)

    def on_eos(self, bus, msg):
        print('on_eos(): seeking to start of video')
        self.pipeline.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            0
        )


    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())


    def start_record(self):
        # Filename (current time)
        filename = datetime.now().strftime("%Y-%m-%d_%H.%M.%S") + ".avi"
        print(filename)
        self.recordpipe = Gst.parse_bin_from_description("queue name=filequeue ! jpegenc ! avimux ! filesink location=" + filename, True)
        self.pipeline.add(self.recordpipe)
        self.pipeline.get_by_name("tee").link(self.recordpipe)
        self.recordpipe.set_state(Gst.State.PLAYING)

    def stop_record(self):
        filequeue = self.recordpipe.get_by_name("filequeue")
        filequeue.get_static_pad("src").add_probe(Gst.PadProbeType.BLOCK_DOWNSTREAM, self.probe_block)
        self.pipeline.get_by_name("tee").unlink(self.recordpipe)
        filequeue.get_static_pad("sink").send_event(Gst.Event.new_eos())
        print("Stopped recording")

    def record_button(self, widget):
        if self.record.get_label() == "Record":
            self.record.set_label("Stop")
            self.start_record()
        else:
            self.stop_record()
            self.record.set_label("Record")

    def probe_block(self, pad, buf):
        print("blocked")
        return True

p = Player()
p.run()
