#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# GStreamer SDK Tutorials in Python
#
#     basic-tutorial-2
#
"""
basic-tutorial-2: GStreamer concepts
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+2%3A+GStreamer+concepts
"""

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import cv2
import numpy

Gst.init(None)


image_arr = None

def gst_to_opencv(sample):
    buf = sample.get_buffer()
    caps = sample.get_caps()
    print(caps.get_structure(0).get_value('format'))
    print(caps.get_structure(0).get_value('height'))
    print(caps.get_structure(0).get_value('width'))

    print(buf.get_size())

    arr = numpy.ndarray(
        (caps.get_structure(0).get_value('height'),
         caps.get_structure(0).get_value('width'),
         3),
        buffer=buf.extract_dup(0, buf.get_size()),
        dtype=numpy.uint8)
    return arr

def new_buffer(sink, data):
    global image_arr
    sample = sink.emit("pull-sample")
    # buf = sample.get_buffer()
    # print "Timestamp: ", buf.pts
    arr = gst_to_opencv(sample)
    image_arr = arr
    return Gst.FlowReturn.OK

# Create the elements
source = Gst.ElementFactory.make("decklinksrc", "source")
convert = Gst.ElementFactory.make("videoconvert", "convert")
sink = Gst.ElementFactory.make("appsink", "sink")

# Create the empty pipeline
pipeline = Gst.Pipeline.new("test-pipeline")

if not source or not sink or not pipeline:
    print("Not all elements could be created.")
    exit(-1)


sink.set_property("emit-signals", True)
# sink.set_property("max-buffers", 2)
# # sink.set_property("drop", True)
# # sink.set_property("sync", False)

caps = Gst.caps_from_string("video/x-raw, format=(string){BGR, GRAY8}; video/x-bayer,format=(string){rggb,bggr,grbg,gbrg}")

sink.set_property("caps", caps)


sink.connect("new-sample", new_buffer, sink)

# Build the pipeline
pipeline.add(source)
pipeline.add(convert)
pipeline.add(sink)
if not Gst.Element.link(source, convert):
    print("Elements could not be linked.")
    exit(-1)

if not Gst.Element.link(convert, sink):
    print("Elements could not be linked.")
    exit(-1)

# Modify the source's properties
# HD1080 25p
source.set_property("mode", 7)
# SDI
source.set_property("connection", 0)

# Start playing
ret = pipeline.set_state(Gst.State.PLAYING)
if ret == Gst.StateChangeReturn.FAILURE:
    print("Unable to set the pipeline to the playing state.")
    exit(-1)

# Wait until error or EOS
bus = pipeline.get_bus()


# Parse message
while True:
    message = bus.timed_pop_filtered(10000, Gst.MessageType.ANY)
    # print "image_arr: ", image_arr
    if image_arr is not None:   
        cv2.imshow("appsink image arr", image_arr)
        cv2.waitKey(1)
    if message:
        if message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(("Error received from element %s: %s" % (
                message.src.get_name(), err)))
            print(("Debugging information: %s" % debug))
            break
        elif message.type == Gst.MessageType.EOS:
            print("End-Of-Stream reached.")
            break
        elif message.type == Gst.MessageType.STATE_CHANGED:
            if isinstance(message.src, Gst.Pipeline):
                old_state, new_state, pending_state = message.parse_state_changed()
                print(("Pipeline state changed from %s to %s." %
                       (old_state.value_nick, new_state.value_nick)))
        else:
            print("Unexpected message received.")

# Free resources
pipeline.set_state(Gst.State.NULL)
