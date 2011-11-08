#!/usr/bin/env python

from distutils.core import setup

#name The name of the package a string 
#version The version number of the package See distutils.version 
#description A single line describing the package a string 
#long_description Longer description of the package a string 
#author The name of the package author a string 
#author_email The email address of the package author a string 
#maintainer The name of the current maintainer, if different from the author a string 
#maintainer_email The email address of the current maintainer, if different from the author   
#url A URL for the package (homepage) a URL 
#download_url A URL to download the package a URL 
#packages A list of Python packages that distutils will manipulate a list of strings 
#py_modules A list of Python modules that distutils will manipulate a list of strings 
#scripts A list of standalone script files to be built and installed a list of strings 
#ext_modules A list of Python extensions to be built A list of instances of distutils.core.Extension 
#classifiers A list of categories for the package The list of available categorizations is at http://pypithon.org/pypi?:action=list_classifiers. 
#distclass the Distribution class to use A subclass of distutils.core.Distribution 
#script_name The name of the setup script - defaults to sys.argv[0] a string 
#script_args Arguments to supply to the setup script a list of strings 
#options default options for the setup script a string 
#license The license for the package   
#keywords Descriptive meta-data. See PEP 314   
#platforms     
#cmdclass A mapping of command names to Command subclasses a dictionary 

from DoDoc.DoDoc import VERSION

setup( name = 'DoDoc',
       version = VERSION,
       description = 'Template-based documentation generation tool',
       author = 'P. E. Demin',
       author_email = 'deminpe@otd263',
       py_modules = (r'DoDoc/__init__',
                     r'DoDoc/DoDoc',
                     r'DoDoc/DoDoc_parameters_parser',
                     r'DoDoc/import_uno',
                     r'DoDoc/odg2png',
                     r'DoDoc/odg2wmf',
                     r'DoDoc/odt2pdf',
                     r'DoDoc/OpenOffice_document',
                     r'DoDoc/Template',
                     r'DoDoc/DoDoc_styles',
                     r'DoDoc/DoXML',
                     r'DoDoc/DoDoc_folder_printer',
                     r'DoDoc/ods_parser'),
     )
