#!/usr/bin/python2

##
# This file is part of pyFidget, licensed under the MIT License (MIT).
#
# Copyright (c) 2016 Wolf480pl <wolf480@interia.pl>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
##

import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo, os
from time import time, sleep
import threading

def mkMatrix(p0, p1, p2, size):
    w, h = size
    w, h = float(w), float(h)
    x0, y0 = p0
    if p1:
        x1, y1 = p1
        dx1, dy1 = x1 - x0, y1 - y0
        ex1, ey1 = dx1 / w, dy1 / w
    else:
        ex1, ey1 = 1, 0
    if p2:    
        x2, y2 = p2
        dx2, dy2 = x2 - x0, y2 - y0
        ex2, ey2 = dx2 / h, dy2 / h
    else:
        ex2, ey2 = 0, 1
    
    return cairo.Matrix(ex1, ey1,
                        ex2, ey2,
                        x0 , y0 )

def toShapeMap(surface):
    if not os.name=="nt":
	#surface.getwidth() doesn't work on windows
        width = surface.get_width()
        height = surface.get_height()
        bitmap = gtk.gdk.Pixmap(None, width, height, 1)
    else:
        bitmap = gtk.gdk.Pixmap(None, 200, 200, 1)
    bmpCr = bitmap.cairo_create()

    patt = cairo.SurfacePattern(surface)
    bmpCr.set_source(patt)
    bmpCr.set_operator(cairo.OPERATOR_SOURCE)
    bmpCr.paint()

    return bmpCr, bitmap

class Screen(gtk.DrawingArea):

    # Draw in response to an expose-event
    __gsignals__ = { "expose-event": "override" }
    
    _time = time()
    _shapemap = None

    def __init__(self, animation, texture, getFrameRect, offset):
        gtk.DrawingArea.__init__(self)
        self._fidget = animation
        self._texture = cairo.ImageSurface.create_from_png(texture)
        self._getFrameRect = getFrameRect
        self._patt = cairo.SurfacePattern(self._texture)
        self._offset = offset

    # Handle the expose-event by drawing
    def do_expose_event(self, event):
        if not hasattr(self, 'bg'):
			if self.is_composited():
				print("Composite! \o/")
				self.bg = None
			else:
				#capt_screen doesn't work properly on windows and only slows everything down
				if os.name=="nt":
					self.bg = None
				else:
					self.bg = capt_screen(self)
        # Create the cairo context
        cr = self.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()

        self.draw(cr, *self.window.get_size())

    def draw(self, cr, width, height):
        t = time()
        dt = t - self._time
        self._time = t
        dtmill = int(dt * 1000)
        self._fidget.update(dtmill)
        
        self.clear(cr)

        cr.save()
        cr.translate(*self._offset)

        if hasattr(self._fidget, 'transforms'):
            for mtx in self._fidget.transforms():
                cr.transform(cairo.Matrix(*mtx))

        for state in self._fidget.state():
            cr.save()
            mtx = self._patt.get_matrix()
            self.drawState(cr, state)
            self._patt.set_matrix(mtx)
            cr.restore()

        cr.restore()
        tgtSurface = cr.get_target()
        
        bmpCr, shapemap = toShapeMap(tgtSurface)

        self._shapemap = shapemap

        #dbgPatt = cairo.SurfacePattern(bmpCr.get_target())
        #cr.set_source(dbgPatt)
        #cr.set_operator(cairo.OPERATOR_SOURCE)
        #cr.paint()

    def shapemap(self):
        return self._shapemap

    def clear(self, cr):
        cr.save()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        if self.bg:
            bg = cairo.SurfacePattern(self.bg)
            cr.set_source(bg)
        else:
            cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.restore()

    def drawState(self, cr, state):
        ((x, y), f, p1, p2) = state
        (sx, sy, w, h) = self._getFrameRect(f)
        surf = self._patt

        mdst = mkMatrix((x, y), p1, p2, (w, h))
        cr.transform(mdst)

        m = cairo.Matrix()
        m.translate(sx, sy)
        surf.set_matrix(m)
        cr.set_source(surf)
        cr.rectangle(0, 0, w, h)
        cr.fill()

class Refresher(threading.Thread):
    def __init__(self, window):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.window = window
    
    def run(self):
        fps = 60
        tick = 1.0 / fps
        while True:
            sleep(tick)
            gtk.threads_enter()
            self.window.queue_draw()
            self.window.queue_resize()
            gtk.threads_leave()

# GTK mumbo-jumbo to show the widget in a window and quit when it's closed
def run(animation, texture, getFrameRect, size=(200, 200), offset=(0, 0)):
    gtk.threads_init()
    gtk.threads_enter()
    
    window = gtk.Window()

    widget = Screen(animation, texture, getFrameRect, offset)
    widget.show()

    def on_size_allocate(wind, rect):
        #print("walloc")
        shapemap = widget.shapemap()
        if shapemap:
            window.input_shape_combine_mask(shapemap, 0, 0)
            #window.reset_shapes()
            #print("walloc with bitmap")        

    window.connect("delete-event", gtk.main_quit)
    window.connect("size-allocate", on_size_allocate)
    window.add(widget)
    window.set_decorated(False)
    window.set_skip_taskbar_hint(True)
    window.set_skip_pager_hint(True)
    window.set_keep_above(True)
    window.stick()
    window.set_default_size(*size)	
	
	#the other function doesn't work on windows
	#which sadly means that transparency doesn't work on windows
    if os.name=="nt":
      colormap = gtk.gdk.colormap_get_system()
    else:
      colormap = window.get_screen().get_rgba_colormap()
    gtk.widget_set_default_colormap(colormap)

    window.present()
    refresher = Refresher(window)
    refresher.start()
    try:
        gtk.main()
    finally:
        gtk.threads_leave()

def rgb24to32(data):
    itr = iter(data)
    out = bytearray()
    try:
        while True:
            r = next(itr)
            g = next(itr)
            b = next(itr)
            out.append(b)
            out.append(g)
            out.append(r)
            out.append(0)
    except StopIteration:
        pass
    return out

def capt_screen(widget):
    x, y = widget.window.get_position()
    win = gtk.gdk.get_default_root_window()
    w, h = win.get_size()
    pb = gtk.gdk.Pixbuf(0 , False, 8, w, h)
    widget.hide()
    pb = pb.get_from_drawable(win, win.get_colormap(), 0, 0, 0, 0, w, h)
    widget.show_all()
    if (pb != None):
        myw, myh = 512, 300
        pb = pb.subpixbuf(x, y, myw, myh)
        w, h = myw * 2, myh / 2
        format = cairo.FORMAT_ARGB32
        stride = cairo.ImageSurface.format_stride_for_width(format, w)
        im = cairo.ImageSurface.create_for_data(rgb24to32(pb.get_pixels()), format, w, h, stride)
        return im

import fidget

if __name__ == "__main__":
    print("This way of starting Fidget is deprecated. Please run cairoFidget.py instead.")
    run(fidget.Fidget(), "fidget-sprites.png", fidget.getFrameRect, (121, 121), (-53, -17))
