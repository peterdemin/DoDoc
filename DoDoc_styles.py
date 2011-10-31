import xml.dom.minidom
import re

class Stylesheet(object):
    def __init__(self):
        self.style_def = xml.dom.minidom.Document()
        self.style_root = self.style_def.createElement('styles')
        self.style_def.appendChild(self.style_root)
        self.regulars = []

    def inject(self, document):
        root = document.firstChild() # office:document-content
        doc_styles = root.getElementsByTagName('office:automatic-styles')[0]
        for node in self.style_def.childNodes:
            doc_styles.appendChild(node)

    def addStyle(self, name, attributes):
        #self.styles[name] = replacement
        style_node = self.style_def.createElement('style:style')
        #print dir(style_node)
        style_name = 'DoDoc_%s' % (name)
        reg_exp = re.compile(ur'(?imu)\<%(name)s\>(.+?)\</%(name)s\>' % {'name' : name})
        self.regulars.append((reg_exp, style_name))
        style_node.setAttribute('style:name', style_name)
        style_node.setAttribute('style:family', 'text')
        descr_node = self.style_def.createElement('style:text-properties')
        for k,v in attributes.iteritems():
            descr_node.setAttribute(k, v)
        style_node.appendChild(descr_node)
        self.style_root.appendChild(style_node)

    def apply(self, source):
        result = source
        for repl in self.regulars:
            result = repl[0].sub(repl[1], result)
        return result

class Stylesheet_default(Stylesheet):
    def __init__(self):
        super(Stylesheet_default, self).__init__()
        self.addStyle('sub', {'style:text-position' : "sub 58%"})
        self.addStyle('super', {'style:text-position' : "super 58%"})
        self.addStyle('blue',  {'fo:color' : "#4747b8"})
        self.addStyle('red',   {'fo:color' : "#b84747"})
        self.addStyle('green', {'fo:color' : "#47b847"})

    def unpretty(self, xml):
        return u''.join(filter(len, [a.strip() for a in xml.splitlines()]))

def test():
    s = Stylesheet_default()
    print s.style_def.toprettyxml()

if __name__ == '__main__':
    test()
