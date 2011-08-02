import re
import xml.sax
import xml.dom.minidom
from pprint import pprint


TAG_TABLE = u'table:table'
TAG_ROW   = u'table:table-row'
TAG_FRAME = u'draw:frame'
TAG_IMAGE = u'draw:image'
TAG_BREAK = u'text:line-break'
TAG_SECTION = u'text:section'
SECTION_NAME = u'text:name'

def setAttributes(doc, node, attributes):
    if attributes:
        for k, v in attributes.items():
            node.setAttribute(k, v)


def iterNode(doc, node, callback):
    if node.nodeType == node.TEXT_NODE:
        callback.characters(node.wholeText)
    else:
        #print node.tagName
        callback.startElement(node.tagName, node.attributes)
        if node.hasChildNodes():
            for child in node.childNodes:
                iterNode(doc, child, callback)
        callback.endElement(node.tagName)


class Template(object):
    def __init__(self, xml_content, params):
        self.xml_content = xml_content
        self.params = params or {}

    def render(self):
        h = Template_handler(self.params)
        xml.sax.parseString(self.xml_content, h)
        result = h.resultXML()
        self.image_urls = h.imageUrls()
        return result

    def imageUrls(self):
        return self.image_urls


class Template_handler(xml.sax.handler.ContentHandler):
    def __init__(self, params = None):
        self.params = params or {}
        self.doc = xml.dom.minidom.Document()
        self.doc.encoding = "UTF-8"
        self.node = None
        self.available_handlers = [Row_handler, Image_handler, Condition_block_handler]
        self.handler = None
        self.do_not_handle = set()
        self.image_replacements = {}

    def startElement(self, name, attrs):
        #print 'START', self.node, name
        if self.handler:
            self.handler.startElement(name, attrs)
        else:
            for h in self.available_handlers:
                if name == h.handled_tag:
                    if name not in self.do_not_handle:
                        self.handler = h(self, self.params)
                        self.handler.startElement(name, attrs)
                    else:
                        #print 'ignore', name
                        break
                    return
            if self.node:
                self.node = self.node.appendChild(self.doc.createElement(name))
            else:
                self.node = self.doc.createElement(name)
                self.doc.appendChild(self.node)
            setAttributes(self.doc, self.node, attrs)

    def endElement(self, name):
        if self.handler:
            self.handler.endElement(name)
            if self.handler.isDone():
                self.__insertHandled()
        else:
            self.node = self.node.parentNode

    def characters(self, content):
        if self.handler:
            self.handler.characters(content)
            return
        text_node = self.doc.createTextNode(content)
        self.node.appendChild(text_node)

    def __insertHandled(self):
        handled_tag = self.handler.handled_tag
        rendered_root = self.handler.render()
        if rendered_root:
            self.do_not_handle.add(handled_tag)
            self.handler = None
            for child in rendered_root.childNodes:
                iterNode(self.doc, child, self)
            self.do_not_handle.remove(handled_tag)
        else:
            self.handler = None

    def resultXML(self):
        r = Replacer(self.params)
        iterNode(self.doc, self.doc.firstChild, r)
        if __name__ == '__main__':
            return r.doc.toprettyxml()
        else:
            return r.doc.toxml()

    def imageUrls(self):
        return self.image_replacements

    def moveUp_to(self, tag_name, current_node):
        # trace up to given tag
        #print 'moving up'
        self.node = self.node.appendChild(current_node)
        while not self.node.tagName == tag_name:
            #print 'move up from', self.node.tagName
            self.node = self.node.parentNode
        # handle contents
        #print self.node.toprettyxml()
        iterNode(self.doc, self.node, self.handler)
        # remove node from tree and step up
        moved_up_to_node = self.node
        self.node = self.node.parentNode
        self.node.removeChild(moved_up_to_node)


class Tag_handler(object):
    '''handled_tag - tag, that is handled by this handler'''
    handled_tag = None

    def __init__(self, master, params):
        self.master = master
        self.params = params
        self.doc = xml.dom.minidom.Document()
        self.node = None

    def startElement(self, name, attrs):
        if self.node == None:
            self.node = self.doc.createElement(name)
            self.doc.appendChild(self.node)
        else:
            self.node = self.node.appendChild(self.doc.createElement(name))
        setAttributes(self.doc, self.node, attrs)

    def endElement(self, name):
        self.node = self.node.parentNode

    def characters(self, content):
        self.node.appendChild(self.doc.createTextNode(content))

    def isDone(self):
        '''returns whether handler must be rendered'''
        raise Exception("Unimplemented method of abstract class")

    def render(self):
        '''returns 'root' node, which childs must be inserted in master tree'''
        raise Exception("Unimplemented method of abstract class")


