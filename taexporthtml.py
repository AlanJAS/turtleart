#Copyright (c) 2008-9, Walter Bender

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

import tawindow
import talogo
from sugar.activity import activity
from sugar.datastore import datastore
import os.path
import subprocess
from talogo import get_pixbuf_from_journal
from tahoverhelp import *
from gettext import gettext as _

def save_html(self, tw, embed_flag=True):

    self.embed_images = embed_flag
    try:
        self.datapath = os.path.join(activity.get_activity_root(), "instance")
    except:
        # early versions of Sugar (656) didn't support get_activity_root()
        self.datapath = os.path.join( \
            os.environ['HOME'], \
            ".sugar/default/org.laptop.TurtleArtActivity/instance")

    # dictionary defines the html wrappers around template elements
    # start of block, end of block
    self.html_glue = {
        'doctype': ("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 \
Transitional//EN\" \"http://www.w3.org/TR/html4/loose.dtd\">\n", ""),
        'html': ("<html>\n", "</html>\n"),
        'head': ("<head>\n<!-- Created by Turtle Art -->\n", \
             "</head>\n"),
        'meta': ("<meta http-equiv=\"content-type\" content=\"text/html; \
charset=UTF-8\">\n", ""),
        'title': ("<title>", "</title>\n"),
        'style': ("<style type=\"text/css\">\n<!--\n","-->\n</style>\n"),
        'body': ("<body>\n", "\n</body>\n"),
        'div': ("<div>\n", "</div>\n"),
        'slide': ("\n<a name=\"slide", "\"></a>\n"),
        'h1': ("<h1>", "</h1>\n"),
        'table': ("<table cellpadding=\"10\">\n", "</table>\n"),
        'tr': ("<tr>\n", "</tr>\n"),
        'td': ("<td valign=\"top\" width=\"400\" height=\"300\">\n", \
             "\n</td>\n"),
        'img': ("<img width=\"400\" height=\"300\" alt=\"Image\" src=\"image",\
             ".png\" />\n"),
        'img2': ("<img alt=\"Image\" src=\"image", ".png\" />\n"),
        'ul': ("<table>\n", "</table>\n"),
        'li': ("<tr><td>", "</td></tr>\n") }

    if self.embed_images == True:
        # store images in-line as base64
        self.html_glue['img'] = ("<img width=\"400\" height=\"300\" alt=\"Image\" src=\"data:image/png;base64,\n", " \"/>\n")
        self.html_glue['img2'] = ("<img alt=\"Image\" src=\"data:image/png;base64,\n", " \"/>\n")

    bs = tawindow.blocks(tw)
    code = ""
    self.imagecount = 0 # incremented for each image
    slidecount = 0 # incremented for each template (slide)
    for b in bs:
         this_stack = ""
         data = walk_stack(self, tw, b)
         show = 0
         tp1, tp2, tp3, tp8, tp6, tp7 = 0,0,0,0,0,0
         for d in data:
             if type(d) is float or type(d) is int:
                 d = str(d) # convert floats and ints to strings
             # transalate some Turtle Art blocks into HTML
             #     show and template blocks
             # ignores most turtle graphics
             if d == "show": # show bricks take one argument
                 show = 1
             elif d == "container": # containers hold a media block
                 show = 2
             elif show > 0: # process the argument to show or container
                 if show == 1: # could be media or a string
                     if d[0:8] == '#smedia_': # show media
                         this_stack += add_image(self,d)
                     elif d[0:8] == '#sdescr_': # show description
                         this_stack += add_description(self,d)
                     elif d[0:2] == '#s': # show a string
                         this_stack += d[2:]
                         show = 0
                     else:
                         this_stack += d
                 show = 0
             # process slide templates
             elif d == "tp1":
                 tp1 = 1
             elif d == "tp2":
                 tp2 = 1
             elif d == "tp3":
                 tp3 = 8
             elif d == 'tp8':
                 tp8 = 1
             elif d == "tp6":
                 tp6 = 1
             elif d == "tp7":
                 tp7 = 1
             elif tp3 > 0: # bullets
                 if tp3 == 8: # title comes first
                     tmp = self.html_glue['slide'][0] + \
                           str(slidecount) + \
                           self.html_glue['slide'][1] + \
                           self.html_glue['div'][0] + \
                           self.html_glue['h1'][0] + \
                           d[2:] + \
                           self.html_glue['h1'][1] + \
                           self.html_glue['ul'][0]
                     slidecount += 1
                 elif d[2:] != "": # process bullets
                     tmp = self.html_glue['li'][0] + d[2:] + \
                           self.html_glue['li'][1]
                 this_stack += tmp
                 tmp = ""
                 bullets -= 1
                 if bullets == 0:
                     this_stack += (self.html_glue['ul'][1] + \
                                    self.html_glue['div'][1])
             elif tp1 == 1 or tp2 == 1 or tp8 == 1 or\
                  tp6 == 1 or tp7 == 1:
                 # first time through, process title
                 this_stack += (self.html_glue['slide'][0] + \
                                str(slidecount) + \
                                self.html_glue['slide'][1] + \
                                self.html_glue['div'][0] + \
                                self.html_glue['h1'][0] + d[2:] + \
                                self.html_glue['h1'][1] + \
                                self.html_glue['table'][0])
                 if tp1 > 0: tp1 += 1
                 elif tp2 > 0: tp2 += 1
                 elif tp8 > 0: tp8 += 1
                 elif tp6 > 0: tp6 += 1
                 elif tp7 > 0: tp7 += 1
                 slidecount += 1
             elif tp1 > 1 or tp6 > 1:
                 tmp = self.html_glue['tr'][0] + \
                       self.html_glue['td'][0]
                 if d[0:8] == '#smedia_':
                     tmp += (add_image(self,d) + \
                             self.html_glue['td'][1] + \
                             self.html_glue['td'][0] + \
                             add_description(self,d) + \
                             self.html_glue['td'][1] + \
                             self.html_glue['tr'][1])
                 elif d[0:8] == '#sdescr_':
                     tmp += (add_description(self,d) + \
                             self.html_glue['td'][1] + \
                             self.html_glue['tr'][1])
                 if tp1 > 1 or tp6 > 2:
                     this_stack += (tmp + self.html_glue['table'][1] + \
                                self.html_glue['div'][1])
                     tp1 = 0
                     tp6 = 0
                 else:
                     this_stack += tmp
                     tp6 += 1
             elif tp8 > 1:
                 tmp = self.html_glue['tr'][0] + \
                       self.html_glue['td'][0]
                 if d[0:8] == '#smedia_':
                     tmp += (add_image(self,d) + \
                             self.html_glue['td'][1] + \
                             self.html_glue['tr'][1])
                 elif d[0:8] == '#sdescr_':
                     tmp += (add_description(self,d) + \
                             self.html_glue['td'][1] + \
                             self.html_glue['tr'][1])
                 this_stack += (tmp + self.html_glue['table'][1] + \
                                self.html_glue['div'][1])
                 tp8 = 0
             elif tp2 > 1 or tp7 > 1:             
                 if tp2 == 2 or tp7 == 2:
                     tmp = self.html_glue['tr'][0] + \
                           self.html_glue['td'][0]
                 else:
                     tmp += self.html_glue['td'][0]
                 if tp2 == 2:
                     saved_description = add_description(self,d)
                 if tp2 == 2 or tp7 == 2:
                     if d[0:8] == '#smedia_':
                         tmp += (add_image(self,d) + \
                                 self.html_glue['td'][1])
                     elif d[0:8] == '#sdescr_':
                         tmp += (add_description(self,d) + \
                                 self.html_glue['td'][1])
                     if tp2 > 1: tp2 += 1
                     elif tp7 > 1: tp7 += 1
                 elif tp2 == 3:
                     if tmp == "":
                     if d[0:8] == '#smedia_':
                         tmp += add_image(self,d)
                     elif d[0:8] == '#sdescr_':
                         tmp += add_description(self,d)
                     tmp += (self.html_glue['td'][1] + \
                             self.html_glue['tr'][1] + \
                             self.html_glue['tr'][0] + \
                             self.html_glue['td'][0])
                     tmp += saved_description
                     saved_desciption = ""
                     tmp += (self.html_glue['td'][1] + \
                             self.html_glue['td'][0])
                     tmp += (add_description(self,d) + \
                             self.html_glue['td'][1] + \
                             self.html_glue['tr'][1])
                     this_stack += (tmp + self.html_glue['table'][1] + \
                            self.html_glue['div'][1])
                     tp2 = 0
                 elif tp7 == 3:
                     if d[0:8] == '#smedia_':
                         tmp += add_image(self,d)
                     elif d[0:8] == '#sdescr_':
                         tmp += add_description(self,d)
                     tmp += (self.html_glue['td'][1] + \
                             self.html_glue['tr'][1] + \
                             self.html_glue['tr'][0])
                     tp7 += 1
                 elif tp7 == 4:
                     if d[0:8] == '#smedia_':
                         tmp += add_image(self,d)
                     elif d[0:8] == '#sdescr_':
                         tmp += add_description(self,d)
                     tmp += (self.html_glue['td'][1])
                     tp7 += 1
                 elif tp7 == 5:
                     if d[0:8] == '#smedia_':
                         tmp += add_image(self,d)
                     elif d[0:8] == '#sdescr_':
                         tmp += add_description(self,d)
                     tmp += (self.html_glue['td'][1] + \
                             self.html_glue['tr'][1])
                     this_stack += (tmp + self.html_glue['table'][1] + \
                                    self.html_glue['div'][1])
                     tp7 = 0

         if len(data) > 0:
             code += this_stack

    """
    if no show or template blocks were present, we've got no slides,
    so save a screendump instead
    """
    if slidecount == 0:
        # save a screen dump instead
        filename = os.path.join(self.datapath, 'image.png')
        tawindow.save_pict(tw,filename)
        # if the embed_images flag is True
        # embed_images base64 into the html
        if self.embed_images == True:
            base64 = os.path.join(self.datapath, 'base64tmp')
            cmd = "base64 <" + filename + " >" + base64
            subprocess.check_call(cmd, shell=True)
            f = open( base64, 'r')
            imgdata = f.read()
            f.close()
            code += (self.html_glue['img'][0] + \
                        imgdata + \
                        self.html_glue['img'][1])
            code += (self.html_glue['div'][0])
            # get a json dump of the code
            code += (tawindow.save_string(tw,False))
            code += (self.html_glue['div'][1])
    code = self.html_glue['doctype'][0] + \
           self.html_glue['html'][0] + \
           self.html_glue['head'][0] + \
           self.html_glue['meta'][0] + \
           self.html_glue['title'][0] + \
           _("Turtle Art") + " " + tw.activity.metadata['title'] + \
           self.html_glue['title'][1] + \
           self.html_glue['style'][0] + \
           self.html_glue['style'][1] + \
           self.html_glue['head'][1] + \
           self.html_glue['body'][0] + \
           code + \
           self.html_glue['body'][1] + \
           self.html_glue['html'][1]
    return code

