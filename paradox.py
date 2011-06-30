import os
import codecs

CONVERTER_PATH = r'paradox2csv\paradox2csv.exe'

class Paradox_database(object):
    def __init__(self, table_path):
        self.csv_path = os.path.splitext(table_path)[0] + '.csv'
        cmd_line = '%s %s %s' % (CONVERTER_PATH, table_path, self.csv_path)
        print cmd_line
        os.system(cmd_line)
        self.__readCSV()

    def __readCSV(self):
        self.correction_by_siam = {}
        for line in codecs.open(self.csv_path, 'r', 'cp1251').readlines():
            parts = [a.strip() for a in line.split(u';')]
            if parts[3]:
                parts[3] = int(parts[3])
            else:
                parts[3] = 0
            self.correction_by_siam[parts[2].lower()] = parts[3]

    def getCorrections_amount(self, siam):
        if self.correction_by_siam.has_key(siam.lower()):
            return self.correction_by_siam[siam.lower()]
        else:
            return -1

    def close(self):
        os.unlink(self.csv_path)