class Row_handler(Tag_handler):
    handled_tag = TAG_ROW

    def __init__(self, master, params):
        super(Row_handler, self).__init__(master, params)

    def isDone(self):
        return self.node == self.doc

    def render(self):
        pf = Parameters_finder()
        iterNode(self.doc, self.doc.firstChild, pf)
        tables_used = set()
        for param in pf.parameters:
            data = param.split('.')
            if len(data) == 2:
                tables_used.add(param.split('.')[0])
        self.render_root = self.doc.createElement('root')
        if len(tables_used):
            for t in tables_used:
                if self.params.has_key(t):
                    row_dict = {}
                    for lines in self.params[t]:
                        for k, v in lines.iteritems():
                            row_dict['%s.%s' % (t, k)] = v
                        self.renderRow(row_dict)
        else:
            self.renderRow({})
        return self.render_root

    def renderRow(self, params):
        r = Replacer(params)
        iterNode(self.doc, self.doc.firstChild, r)
        self.render_root.appendChild(r.doc.firstChild)


class Image_handler(Tag_handler):
    handled_tag = TAG_IMAGE

    def __init__(self, master, params):
        super(Image_handler, self).__init__(master, params)
        self.placeholder_name = None
        self.marker_xlink = None
        self.moving_up = False

    def isDone(self):
        return self.node == self.doc

    def initialize(self, current_node):
        self.moving_up = True
        self.omit_ends = False
        self.entry_node = self.master.node
        self.master.moveUp_to(TAG_FRAME, current_node)
        self.moving_up = False

    def startElement(self, name, attrs):
        if self.node:
            #print 'START IMAGE', name
            self.node = self.node.appendChild(self.doc.createElement(name))
        else:
            if self.moving_up:
                #print 'START-MU IMAGE', name
                self.node = self.doc.createElement(name)
                self.doc.appendChild(self.node)
            else:
                cur_node = self.doc.createElement(name)
                setAttributes(self.doc, cur_node, attrs)
                self.initialize(cur_node)
                #print self.doc.toprettyxml()
                #self.startElement(name, attrs)
                return
        if name == TAG_FRAME:
            self.placeholder_name = attrs['draw:name'].nodeValue
        if name == TAG_IMAGE:
            self.marker_xlink = attrs['xlink:href'].nodeValue
        setAttributes(self.doc, self.node, attrs)

    def endElement(self, name):
        if self.moving_up:
            if self.node.tagName == TAG_IMAGE:
                self.omit_ends = True
            if self.omit_ends:
                return
        self.node = self.node.parentNode
        #print self.node

    def render(self):
        render_root = self.doc.createElement('root')
        if self.params.has_key(self.placeholder_name):
            images = self.params[self.placeholder_name]
            assert( type(images) in (list, tuple) )
            inserted_xlinks = []
            for image in images:
                attr_dict = {u'draw:name' : image, u'xlink:href' : image}
                r = Replacer(self.params, attr_dict)
                iterNode(self.doc, self.doc.firstChild, r)
                render_root.appendChild(r.doc.firstChild)
                inserted_xlinks.append(image)
            self.master.image_replacements[self.marker_xlink] = inserted_xlinks
        else:
            print 'NO KEY', self.placeholder_name
            render_root.appendChild(self.doc.firstChild)
        return render_root


class Condition_block_handler(Tag_handler):
    handled_tag = TAG_SECTION
    have = re.compile(ur'(?iu)have_([a-z0-9_]+)(?: .+)?')
    have_no = re.compile(ur'(?iu)have_no_([a-z0-9_]+)(?: .+)?')

    def __init__(self, master, params):
        super(Condition_block_handler, self).__init__(master, params)
        self.node = self.doc.createElement('root')
        self.doc.appendChild(self.node)

    def isDone(self):
        return self.node == self.doc.firstChild

    def render(self):
        root = self.doc.firstChild
        if root.firstChild.attributes.has_key(SECTION_NAME):
            block_name = root.firstChild.attributes[SECTION_NAME].value
            m_no = self.have_no.match(block_name)
            if m_no:
                param_name = m_no.group(1)
                if self.params.has_key(param_name):
                    if self.params[param_name] != None:
                        return None
            else:
                m = self.have.match(block_name)
                if m:
                    param_name = m.group(1)
                    if self.params.has_key(param_name):
                        if self.params[param_name] == None:
                            return None
                    else:
                        return None
        return root

class Parameters_finder(object):
    re_param = re.compile(ur'(?iu)\{([a-z0-9\._]+)\}')

    def __init__(self, doc = None):
        self.parameters = set()

    def startElement(self, name, attrs):
        pass

    def endElement(self, name):
        pass

    def characters(self, content):
        params = self.re_param.findall(content)
        for p in params:
            self.parameters.add(p)