def walk_stack(self, tw, spr):
    top = tawindow.find_top_block(spr)
    if spr == top:
        # only walk the stack if the block is the top block
        return talogo.run_blocks(tw.lc, top, tawindow.blocks(tw), False)
    else:
        # not top of stack, then return empty list
        return []

def add_image(self, d):
    if d[8:] != "None":
        try:
            dsobject = datastore.get(d[8:])
            pixbuf = get_pixbuf_from_journal(dsobject,400,300)
            filename = os.path.join(self.datapath, 'image' + \
                                    str(self.imagecount) + ".png")
            pixbuf.save(filename, "png")
            # if the embed_images flag is True
            # embed images base64 into the html
            if self.embed_images == True:
                base64 = os.path.join(self.datapath, 'base64tmp')
                cmd = "base64 <" + filename + " >" + base64
                subprocess.check_call(cmd, shell=True)
                f = open( base64, 'r')
                imgdata = f.read()
                f.close()
            tmp = self.html_glue['img2'][0]
            if self.embed_images == True:
                tmp += imgdata
            else:
                tmp += str(self.imagecount)
            self.imagecount += 1
            tmp += self.html_glue['img2'][1]
            return tmp
        except:
            return ""
    return ""

def add_description(self, d):
    # show description
    if d[8:] != "None":
        try:
            dsobject = datastore.get(d[8:])
            return dsobject.metadata['description']
        except:
            return ""
    return ""
