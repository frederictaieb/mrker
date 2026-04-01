from openpyxl import Workbook
from pathlib import Path
from pprint import pformat
from utils.file import delete_path

class XlsService:
    def __init__(self, markers=None, filenames=None):
        self.xls_file = "data/infos/markers.xlsx"
        self.txt_file = "data/infos/markers.txt"
        self.filenames = filenames
        self.markers = markers

    def same_len(self):
        return len(self.filenames) == len(self.markers)

    def min_len(self):
        return min(len(self.filenames), len(self.markers))

   
    def _generate_xls(self):
        wb = Workbook()
        ws = wb.active

        for i, (start, end) in enumerate(self.markers, start=1):
            ws.cell(row=i, column=1, value=start)
            ws.cell(row=i, column=2, value=end)

        for i, filename in enumerate(self.filenames, start=1):
            ws.cell(row=i, column=3, value=filename)

        wb.save(self.xls_file)

    def _generate_txt(self):
        with open(self.txt_file, "w", encoding="utf-8") as f:
            for i in range(self.min_len()):
                start, end = self.markers[i] 
                filename = self.filenames[i]
                f.write(f"{start}\t{end}\t{filename}\n")


    def generate(self):
        self._generate_xls()
        self._generate_txt()

    def is_generated(self):
        xls_file_path = Path(self.xls_file)
        txt_file_path = Path(self.txt_file)
        return xls_file_path.is_file() and txt_file_path.is_file()

    def reset(self):
        if self.is_generated():
            delete_path(self.xls_file)
            delete_path(self.txt_file)
            logger.info("Fichiers supprimés")
        else: 
            logger.info("Erreur")


    def __str__(self):
        return f"{self.xls_file}"

    def __repr__(self):
        return self.__str__()
