#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'
'''утф'''

import os
import zipfile
import codecs
import xml.sax
import xml.dom.minidom

from DoDoc.OpenOffice_document import packAll
from DoDoc.OpenOffice_document import extractAll

def setAttributes(doc, node, attributes):
    if attributes:
        for k, v in attributes.items():
            node.setAttribute(k, v)

class DrawHandler(xml.sax.handler.ContentHandler):
    tag_page        = "draw:page"
    tag_frame       = "draw:frame"
    tag_connector   = "draw:connector"
    tag_shape       = "draw:custom-shape"
    tag_path        = "draw:path"

    def __init__(self):
        self.pages = []
        self.doc = xml.dom.minidom.Document()
        self.node = None

    def startElement(self, name, attrs):
        if self.node == None:
            self.node = self.doc.createElement(name)
            self.doc.appendChild(self.node)
        else:
            self.node = self.node.appendChild(self.doc.createElement(name))
        setAttributes(self.doc, self.node, attrs)
        if name == self.tag_page:
            self.page = { 'blocks' : {} }

    def endElement(self, name):
        if name == self.tag_page:
            self.pages.append(self.page)
        elif name == self.tag_frame:
            self.page[Frame(self.node)] = self.node.cloneNode(True)
        elif name == self.tag_connector:
            self.page[Connector(self.node)] = self.node.cloneNode(True)
        elif name == self.tag_shape:
            shape = CustomShape(self.node)
            self.page[shape] = self.node.cloneNode(True)
            self.page['blocks'][shape.id] = shape
        elif name == self.tag_path:
            shape = CustomShape(self.node)
            self.page[shape] = self.node.cloneNode(True)
            self.page['blocks'][shape.id] = shape
            #print '+', shape.id
        self.node = self.node.parentNode
        if self.node == self.doc.firstChild:
            pages = list(self.pages)
            for i, page in enumerate(self.pages):
                #print 'blocks:', page['blocks'].keys()
                for item in page.iterkeys():
                    if hasattr(item, 'updateShape_ids'):
                        value = page[item]
                        old_item = item
                        item.updateShape_ids(page['blocks'])
                        #print item.identity()
                        pages[i].pop(old_item)
                        pages[i][item] = value
            self.pages = pages

    def characters(self, content):
        self.node.appendChild(self.doc.createTextNode(content))


class AltHandler(xml.sax.handler.ContentHandler):
    tag_page      = "draw:page"
    tag_frame     = "draw:frame"
    tag_connector = "draw:connector"
    tag_shape     = "draw:custom-shape"

    def __init__(self, diff):
        self.diff = diff
        self.added = set(self.diff['add'])
        self.page_id = -1
        self.doc = xml.dom.minidom.Document()
        self.node = None
        self.name_id = 1
        self.overridens = {}

    def startElement(self, name, attrs):
        if self.node == None:
            self.node = self.doc.createElement(name)
            self.doc.appendChild(self.node)
        else:
            self.node = self.node.appendChild(self.doc.createElement(name))
        setAttributes(self.doc, self.node, attrs)
        if name == self.tag_page:
            self.page_id+= 1

    def override(self):
        ancestor = self.node.getAttribute(u'draw:style-name')
        descendant = u'HL_%d' % (self.name_id)
        self.node.setAttribute(u'draw:style-name', descendant)
        self.overridens[descendant] = ancestor
        self.name_id+= 1
        #style_name = self.node.getAttribute(u'draw:style-name')
        #self.overridens.add(style_name)
        #print style_name

    def endElement(self, name):
        shapes = {
            self.tag_frame : Frame,
            self.tag_connector : Connector,
            self.tag_shape : CustomShape,
            }
        if shapes.has_key(name):
            if shapes[name](self.node) in self.added:
                self.override()
        #if name == self.tag_frame:
        #    if Frame(self.node) in self.added:
        #        self.override()
        #elif name == self.tag_connector:
        #    if Connector(self.node) in self.added:
        #        self.override()
        #elif name == self.tag_shape:
        #    if CustomShape(self.node) in self.added:
        #        self.override()
        self.node = self.node.parentNode

    def characters(self, content):
        self.node.appendChild(self.doc.createTextNode(content))


