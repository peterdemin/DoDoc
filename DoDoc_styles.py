import re
import xml.dom.minidom
from xml.parsers.expat import ExpatError
import Template

class Stylesheet(object):
    def __init__(self):
        self.style_def = xml.dom.minidom.Document()
        self.style_root = self.style_def.createElement('styles')
        self.style_def.appendChild(self.style_root)
        self.regulars = []
        self.doc = xml.dom.minidom.Document()
        self.node = None
        self.cur_text = []

    def inject(self, document):
        root = document.firstChild # office:document-content
        elements = root.getElementsByTagName('office:automatic-styles')
        if len(elements) == 1:
            doc_styles = elements[0]
            for node in self.style_root.childNodes:
                doc_styles.appendChild(node.cloneNode(True))

    def addStyle(self, name, attributes):
        #self.styles[name] = replacement
        style_node = self.style_def.createElement('style:style')
        #print dir(style_node)
        style_name = 'DoDoc_%s' % (name)
        expr = ur'(?imu)\<%(name)s\>(.+?)\</%(name)s\>' % {'name' : name}
        repl = ur'<text:span text:style-name="%(name)s">\1</text:span>' % {'name' : style_name}
        reg_exp = re.compile(expr)
        self.regulars.append((re.compile(expr), repl))
        style_node.setAttribute('style:name', style_name)
        style_node.setAttribute('style:family', 'text')
        descr_node = self.style_def.createElement('style:text-properties')
        for k,v in attributes.iteritems():
            descr_node.setAttribute(k, v)
        style_node.appendChild(descr_node)
        self.style_root.appendChild(style_node)

    def startElement(self, name, attrs):
        self.putCurrent_text()
        if not self.node:
            self.node = self.doc.createElement(name)
            self.doc.appendChild(self.node)
        else:
            elem = self.doc.createElement(name)
            self.node = self.node.appendChild(elem)
        Template.setAttributes(self.doc, self.node, attrs)
        self.cur_text = []

    def endElement(self, name):
        self.putCurrent_text()
        self.node = self.node.parentNode

    def characters(self, content):
        self.cur_text.append(content)
        #text_node = self.doc.createTextNode(content)
        #self.node.appendChild(text_node)

    def putCurrent_text(self):
        if len(self.cur_text):
            content = u''.join(self.cur_text)
            content = self.replaceRAW(content)
            expanded = self.expand(content)
            for a in expanded:
                self.node.appendChild(a.cloneNode(True))
            self.cur_text = []

    def replaceRAW(self, text):
        for r in self.regulars:
            text = r[0].sub(r[1], text)
        return text

    def expand(self, text, doc_ = None):
        if doc_:
            doc = doc_
        else:
            doc = self.doc
        try:
            raw_xml = u'<tttt xmlns:style="a" xmlns:fo="b" xmlns:text="c">%s</tttt>' % (text)
            content_dom = xml.dom.minidom.parseString(raw_xml.encode('utf8'))
            children = content_dom.firstChild.cloneNode(True).childNodes
        except xml.parsers.expat.ExpatError, e:
            #print 'FAILED EXPAND:', text
            children = [doc.createTextNode(text).cloneNode(True)]
        return children

    def apply(self, doc, text):
        if len(text.strip()):
            return self.expand(self.replaceRAW(text), doc)
        else:
            return [doc.createTextNode(text).cloneNode(True)]

class Stylesheet_default(Stylesheet):
    __instance = None

    def __init__(self):
        super(Stylesheet_default, self).__init__()
        self.addStyle('sub', {'style:text-position' : "sub 58%"})
        self.addStyle('super', {'style:text-position' : "super 58%"})
        self.addStyle('blue',  {'fo:color' : "#4747b8"})
        self.addStyle('red',   {'fo:color' : "#b84747"})
        self.addStyle('green', {'fo:color' : "#47b847"})
        self.addStyle('b', {'fo:font-weight' : "bold", 'style:font-weight-complex' : 'bold'})
        self.addStyle('i', {'fo:font-style' : "italic", 'style:font-style-complex' : 'italic'})
        self.addStyle('u', {'fo:text-underline-width' : "auto", 'style:text-underline-style' : 'solid', 'style:text-underline-color' : 'font-color'})

    @staticmethod
    def instance():
        Stylesheet_default.__instance = Stylesheet_default()
        Stylesheet_default.instance = Stylesheet_default.__instance.__return_initialized
        return Stylesheet_default.__instance

    def __return_initialized(self):
        return self.__instance

def test():
    from DoXML import DoXML
    doc = DoXML()
    s = Stylesheet_default()
    doc.table('a')
    doc.row()
    doc.text('test', u'Text of <red>Red</red> color')
    #raw_xml = '<test></test>'
    source = xml.dom.minidom.parseString(doc.doc.toxml().encode('utf8'))
    Template.iterNode(source, source.firstChild, s)
    print s.doc.toprettyxml()

if __name__ == '__main__':
    test()