class Replacer(object):
    re_param = re.compile(ur'(?iu)\{([a-z0-9\._]+)\}')
    BREAK_LINE = u'##LINE-BREAK-IN-REPLACEMENT##'

    def __init__(self, rdict = None, adict = None):
        self.doc = xml.dom.minidom.Document()
        self.node = None
        self.rdict = rdict or {}
        self.adict = adict or {}

    def startElement(self, name, attrs):
        if not self.node:
            self.node = self.doc.createElement(name)
            self.doc.appendChild(self.node)
        else:
            elem = self.doc.createElement(name)
            self.node = self.node.appendChild(elem)
        rattrs = {}
        if attrs:
            for key, value in attrs.items():
                if self.adict.has_key(key):
                    rattrs[key] = self.adict[key]
                else:
                    rattrs[key] = value
        setAttributes(self.doc, self.node, rattrs)

    def endElement(self, name):
        self.node = self.node.parentNode

    def replacement(self, matched):
        key = matched.group(1)
        if self.rdict.has_key(key):
            lines = [a.strip() for a in self.rdict[key].split('#BR#')]
            content = self.BREAK_LINE.join(lines)
            return unicode(content)
        else:
            return matched.group(0)

    def characters(self, content):
        rcontent = self.re_param.sub(self.replacement, content)
        lines = rcontent.split(self.BREAK_LINE)
        for i, line in enumerate(lines):
            text_node = self.doc.createTextNode(line)
            if i != 0:
                break_node = self.doc.createElement(TAG_BREAK)
                self.node.appendChild(break_node)
            self.node.appendChild(text_node)

def testTable():
    source = u'<xml><table:table><table:table-row>\
<table:table-cell><text:p>{table1.id}</text:p></table:table-cell>\
<table:table-cell><text:p>{table1.name}</text:p></table:table-cell>\
<table:table-cell><text:p>{table1.description}</text:p></table:table-cell>\
</table:table-row></table:table></xml>'''
    parameters = {
                u'table1' :
                (
                    {'id' : '1', 'name' : 'SIAM.00479', 'description' : 'Test1'},
                    {'id' : '2', 'name' : 'SIAM.00172', 'description' : 'Test2'},
                ),
            }
    t = Template(source, parameters)
    rendered_content_xml = t.render()
    print rendered_content_xml

def testImage():
    source = u'<xml><text:p>\
<draw:frame draw:name="flow_chart">\
<draw:image xlink:href="Pictures/asd.png" />\
</draw:frame>\
</text:p></xml>'''
    parameters = {
            u'flow_chart' :
                (
                    {'name' : 'svbsa101k2_0.png', 'url' : 'Pictures/svbsa101k2_0.png'},
                    {'name' : 'svbsa101k2_1.png', 'url' : 'Pictures/svbsa101k2_1.png'},
                    {'name' : 'svbsa101k2_2.png', 'url' : 'Pictures/svbsa101k2_2.png'},
                ),
            }
    t = Template(source, parameters)
    rendered_content_xml = t.render()
    print rendered_content_xml

def testImage_and_table():
    source = u'<xml>\
<text:p><draw:frame draw:name="flow_chart"><draw:image xlink:href="Pictures/asd.png" /></draw:frame></text:p>\
<table:table><table:table-row>\
<table:table-cell><text:p>{table1.id}</text:p></table:table-cell>\
<table:table-cell><text:p>{table1.name}</text:p></table:table-cell>\
<table:table-cell><text:p>{table1.description}</text:p></table:table-cell>\
</table:table-row></table:table>\
</xml>'''
    parameters = {
            u'flow_chart' :
                (
                    {'name' : 'svbsa101k2_0.png', 'url' : 'Pictures/svbsa101k2_0.png'},
                    {'name' : 'svbsa101k2_1.png', 'url' : 'Pictures/svbsa101k2_1.png'},
                    {'name' : 'svbsa101k2_2.png', 'url' : 'Pictures/svbsa101k2_2.png'},
                ),
            u'table1' :
                (
                    {'id' : '1', 'name' : 'SIAM.00479', 'description' : 'Test1'},
                    {'id' : '2', 'name' : 'SIAM.00172', 'description' : 'Test2'},
                ),
            }
    t = Template(source, parameters)
    rendered_content_xml = t.render()
    print rendered_content_xml

def testImage_in_table():
    source = u'<xml>\
<table:table><table:table-row>\
<table:table-cell><text:p>{table1.id}</text:p></table:table-cell>\
<table:table-cell><text:p>{table1.name}</text:p></table:table-cell>\
<table:table-cell>\
<draw:frame draw:name="flow_chart"><draw:image xlink:href="Pictures/asd.png" /></draw:frame>\
</table:table-cell>\
</table:table-row></table:table>\
</xml>'''
    parameters = {
            u'flow_chart' :
                (
                    {'name' : 'svbsa101k2_0.png', 'url' : 'Pictures/svbsa101k2_0.png'},
                    {'name' : 'svbsa101k2_1.png', 'url' : 'Pictures/svbsa101k2_1.png'},
                    {'name' : 'svbsa101k2_2.png', 'url' : 'Pictures/svbsa101k2_2.png'},
                ),
            u'table1' :
                (
                    {'id' : '1', 'name' : 'SIAM.00479', 'description' : 'Test1'},
                    {'id' : '2', 'name' : 'SIAM.00172', 'description' : 'Test2'},
                ),
            }
    t = Template(source, parameters)
    rendered_content_xml = t.render()
    print rendered_content_xml

def main():
    #return testTable_in_frame()
    return testImage_in_table()
    return testImage_and_table()
    return testImage()
    return testTable()

if __name__ == '__main__':
    main()