class StyleHandler(xml.sax.handler.ContentHandler):
    def __init__(self, overridens):
        #print overridens
        self.doc = xml.dom.minidom.Document()
        self.node = None
        self.overridens = overridens
        self.ancestors = dict.fromkeys(overridens.values())

    def startElement(self, name, attrs):
        if self.node == None:
            self.node = self.doc.createElement(name)
            self.doc.appendChild(self.node)
        else:
            self.node = self.node.appendChild(self.doc.createElement(name))
        setAttributes(self.doc, self.node, attrs)

    def endElement(self, name):
        if name == u'style:style':
            if self.node.getAttribute('style:name') in self.ancestors:
                self.store()
        elif name == u'office:automatic-styles':
            for desc, anc in self.overridens.iteritems():
                self.inject(desc, self.ancestors[anc])
        self.node = self.node.parentNode

    def store(self):
        self.ancestors[self.node.getAttribute('style:name')] = self.node.cloneNode(True)

    def inject(self, name, origin):
        raw_xml = u'''<tttt xmlns:style="a" xmlns:fo="b" xmlns:draw="c" xmlns:svg="d">
                        <style:graphic-properties draw:stroke="solid" svg:stroke-color="#ff0000" />
                      </tttt>'''
        content_dom = xml.dom.minidom.parseString(u''.join([a.strip() for a in raw_xml.splitlines()]).encode('utf8'))
        injection = content_dom.firstChild.firstChild.cloneNode(True)
        new_node = origin.cloneNode(True)
        new_node.setAttribute(u'style:name', name)
        new_node.appendChild(injection)
        self.node.appendChild(new_node)
        #print self.node.toxml()

    def characters(self, content):
        self.node.appendChild(self.doc.createTextNode(content))


def measure(s):
    return float(s.replace(u'cm', u''))

class Shape(object):
    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        return self.hash == other.hash

    def __cmp__(self, other):
        return cmp(self.hash, other.hash)

def getData(node):
    data = u''
    if node.hasChildNodes():
        for c in node.childNodes:
            data+= getData(c)
    if hasattr(node, 'data'):
        data+= node.data
    return data

class Frame(Shape):
    def __init__(self, node):
        svg_x      = node.getAttribute("svg:x"     )
        svg_y      = node.getAttribute("svg:y"     )
        svg_width  = node.getAttribute("svg:width" )
        svg_height = node.getAttribute("svg:height")
        self.x      = measure(svg_x     )
        self.y      = measure(svg_y     )
        self.width  = measure(svg_width )
        self.height = measure(svg_height)
        self.text = u''.join([getData(elem) for elem in node.getElementsByTagName("text:p")])
        self.hash = u''.join([svg_x, svg_y, svg_width, svg_height, self.text]).__hash__()

    def identity(self):
        return 'Frame "%s"' % (self.text)

class Connector(Shape):
    def __init__(self, node):
        svg_x1 = node.getAttribute("svg:x1")
        svg_x2 = node.getAttribute("svg:x2")
        svg_y1 = node.getAttribute("svg:y1")
        svg_y2 = node.getAttribute("svg:y2")
        self.start = node.getAttribute("draw:start-shape")
        self.end   = node.getAttribute("draw:end-shape")
        self.x1 = measure(svg_x1)
        self.x2 = measure(svg_x2)
        self.y1 = measure(svg_y1)
        self.y2 = measure(svg_y2)
        self.hash = u''.join([svg_x1, svg_y1, svg_x2, svg_y2, self.start, self.end]).__hash__()

    def updateShape_ids(self, shapes):
        #print self.start, shapes.keys()
        if shapes.has_key(self.start):
            self.start = shapes[self.start].identity()
        if shapes.has_key(self.end):
            self.end = shapes[self.end].identity()

    def identity(self):
        return 'Connector "%s => %s"' % (self.start, self.end)

class CustomShape(Shape):
    def __init__(self, node):
        svg_x      = node.getAttribute("svg:x"     )
        svg_y      = node.getAttribute("svg:y"     )
        svg_width  = node.getAttribute("svg:width" )
        svg_height = node.getAttribute("svg:height")
        self.x      = measure(svg_x     )
        self.y      = measure(svg_y     )
        self.width  = measure(svg_width )
        self.height = measure(svg_height)
        self.id        = node.getAttribute("xml:id"  )
        self.draw_name = node.getAttribute("draw:name")
        self.text = u''.join([getData(elem) for elem in node.getElementsByTagName("text:p")])
        self.hash = u''.join([svg_x, svg_y, svg_width, svg_height, self.draw_name, self.text]).__hash__()

    def identity(self):
        return 'CustomShape %s "%s"' % (self.draw_name, self.text)

