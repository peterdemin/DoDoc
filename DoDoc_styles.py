from DoXML import DoXML
import Template
import xml.dom.minidom
import re

class Stylesheet(object):
    def __init__(self):
        self.style_def = xml.dom.minidom.Document()
        self.style_root = self.style_def.createElement('styles')
        self.style_def.appendChild(self.style_root)
        self.regulars = []
        self.doc = xml.dom.minidom.Document()
        self.node = None

    def inject(self, document):
        root = document.firstChild # office:document-content
        doc_styles = root.getElementsByTagName('office:automatic-styles')[0]
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
        if not self.node:
            self.node = self.doc.createElement(name)
            self.doc.appendChild(self.node)
        else:
            elem = self.doc.createElement(name)
            self.node = self.node.appendChild(elem)
        Template.setAttributes(self.doc, self.node, attrs)
        self.cur_text = []

    def endElement(self, name):
        if len(self.cur_text):
            content = u''.join(self.cur_text)
            content = self.replaceRAW(content)
            expanded = self.expand(content)
            asd = False
            if len(expanded) > 1:
                asd = True
                print '!', expanded
            for a in expanded:
                self.node.appendChild(a.cloneNode(True))
            if asd:
                print '!!', self.node.toxml()
                print '#', len(expanded), expanded
            self.cur_text = []
        self.node = self.node.parentNode

    def characters(self, content):
        self.cur_text.append(content)
        #text_node = self.doc.createTextNode(content)
        #self.node.appendChild(text_node)

    def replaceRAW(self, text):
        for r in self.regulars:
            text = r[0].sub(r[1], text)
        return text

    def expand(self, text):
        e = Expander(self)
        raw_xml = u'<tttt xmlns:style="a" xmlns:fo="b" xmlns:text="c">%s</tttt>' % (text)
        content_dom = xml.dom.minidom.parseString(raw_xml.encode('utf8'))
        Template.iterNode(content_dom, content_dom.firstChild, e)
        children = e.doc.firstChild.childNodes
        if len(children) > 1:
            for c in children:
                print 'RAC', c.nodeType, c.toxml()
        return children

class Expander(object):
    def __init__(self, stylesheet):
        self.stylesheet = stylesheet
        self.doc = xml.dom.minidom.Document()
        self.node = None

    def startElement(self, name, attrs):
        if not self.node:
            self.node = self.doc.createElement(name)
            self.doc.appendChild(self.node)
        else:
            elem = self.doc.createElement(name)
            self.node = self.node.appendChild(elem)
        Template.setAttributes(self.doc, self.node, attrs)

    def endElement(self, name):
        self.node = self.node.parentNode

    def characters(self, content):
        text_node = self.doc.createTextNode(content)
        self.node.appendChild(text_node)

class Stylesheet_default(Stylesheet):
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
        
def test():
    doc = DoXML()
    s = Stylesheet_default()
    raw_xml = '<test>Text of <red>Red color</red></test>'
    source = xml.dom.minidom.parseString(raw_xml)
    Template.iterNode(source, source.firstChild, s)
    print s.doc.toprettyxml()

if __name__ == '__main__':
    test()
