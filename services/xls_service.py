from openpyxl import Workbook
from pprint import pformat

class XlsService:
    def __init__(self, xls_file="data/infos/markers.xlsx", txt_file="data/infos/markers.txt", markers=None, filenames=None):
        self.xls_file = xls_file
        self.txt_file = txt_file
        self.filenames = filenames
        self.markers = markers
        pass

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

    @classmethod 
    def create(cls, xls_file, txt_file, markers, filenames):
        obj = cls(xls_file, txt_file, markers, filenames)
        obj._generate_xls()
        obj._generate_txt()
        return obj

    def __str__(self):
        return f"{self.xls_file}"
        pass

    def __repr__(self):
        return self.__str__()
