# -*- coding: utf8 -*-
# Импорт необходимых библиотек
import codecs
from DoDoc.DoXML import DoXML
from DoDoc import DoDoc

# Создание объекта компоновщика XML файла
doc = DoXML()
# Добавление таблицы 'contacts'
doc.table('contacts')
for line in codecs.open('contacts.txt', 'r', 'utf8').readlines():
    # Для каждой строки входного файла
    # Разобрать строку на части:
    mail, name = line.strip().split(u' ', 1)
    # Создать ряд таблицы:
    doc.row()
    # Добавить в ряд таблицы текстовые значения:
    doc.text(u'name', name)
    doc.text(u'mail', mail)
# Сохранить XML в файл 'contacts.xml'
doc.save('contacts.xml')
# Вызвать DoDoc, передав имена файлов шаблона, входного XML и выходного файла
DoDoc.DoDoc('contacts_template.odt', 'contacts.xml', 'my_contacts.odt')
