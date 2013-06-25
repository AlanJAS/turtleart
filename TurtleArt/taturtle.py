# -*- coding: utf-8 -*-
#Copyright (c) 2010-13 Walter Bender

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import os

import gtk
import gobject
import cairo

from random import uniform
from math import sin, cos, pi, sqrt

from taconstants import (TURTLE_LAYER, DEFAULT_TURTLE_COLORS, DEFAULT_TURTLE,
                         COLORDICT)
from tasprite_factory import SVG, svg_str_to_pixbuf
from tacanvas import wrap100, COLOR_TABLE
from sprites import Sprite
from tautils import (debug_output, data_to_string, round_int, get_path,
                     image_to_base64)

SHAPES = 36
DEGTOR = pi / 180.
RTODEG = 180. / pi


def generate_turtle_pixbufs(colors):
    ''' Generate pixbufs for generic turtles '''
    shapes = []
    svg = SVG()
    svg.set_scale(1.0)
    for i in range(SHAPES):
        svg.set_orientation(i * 10)
        shapes.append(svg_str_to_pixbuf(svg.turtle(colors)))
    return shapes


class Turtles:

    def __init__(self, turtle_window):
        ''' Class to hold turtles '''
        self.turtle_window = turtle_window
        self.sprite_list = turtle_window.sprite_list
        self.width = turtle_window.width
        self.height = turtle_window.height
        self.dict = {}
        self._default_pixbufs = []
        self._active_turtle = None
        self._default_turtle_name = DEFAULT_TURTLE

    def get_turtle(self, turtle_name, append=False, colors=None):
        ''' Find a turtle '''
        if turtle_name in self.dict:
            return self.dict[turtle_name]
        elif not append:
            return None
        else:
            if colors is None:
                Turtle(self, turtle_name)
            elif isinstance(colors, (list, tuple)):
                Turtle(self, turtle_name, colors)
            else:
                Turtle(self, turtle_name, colors.split(','))
            return self.dict[turtle_name]

    def get_turtle_key(self, turtle):
        ''' Find a turtle's name '''
        for turtle_name in iter(self.dict):
            if self.dict[turtle_name] == turtle:
                return turtle_name
        return None

    def turtle_count(self):
        ''' How many turtles are there? '''
        return(len(self.dict))

    def add_to_dict(self, turtle_name, turtle):
        ''' Add a new turtle '''
        self.dict[turtle_name] = turtle

    def remove_from_dict(self, turtle_name):
        ''' Delete a turtle '''
        if turtle_name in self.dict:
            del(self.dict[turtle_name])

    def show_all(self):
        ''' Make all turtles visible '''
        for turtle_name in iter(self.dict):
            self.dict[turtle_name].show()

    def spr_to_turtle(self, spr):
        ''' Find the turtle that corresponds to sprite spr. '''
        for turtle_name in iter(self.dict):
            if spr == self.dict[turtle_name].spr:
                return self.dict[turtle_name]
        return None

    def get_pixbufs(self):
        ''' Get the pixbufs for the default turtle shapes. '''
        if self._default_pixbufs == []:
            self._default_pixbufs = generate_turtle_pixbufs(
                ["#008000", "#00A000"])
        return(self._default_pixbufs)

    def turtle_to_screen_coordinates(self, pos):
        ''' The origin of turtle coordinates is the center of the screen '''
        return [self.width / 2.0 + pos[0], self._invert_y_coordinate(pos[1])]

    def screen_to_turtle_coordinates(self, pos):
        ''' The origin of the screen coordinates is the upper-left corner '''
        return [pos[0] - self.width / 2.0, self._invert_y_coordinate(pos[1])]

    def _invert_y_coordinate(self, y):
        ''' Positive y goes up in turtle coordinates, down in sceeen
        coordinates '''
        return self.height / 2.0 - y

    def reset_turtles(self):
        for turtle_name in iter(self.dict):
            self.set_turtle(turtle_name)
            if not self._active_turtle.get_remote():
                self._active_turtle.set_color(0)
                self._active_turtle.set_shade(50)
                self._active_turtle.set_gray(100)
                self._active_turtle.set_pen_size(5)
                self._active_turtle.reset_shapes()
                self._active_turtle.set_heading(0.0)
                self._active_turtle.set_pen_state(False)
                self._active_turtle.move_turtle((0.0, 0.0))
                self._active_turtle.set_pen_state(True)
                self._active_turtle.set_fill(False)
                self._active_turtle.hide()
        self.set_turtle(self._default_turtle_name)

    def set_turtle(self, turtle_name, colors=None):
        ''' Select the current turtle and associated pen status '''
        if turtle_name not in self.dict:
            # if it is a new turtle, start it in the center of the screen
            self._active_turtle = self.get_turtle(turtle_name, True, colors)
            self._active_turtle.set_heading(0.0, False)
            self._active_turtle.set_xy((0.0, 0.0), False, pendown=False)
            self._active_turtle.set_pen_state(True)
        elif colors is not None:
            self._active_turtle = self.get_turtle(turtle_name, False)
            self._active_turtle.set_turtle_colors(colors)
        else:
            self._active_turtle = self.get_turtle(turtle_name, False)
        self._active_turtle.show()
        self._active_turtle.set_color(share=False)
        self._active_turtle.set_gray(share=False)
        self._active_turtle.set_shade(share=False)
        self._active_turtle.set_pen_size(share=False)
        self._active_turtle.set_pen_state(share=False)

    def set_default_turtle_name(self, name):
        self._default_turtle_name = name

    def get_default_turtle_name(self):
        return self._default_turtle_name

    def set_active_turtle(self, active_turtle):
        self._active_turtle = active_turtle

    def get_active_turtle(self):
        return self._active_turtle


