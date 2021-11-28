
import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, Gtk, GObject, Gdk, GdkPixbuf
from gi.repository import GdkX11, GstVideo

import numpy as np
from Xlib.display import Display

import cairo

import sys
from datetime import datetime 
import time

from PIL import Image

from Device.AndroidDevice import AndroidDevice


Gst.init(None)

class BotAppWindow(Gtk.ApplicationWindow):

    v4l2loop_location = '/dev/video0'

    img_minw = 1140
    img_curwidth = img_minw
    img_minh = 540
    img_curheight = img_minh

    pix_screenshot = None
    box_select = []
    
    def on_delete_event(self, *args):
        return self.do_delete_event(args)


    def on_destroy(self, *args):
        return self.quit_bot()


    def on_start_device(self, *args):
        print('Start device')
        pass


    def on_stop_device(self, *args):
        print('Stop device')
        pass


    def on_pause_screenshots(self, *args):
        self.do_pause_screenshots()
        pass

    
    def on_screenshot_event(self, box, event):
        ctxid = self.stb_status.get_context_id('Mouse')
        self.stb_status.push(ctxid, str(event.type) + ' @ ' + str(int(event.x)) + ':' + str(int(event.y)))

        if event.type == Gdk.EventType.BUTTON_PRESS:
            x = int(event.x)
            y = int(event.y)
            self.box_select = [ x, y, 0, 0 ]
            self.dar_screenshot.queue_draw()

        elif event.type == Gdk.EventType.MOTION_NOTIFY:
            x0 = self.box_select[0]
            y0 = self.box_select[1]
            x1 = int(event.x) - x0
            y1 = int(event.y) - y0
            self.box_select = [ x0, y0, x1, y1 ]
            self.dar_screenshot.queue_draw()

        pass


    def on_screenshot_draw(self, dar, cr):
        if self.pix_screenshot is not None:
            Gdk.cairo_set_source_pixbuf(cr, self.pix_screenshot, 0, 0)
            cr.paint()

        if len(self.box_select) == 4:
            cr.set_source_rgb(255, 0, 0)
            cr.rectangle(*self.box_select)
            cr.stroke()

        pass


    def on_btn_start_clicked(self, *args):
        self.pipeline.set_state(Gst.State.PLAYING)
        pass


    def on_btn_pause_clicked(self, *args):
        self.do_refresh_screenshot()
        self.pipeline.set_state(Gst.State.NULL)
        pass


    def on_btn_stop_clicked(self, *args):
        self.pipeline.set_state(Gst.State.NULL)
        pass


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        builder = Gtk.Builder()
        builder.add_from_file("UI/GameBotUI.glade")

        #builder.connect_signals(self.AppWindowHandler(self))

        self.app = self.props.application
        self.device = AndroidDevice()

        self.window = builder.get_object("wnd_main")
        self.window.connect('delete-event', self.on_delete_event)
        self.window.connect('destroy', self.on_destroy)
        
        self.evt_screenshot = builder.get_object("evt_screenshot")
        self.evt_screenshot.connect('event', self.on_screenshot_event)

        self.dar_screenshot = builder.get_object("dar_screenshot")
        self.dar_screenshot.set_size_request(self.img_minw, self.img_minh)
        self.dar_screenshot.connect('draw', self.on_screenshot_draw)

        builder.get_object("btn_start").connect('clicked', self.on_btn_start_clicked)
        builder.get_object("btn_pause").connect('clicked', self.on_btn_pause_clicked)
        builder.get_object("btn_stop").connect('clicked', self.on_btn_stop_clicked)

        self.stb_status = builder.get_object("stb_statusbar")

        self.window.show_all()

        self.autosave = False
        self.set_status("Initializing...")

        self.paused = False
        #GObject.timeout_add(1000, self.do_update_screenshot)

        # Create GStreamer pipeline
        self.pipeline = Gst.parse_launch("v4l2src device=" + self.v4l2loop_location + " ! tee name=tee ! queue name=videoqueue flush-on-eos=true ! xvimagesink name=imagesink enable-last-sample=true")

        # Create bus to get events from GStreamer pipeline
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::eos', self.on_eos)
        bus.connect('message::error', self.on_error)

        # This is needed to make the video output in our DrawingArea
        bus.enable_sync_message_emission()
        bus.connect('sync-message::element', self.on_sync_message)

        #self.xid = self.dar_screenshot.get_property('window').get_xid()
        #self.pipeline.set_state(Gst.State.PLAYING)


    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle')
            dar_wnd = self.dar_screenshot.get_property('window')
            print(dar_wnd)
            self.xid = dar_wnd.get_xid()
            print(self.xid)
            msg.src.set_window_handle(self.xid)


    def on_eos(self, bus, msg):
        print('on_eos(): seeking to start of video')
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0)


    def on_error(self, bus, msg):
        print('on_error():', msg.parse_error())
        # Try to reset src
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 0)
        self.pipeline.set_state(Gst.State.PLAYING)


        '''
        filename = str(time.time()) + ".jpg"     
        pixbuf = gtk.gdk.Pixbuf.get_from_drawable(self.movie_window.window, self.movie_window.window.get_colormap(), 0, 0, 0,0 500, 400)
        pixbuf.save(filename, "jpeg", {"quality":"100"})
        '''
        '''
        if self.paused:
            return

        # Get screenshot from device
        self.current_screenshot = self.device.get_screenshot()
        if self.autosave:
            self.save_screenshot()

        # Update screenshot widget (Original expected is 2280x1080)
        self.pix_screenshot = self.current_screenshot.scale_simple(1140, 540, GdkPixbuf.InterpType.BILINEAR)
        self.dar_screenshot.queue_draw()

        GObject.timeout_add(50, self.do_update_screenshot)
        '''


    def on_new_sample(self, sink, data):

        def gst_to_opencv(sample):
            buffer = sample.get_buffer()
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if success:
                data = map_info.data
                with open('frame.jpeg', 'wb') as snapshot:
                    snapshot.write(data)
                
            else:
                raise RuntimeError("Could not map buffer data!")
            buffer.unmap(map_info)

        sink.set_property("emit-signals", False)
        sample = sink.emit("pull-sample")
        if isinstance(sample, Gst.Sample):
            gst_to_opencv(sample)
            return Gst.FlowReturn.OK
        else:
            return Gst.FlowReturn.ERROR    


    def save_gstsample(self, sample):
        print('saving sample...')
        buffer = sample.get_buffer()
        print(buffer)
        success, map_info = buffer.map(Gst.MapFlags.READ)
        print(success, map_info)
        if success:
            data = map_info.data
            with open('frame.jpeg', 'wb') as snapshot:
                snapshot.write(data)
            
        else:
            raise RuntimeError("Could not map buffer data!")
        buffer.unmap(map_info)


    def do_refresh_screenshot(self):
        print("refresh")

        sink = self.pipeline.get_by_name('imagesink')
        print(sink)
        sample = sink.get_property("last_sample")
        print(sample)
        if isinstance(sample, Gst.Sample):
            print('new sample received:', sample)
            self.save_gstsample(sample)
            return Gst.FlowReturn.OK
        else:
            return Gst.FlowReturn.ERROR    

        """
        snappipe = self.pipeline.get_by_name('snapqueue')
        if snappipe is None:
            snappipe = Gst.parse_bin_from_description("queue name=snapqueue flush-on-eos=true ! jpegenc ! appsink name=snapsink caps=image/jpeg max-buffers=1 drop=true", True)
            self.pipeline.add(snappipe)
            snappipe.set_state(Gst.State.PLAYING)

            sink = self.pipeline.get_by_name('snapsink')
            sink.connect("new-sample", self.on_new_sample, sink)
            sink.set_property("emit-signals", True)
            self.pipeline.get_by_name("tee").link(snappipe)
        else:
            sink = self.pipeline.get_by_name('snapsink')
            sink.set_property("emit-signals", True)
        """
        pass


    def probe_block(self, pad, buf):
        print("blocked")
        return True


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


    def do_delete_event(self, event):
        d = Gtk.MessageDialog(transient_for=self, modal=True,
                              buttons=Gtk.ButtonsType.OK_CANCEL)
        d.props.text = 'Are you sure you want to quit?'
        response = d.run()
        d.destroy()

        if response == Gtk.ResponseType.OK:
            return self.quit_bot()

        return True


    def quit_bot(self):
        print('quit_bot')
        self.pipeline.set_state(Gst.State.NULL)
        self.app.quit()
        
        return True


    def do_pause_screenshots(self):
        self.paused = not self.paused
        self.set_status('Screenshot is now ' + ("paused" if self.paused else "running"))
        if not self.paused:
            self.do_update_screenshot()


    def set_status(self, message):
        ctxid = self.stb_status.get_context_id('Info')
        self.stb_status.push(ctxid, message)


    def save_screenshot(self, pixbuf):
        print("Todo: Enhance file naming")
        pixbuf.savev('screenshot_pixbuf.png', 'png', [], [])