def parseODG(filename):
    fd = zipfile.ZipFile(filename, 'r')
    content = fd.read("content.xml")
    fd.close()
    draw_handler = DrawHandler()
    xml.sax.parseString(content, draw_handler)
    return draw_handler.pages

def createHighlighted(standard_path, alternative_path):
    import tempfile
    temp_dir = tempfile.mkdtemp()
    standard = parseODG(standard_path)
    extractAll(alternative_path, temp_dir)
    content_xml = os.path.join(temp_dir, "content.xml")
    content = open(content_xml).read()
    alt_handler = AltHandler(modifications(standard_path, alternative_path))
    xml.sax.parseString(content, alt_handler)
    #codecs.open(content_xml, "w", "utf8").write(alt_handler.doc.toxml())

    #styles_xml = os.path.join(temp_dir, "styles.xml")
    #styles = open(styles_xml).read()
    style_handler = StyleHandler(alt_handler.overridens)
    xml.sax.parseString(alt_handler.doc.toxml(), style_handler)
    codecs.open(content_xml, "w", "utf8").write(style_handler.doc.toxml())

    fd, result = tempfile.mkstemp(suffix='.odg')
    os.fdopen(fd).close()
    packAll(temp_dir, result)

    for root, dirs, files in os.walk(temp_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

    return result

def modifications(standard_path, alternative_path):
    standard = parseODG(standard_path)
    alternative = parseODG(alternative_path)
    result = { 'add' : [], 'mod' : [], 'rem' : [] }
    for s_page, a_page in zip(standard, alternative):
        keys = set(s_page.keys()).union(a_page.keys())
        added, removed = {}, {}
        for k in keys:
            if not s_page.has_key(k):
                added[k.identity()] = k
            if not a_page.has_key(k):
                removed[k.identity()] = k
        for a in set(added.keys()).difference(set(removed.keys())):
            result['add'].append(added[a])
        for a in set(removed.keys()).difference(set(added.keys())):
            result['rem'].append(removed[a])
        for a in set(added.keys()).intersection(set(removed.keys())):
            result['mod'].append(added[a])
    return result

def printDiff(standard_path, alternative_path):
    m = modifications(standard_path, alternative_path)
    for a in m['add']:
        print 'A', a.identity()
    for a in m['rem']:
        print 'R', a.identity()
    for a in m['mod']:
        print 'M', a.identity()

def gui(standard_path, alternative_path):
    import Tix
    from Tkinter import Frame
    from Tkinter import Button
    from Tkinter import Label

    class Application(Frame):
        def diffRact(self):
            before = self.before_entry["value"]
            after  = self.after_entry["value"]
            if(os.path.splitext(before)[1].lower() == '.odg' and os.path.splitext(after)[1].lower() == '.odg'):
                result = os.path.splitext(os.path.basename(before))[0] + '_vs_' + os.path.splitext(os.path.basename(after))[0] + '.odg'
                result = createHighlighted(before, after)
                os.startfile(result)
                print 'done'

        def createWidgets(self):
            Label(self, text='Before:').grid(row=0, column=0, sticky='W')
            Label(self, text='After:').grid(row=1, column=0, sticky='W')
            self.before_entry = Tix.FileEntry(self)
            self.before_entry.grid(row=0, column=1, sticky='W')
            if(self.before_path):
                self.before_entry["value"] = self.before_path
            self.after_entry = Tix.FileEntry(self)
            self.after_entry.grid(row=1, column=1, sticky='W')
            if(self.after_path):
                self.after_entry["value"] = self.after_path
            b_ok = Button(self, text='diffRact')
            b_ok.grid(row=2, columnspan=2, sticky='E')
            b_ok["command"] = self.diffRact

        def __init__(self, standard_path = None, alternative_path = None, master=None):
            Frame.__init__(self, master)
            self.grid()
            self.before_path = standard_path
            self.after_path  = alternative_path
            self.createWidgets()

    root = Tix.Tk()
    app = Application(standard_path, alternative_path, master=root)
    app.mainloop()
    #root.destroy()

def main():
    import sys
    if len(sys.argv) == 3:
        os.startfile(createHighlighted(sys.argv[1], sys.argv[2]))
    else:
        print 'Usage:'
        print '    python odgDiff before.odg after.odg'
        before, after = None, None #'dn_jd_1.odg', 'dn_jd_2.odg'
        gui(before, after)
    #modifications(before, after)
    #printDiff(before, after)
    #createHighlighted(before, after)

if __name__ == '__main__':
    main()