class Turtle:

    def __init__(self, turtles, turtle_name, turtle_colors=None):
        ''' The turtle is not a block, just a sprite with an orientation '''
        self.turtles = turtles
        self.spr = None
        self.hidden = False
        self.shapes = []
        self.custom_shapes = False
        self.type = 'turtle'
        self.name = turtle_name
        self.remote = False
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0
        self.half_width = 0
        self.half_height = 0
        self.pen_shade = 50
        self.pen_color = 0
        self.pen_gray = 100
        self.pen_size = 5
        self.pen_state = True
        self.pen_fill = False
        self.pen_poly_points = []
        self.label_block = None

        self._prep_shapes(turtle_name, self.turtles, turtle_colors)

        # Create a sprite for the turtle in interactive mode.
        if turtles.sprite_list is not None:
            self.spr = Sprite(self.turtles.sprite_list, 0, 0, self.shapes[0])

            self.half_width = int(self.spr.rect.width / 2.0)
            self.half_height = int(self.spr.rect.height / 2.0)

            # Choose a random angle from which to attach the turtle
            # label to be used when sharing.
            angle = uniform(0, pi * 4 / 3.0)  # 240 degrees
            width = self.shapes[0].get_width()
            radius = width * 0.67
            # Restrict the angle to the sides: 30-150; 210-330
            if angle > pi * 2 / 3.0:
                angle += pi / 2.0  # + 90
                self.label_xy = [int(radius * sin(angle)),
                                 int(radius * cos(angle) + width / 2.0)]
            else:
                angle += pi / 6.0  # + 30
                self.label_xy = [int(radius * sin(angle) + width / 2.0),
                                 int(radius * cos(angle) + width / 2.0)]

        self.turtles.add_to_dict(turtle_name, self)

    def set_remote(self):
        self.remote = True

    def get_remote(self):
        return self.remote

    def _prep_shapes(self, name, turtles=None, turtle_colors=None):
        # If the turtle name is an int, we'll use a palette color as the
        # turtle color
        try:
            int_key = int(name)
            use_color_table = True
        except ValueError:
            use_color_table = False

        if turtle_colors is not None:
            self.colors = turtle_colors[:]
            self.shapes = generate_turtle_pixbufs(self.colors)
        elif use_color_table:
            fill = wrap100(int_key)
            stroke = wrap100(fill + 10)
            self.colors = ['#%06x' % (COLOR_TABLE[fill]),
                           '#%06x' % (COLOR_TABLE[stroke])]
            self.shapes = generate_turtle_pixbufs(self.colors)
        else:
            if turtles is not None:
                self.colors = DEFAULT_TURTLE_COLORS
                self.shapes = turtles.get_pixbufs()

    def set_turtle_colors(self, turtle_colors):
        ''' reset the colors of a preloaded turtle '''
        if turtle_colors is not None:
            self.colors = turtle_colors[:]
            self.shapes = generate_turtle_pixbufs(self.colors)
            self.set_heading(self.heading, share=False)

    def set_shapes(self, shapes, i=0):
        ''' Reskin the turtle '''
        n = len(shapes)
        if n == 1 and i > 0:  # set shape[i]
            if i < len(self.shapes):
                self.shapes[i] = shapes[0]
        elif n == SHAPES:  # all shapes have been precomputed
            self.shapes = shapes[:]
        else:  # rotate shapes
            if n != 1:
                debug_output("%d images passed to set_shapes: ignoring" % (n),
                             self.turtles.turtle_window.running_sugar)
            if self.heading == 0.0:  # rotate the shapes
                images = []
                w, h = shapes[0].get_width(), shapes[0].get_height()
                nw = nh = int(sqrt(w * w + h * h))
                for i in range(SHAPES):
                    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, nw, nh)
                    context = cairo.Context(surface)
                    context = gtk.gdk.CairoContext(context)
                    context.translate(nw / 2.0, nh / 2.0)
                    context.rotate(i * 10 * pi / 180.)
                    context.translate(-nw / 2.0, -nh / 2.0)
                    context.set_source_pixbuf(shapes[0], (nw - w) / 2.0,
                                              (nh - h) / 2.0)
                    context.rectangle(0, 0, nw, nh)
                    context.fill()
                    images.append(surface)
                self.shapes = images[:]
            else:  # associate shape with image at current heading
                j = int(self.heading + 5) % 360 / (360 / SHAPES)
                self.shapes[j] = shapes[0]
        self.custom_shapes = True
        self.show()

    def reset_shapes(self):
        ''' Reset the shapes to the standard turtle '''
        if self.custom_shapes:
            self.shapes = generate_turtle_pixbufs(self.colors)
            self.custom_shapes = False

    def set_heading(self, heading, share=True):
        ''' Set the turtle heading (one shape per 360/SHAPES degrees) '''
        try:
            self.heading = heading
        except (TypeError, ValueError):
            debug_output('bad value sent to %s' % (__name__),
                         self.turtles.turtle_window.running_sugar)
            return
        self.heading %= 360

        i = (int(self.heading + 5) % 360) / (360 / SHAPES)
        if not self.hidden and self.spr is not None:
            try:
                self.spr.set_shape(self.shapes[i])
            except IndexError:
                self.spr.set_shape(self.shapes[0])

        if self.turtles.turtle_window.sharing() and share:
            event = 'r|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              round_int(self.heading)]))
            self.turtles.turtle_window.send_event(event)

    def set_color(self, color=None, share=True):
        ''' Set the pen color for this turtle. '''
        # Special case for color blocks
        if color is not None and color in COLORDICT:
            self.set_shade(COLORDICT[color][1], share)
            self.set_gray(COLORDICT[color][2], share)
            if COLORDICT[color][0] is not None:
                self.set_color(COLORDICT[color][0], share)
                color = COLORDICT[color][0]
            else:
                color = self.pen_color

            try:
                self.pen_color = color
            except (TypeError, ValueError):
                debug_output('bad value sent to %s' % (__name__),
                             self.turtles.turtle_window.running_sugar)
                return

        self.turtles.turtle_window.canvas.set_fgcolor(shade=self.pen_shade,
                                                      gray=self.pen_gray,
                                                      color=self.pen_color)

        if self.turtles.turtle_window.sharing() and share:
            event = 'c|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              round_int(self.pen_color)]))
            self.turtles.turtle_window.send_event(event)

    def set_gray(self, gray=None, share=True):
        ''' Set the pen gray level for this turtle. '''
        if gray is not None:
            try:
                self.pen_gray = gray
            except (TypeError, ValueError):
                debug_output('bad value sent to %s' % (__name__),
                             self.turtles.turtle_window.running_sugar)
                return

        if self.pen_gray < 0:
            self.pen_gray = 0
        if self.pen_gray > 100:
            self.pen_gray = 100

        self.turtles.turtle_window.canvas.set_fgcolor(shade=self.pen_shade,
                                                      gray=self.pen_gray,
                                                      color=self.pen_color)

        if self.turtles.turtle_window.sharing() and share:
            event = 'g|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              round_int(self.pen_gray)]))
            self.turtles.turtle_window.send_event(event)

    def set_shade(self, shade=None, share=True):
        ''' Set the pen shade for this turtle. '''
        if shade is not None:
            try:
                self.pen_shade = shade
            except (TypeError, ValueError):
                debug_output('bad value sent to %s' % (__name__),
                             self.turtles.turtle_window.running_sugar)
                return

        self.turtles.turtle_window.canvas.set_fgcolor(shade=self.pen_shade,
                                                      gray=self.pen_gray,
                                                      color=self.pen_color)

        if self.turtles.turtle_window.sharing() and share:
            event = 's|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              round_int(self.pen_shade)]))
            self.turtles.turtle_window.send_event(event)

    def set_pen_size(self, pen_size=None, share=True):
        ''' Set the pen size for this turtle. '''
        if pen_size is not None:
            try:
                self.pen_size = max(0, pen_size)
            except (TypeError, ValueError):
                debug_output('bad value sent to %s' % (__name__),
                             self.turtles.turtle_window.running_sugar)
                return

        self.turtles.turtle_window.canvas.set_pen_size(self.pen_size)

        if self.turtles.turtle_window.sharing() and share:
            event = 'w|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              round_int(self.pen_size)]))
            self.turtles.turtle_window.send_event(event)

    def set_pen_state(self, pen_state=None, share=True):
        ''' Set the pen state (down==True) for this turtle. '''
        if pen_state is not None:
            self.pen_state = pen_state

        if self.turtles.turtle_window.sharing() and share:
            event = 'p|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              self._pen_state]))
            self.turtles.turtle_window.send_event(event)

    def set_fill(self, state=False):
        self.pen_fill = state
        if not self.pen_fill:
            self.poly_points = []

    def set_poly_points(self, poly_points=None):
        if poly_points is not None:
            self.poly_points = poly_points[:]

    def start_fill(self):
        self.pen_fill = True
        self.poly_points = []

    def stop_fill(self, share=True):
        self.pen_fill = False
        if len(self.poly_points) == 0:
            return

        self.turtles.turtle_window.canvas.fill_polygon(self.poly_points)

        if self.turtles.turtle_window.sharing() and share:
            shared_poly_points = []
            for p in self.poly_points:
                shared_poly_points.append(
                    (self.turtles.screen_to_turtle_coordinates(p)))
                event = 'F|%s' % (data_to_string(
                        [self.turtles.turtle_window.nick, shared_poly_points]))
            self.turtles.turtle_window.send_event(event)
        self.poly_points = []

    def hide(self):
        if self.spr is not None:
            self.spr.hide()
        if self.label_block is not None:
            self.label_block.spr.hide()
        self.hidden = True

    def show(self):
        if self.spr is not None:
            self.spr.set_layer(TURTLE_LAYER)
            self.hidden = False
        self.move((self.x, self.y))
        self.set_heading(self.heading)
        if self.label_block is not None:
            self.label_block.spr.set_layer(TURTLE_LAYER + 1)

    def move_turtle(self, pos=None):
        ''' Move the turtle's position '''
        if pos is None:
            pos = self.get_xy()

        self.x, self.y = pos[0], pos[1]
        self.move(pos)

    def move(self, pos):
        ''' Move the turtle's sprite '''
        # self.x, self.y = pos[0], pos[1]
        pos = self.turtles.turtle_to_screen_coordinates(pos)

        # In interactive mode, center the sprite around the turtle position
        if self.spr is not None:
            pos[0] -= self.half_width
            pos[1] -= self.half_height

            if not self.hidden and self.spr is not None:
                self.spr.move(pos)
            if self.label_block is not None:
                self.label_block.spr.move((pos[0] + self.label_xy[0],
                                           pos[1] + self.label_xy[1]))

    def right(self, degrees, share=True):
        ''' Rotate turtle clockwise '''
        try:
            self.heading += degrees
        except (TypeError, ValueError):
            debug_output('bad value sent to %s' % (__name__),
                         self.turtles.turtle_window.running_sugar)
            return
        self.heading %= 360

        if self.turtles.turtle_window.sharing() and share:
            event = 'r|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              round_int(self.heading)]))
            self.turtles.turtle_window.send_event(event)

    def _draw_line(self, old, new, pendown):
        if self.pen_state and pendown:
            self.turtles.turtle_window.canvas.set_rgb(
                self.turtles.turtle_window.canvas.fgrgb[0] / 255.,
                self.turtles.turtle_window.canvas.fgrgb[1] / 255.,
                self.turtles.turtle_window.canvas.fgrgb[2] / 255.)
            pos1 = self.turtles.turtle_to_screen_coordinates(old)
            pos2 = self.turtles.turtle_to_screen_coordinates(new)
            self.turtles.turtle_window.canvas.draw_line(pos1[0], pos1[1],
                                                        pos2[0], pos2[1])
            if self.pen_fill:
                if self.poly_points == []:
                    self.poly_points.append(('move', pos1[0], pos1[1]))
                self.poly_points.append(('line', pos2[0], pos2[1]))

    def forward(self, distance, share=True):
        scaled_distance = distance * self.turtles.turtle_window.coord_scale

        self.turtles.turtle_window.canvas.set_rgb(
            self.turtles.turtle_window.canvas.fgrgb[0] / 255.,
            self.turtles.turtle_window.canvas.fgrgb[1] / 255.,
            self.turtles.turtle_window.canvas.fgrgb[2] / 255.)

        old = self.get_xy()
        try:
            xcor = old[0] + scaled_distance * sin(self.heading * DEGTOR)
            ycor = old[1] + scaled_distance * cos(self.heading * DEGTOR)
        except (TypeError, ValueError):
            debug_output('bad value sent to %s' % (__name__),
                         self.turtles.turtle_window.running_sugar)
            return

        self._draw_line(old, (xcor, ycor), True)
        self.move_turtle((xcor, ycor))

        if self.turtles.turtle_window.sharing() and share:
            event = 'f|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              int(distance)]))
            self.turtles.turtle_window.send_event(event)

    def set_xy(self, pos, share=True, pendown=True):
        old = self.get_xy()

        try:
            xcor = pos[0] * self.turtles.turtle_window.coord_scale
            ycor = pos[1] * self.turtles.turtle_window.coord_scale
        except (TypeError, ValueError):
            debug_output('bad value sent to %s' % (__name__),
                         self.turtles.turtle_window.running_sugar)
            return

        self._draw_line(old, (xcor, ycor), pendown)
        self.move_turtle((xcor, ycor))

        if self.turtles.turtle_window.sharing() and share:
            event = 'x|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              [round_int(x), round_int(y)]]))
            self.turtles.turtle_window.send_event(event)

    def arc(self, a, r, share=True):
        ''' Draw an arc '''
        if self.pen_state:
            self.turtles.turtle_window.canvas.set_rgb(
                self.turtles.turtle_window.canvas.fgrgb[0] / 255.,
                self.turtles.turtle_window.canvas.fgrgb[1] / 255.,
                self.turtles.turtle_window.canvas.fgrgb[2] / 255.)
        try:
            if a < 0:
                pos = self.larc(-a, r)
            else:
                pos = self.rarc(a, r)
        except (TypeError, ValueError):
            debug_output('bad value sent to %s' % (__name__),
                         self.turtles.turtle_window.running_sugar)
            return

        self.move_turtle(pos)

        if self.turtles.turtle_window.sharing() and share:
            event = 'a|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              [round_int(a), round_int(r)]]))
            self.turtles.turtle_window.send_event(event)

    def rarc(self, a, r):
        ''' draw a clockwise arc '''
        r *= self.turtles.turtle_window.coord_scale
        if r < 0:
            r = -r
            a = -a
        pos = self.get_xy()
        cx = pos[0] + r * cos(self.heading * DEGTOR)
        cy = pos[1] - r * sin(self.heading * DEGTOR)
        if self.pen_state:
            npos = self.turtles.turtle_to_screen_coordinates((cx, cy))
            self.turtles.turtle_window.canvas.rarc(npos[0], npos[1], r, a,
                                                   self.heading)

            if self.pen_fill:
                if self.poly_points == []:
                    self.poly_points.append(('move', npos[0], npos[1]))
                    self.poly_points.append(('rarc', npos[0], npos[1], r,
                                             (self.heading - 180) * DEGTOR,
                                             (self.heading - 180 + a) * DEGTOR))

        self.right(a, False)
        return [cx - r * cos(self.heading * DEGTOR),
                cy + r * sin(self.heading * DEGTOR)]

    def larc(self, a, r):
        ''' draw a counter-clockwise arc '''
        r *= self.turtles.turtle_window.coord_scale
        if r < 0:
            r = -r
            a = -a
        pos = self.get_xy()
        cx = pos[0] - r * cos(self.heading * DEGTOR)
        cy = pos[1] + r * sin(self.heading * DEGTOR)
        if self.pen_state:
            npos = self.turtles.turtle_to_screen_coordinates((cx, cy))
            self.turtles.turtle_window.canvas.larc(npos[0], npos[1], r, a,
                                                   self.heading)

            if self.pen_fill:
                if self.poly_points == []:
                    self.poly_points.append(('move', npos[0], npos[1]))
                    self.poly_points.append(('larc', npos[0], npos[1], r,
                                             (self.heading) * DEGTOR,
                                             (self.heading - a) * DEGTOR))

        self.right(-a, False)
        return [cx + r * cos(self.heading * DEGTOR),
                cy - r * sin(self.heading * DEGTOR)]

    def draw_pixbuf(self, pixbuf, a, b, x, y, w, h, path, share=True):
        ''' Draw a pixbuf '''

        self.turtles.turtle_window.canvas.draw_pixbuf(
            pixbuf, a, b, x, y, w, h, self.heading)

        if self.turtles.turtle_window.sharing() and share:
            if self.turtles.turtle_window.running_sugar:
                tmp_path = get_path(self.turtles.turtle_window.activity,
                                    'instance')
            else:
                tmp_path = '/tmp'
            tmp_file = os.path.join(
                get_path(self.turtles.turtle_window.activity, 'instance'),
                'tmpfile.png')
            pixbuf.save(tmp_file, 'png', {'quality': '100'})
            data = image_to_base64(tmp_file, tmp_path)
            height = pixbuf.get_height()
            width = pixbuf.get_width()

            pos = self.screen_to_turtle_coordinates((x, y))

            event = 'P|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              [round_int(a), round_int(b),
                                               round_int(pos[0]),
                                               round_int(pos[1]),
                                               round_int(w), round_int(h),
                                               round_int(width),
                                               round_int(height),
                                               data]]))
            gobject.idle_add(self.turtles.turtle_window.send_event, event)

            os.remove(tmp_file)

    def draw_text(self, label, x, y, size, w, share=True):
        ''' Draw text '''
        w *= self.turtles.turtle_window.coord_scale
        self.turtles.turtle_window.canvas.draw_text(label, x, y, size, w,
                                                    self.heading)

        if self.turtles.turtle_window.sharing() and share:
            event = 'W|%s' % (data_to_string([self.turtles.turtle_window.nick,
                                              [label, round_int(x),
                                               round_int(y), round_int(size),
                                               round_int(w)]]))
            self.turtles.turtle_window.send_event(event)

    def get_name(self):
        return self.name

    def get_xy(self):
        return [self.x, self.y]

    def get_heading(self):
        return self.heading

    def get_color(self):
        return self.pen_color

    def get_gray(self):
        return self.pen_gray

    def get_shade(self):
        return self.pen_shade

    def get_pen_size(self):
        return self.pen_size

    def get_pen_state(self):
        return self.pen_state

    def get_fill(self):
        return self.pen_fill

    def get_poly_points(self):
        return self.poly_points

    def get_pixel(self):
        x, y = self.get_xy()
        pos = self.turtle_to_screen_coordinates((x, y))
        return self.turtles.turtle_window.canvas.get_pixel(pos[0], pos[1])
