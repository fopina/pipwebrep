import xlwt
from xlwt import XFStyle,Formula,Font,Alignment
from datetime import date

def output(file_or_stream, sheetname, headers, values, encoding = 'utf8', footer_text = None, footer_link = None):
	import xlwt

	book = xlwt.Workbook(encoding)
	sh = book.add_sheet(sheetname)

	datestyle = XFStyle()
	datestyle.num_format_str = 'DD/MM/YYYY'

	header_font = Font()
	header_font.bold = True

	header_style = XFStyle()
	header_style.font = header_font

	for i,header in enumerate(headers):
		sh.write(0, i, header, header_style)

	for j, row in enumerate(values):
		for i, value in enumerate(row):
			if value.__class__ == date:
				sh.write(j+1, i, value, datestyle)
			else:
				sh.write(j+1, i, value)

	if footer_link and footer_text:
		link_font = Font()
		link_font.name = 'Verdana'
		link_font.underline = Font.UNDERLINE_DOUBLE
		link_font.colour_index = 4
		link_font.height = 20*8

		al = Alignment()
		al.horz = Alignment.HORZ_CENTER
		al.vert = Alignment.VERT_BOTTOM

		link_style = XFStyle()
		link_style.font = link_font
		link_style.alignment = al
		row = len(values) + 1
		sh.write_merge(row, row, 0, len(headers)-1, Formula('HYPERLINK("' + footer_link + '";"' + footer_text + '")'), link_style)

	book.save(file_or_stream)



