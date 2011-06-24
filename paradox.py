#from adodbapi import adodbapi
#adodbapi.connect('Provider=Microsoft.Jet.OLEDB.4.0;Data Source=Database;Extended Properties=Paradox 5.x')

import pyodbc
#pyodbc.connect('Driver={Microsoft Paradox Driver (*.db )};DriverID=538;Fil=Paradox 5.X;DefaultDir=Database\;Dbq=Database\;CollatingSequence=ASCII')
pyodbc.connect(r'Driver={Microsoft Paradox Driver (*.db )};Fil=Paradox 5.X')
