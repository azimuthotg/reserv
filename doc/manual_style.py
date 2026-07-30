"""สไตล์กลางสำหรับคู่มือชุด 2569 — ตัวหนังสือดำล้วน หัวตารางจัดกลางพื้นเทาอ่อน
ไม่ใช้ bullet และไม่มีกล่องคำแนะนำ/คำเตือน ตามรูปแบบที่ผู้ใช้กำหนด
"""
import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT       = "TH Sarabun New"
BLACK      = RGBColor(0x00, 0x00, 0x00)
HEADER_BG  = "EDEDED"   # เทาอ่อนสำหรับหัวตาราง
BORDER_CLR = "BFBFBF"

BODY_PT    = 16
CONTENT_CM = 16.0       # ความกว้างพื้นที่พิมพ์ = 21 - (3 + 2)


def _thai_run(element, size_pt, bold=False, italic=False):
    """ตั้งค่าฝั่ง Complex Script ให้ run หนึ่งตัว

    Word จัดข้อความไทยเป็น complex script จึงอ่านฟอนต์จาก w:cs และขนาดจาก w:szCs
    ไม่ใช่ w:ascii/w:sz ที่ python-docx ตั้งให้ ถ้าไม่ตั้งสองค่านี้ ข้อความไทยจะกลาย
    เป็นฟอนต์และขนาดเริ่มต้นของ Word ทั้งเอกสาร
    """
    rPr = element.get_or_add_rPr()

    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:cs"), FONT)
    rFonts.set(qn("w:eastAsia"), FONT)

    szCs = rPr.find(qn("w:szCs"))
    if szCs is None:
        szCs = OxmlElement("w:szCs")
        rPr.append(szCs)
    szCs.set(qn("w:val"), str(int(size_pt * 2)))

    if bold:
        b = OxmlElement("w:bCs")
        b.set(qn("w:val"), "1")
        rPr.append(b)
    if italic:
        i = OxmlElement("w:iCs")
        i.set(qn("w:val"), "1")
        rPr.append(i)


class Manual:
    def __init__(self, shots_dir):
        self.shots = shots_dir
        self.doc   = Document()
        self._setup()

    # ── ตั้งค่าเอกสาร ─────────────────────────────────────────────────────────
    def _setup(self):
        sec = self.doc.sections[0]
        sec.page_width  = Cm(21)
        sec.page_height = Cm(29.7)
        sec.top_margin    = Cm(2.5)
        sec.bottom_margin = Cm(2.0)
        sec.left_margin   = Cm(3.0)
        sec.right_margin  = Cm(2.0)

        normal = self.doc.styles["Normal"]
        normal.font.name = FONT
        normal.font.size = Pt(BODY_PT)
        normal.font.color.rgb = BLACK
        _thai_run(normal.element, BODY_PT)
        normal.paragraph_format.line_spacing = 1.15

        for level, size in ((1, 22), (2, 19), (3, 17)):
            s = self.doc.styles[f"Heading {level}"]
            s.font.name = FONT
            s.font.size = Pt(size)
            s.font.bold = True
            s.font.color.rgb = BLACK
            _thai_run(s.element, size, bold=True)

    # ── ชิ้นส่วนพื้นฐาน ───────────────────────────────────────────────────────
    def run(self, p, text, bold=False, size=BODY_PT, italic=False):
        r = p.add_run(text)
        r.font.name  = FONT
        r.font.size  = Pt(size)
        r.font.bold  = bold
        r.font.italic = italic
        r.font.color.rgb = BLACK
        _thai_run(r.element, size, bold, italic)
        return r

    def para(self, text="", bold=False, size=BODY_PT, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             before=0, after=6, indent=0.0, italic=False):
        p = self.doc.add_paragraph()
        p.alignment = align
        pf = p.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after  = Pt(after)
        if indent:
            pf.left_indent = Cm(indent)
        if text:
            self.run(p, text, bold=bold, size=size, italic=italic)
        return p

    def heading(self, text, level=1, page_break_before=False):
        if page_break_before:
            self.doc.add_page_break()
        h = self.doc.add_heading(text, level=level)
        h.paragraph_format.space_before = Pt(16 if level == 1 else 12)
        h.paragraph_format.space_after  = Pt(8)
        size = {1: 22, 2: 19, 3: 17}.get(level, 17)
        for r in h.runs:
            r.font.name = FONT
            r.font.color.rgb = BLACK
            _thai_run(r.element, size, bold=True)
        return h

    def steps(self, items, indent=0.6):
        """ขั้นตอนแบบเลขลำดับ เริ่มที่ 1 เสมอ (ไม่ใช้ List Number ของ Word
        เพราะตัวนับใช้ร่วมกันทั้งเอกสาร)"""
        for i, text in enumerate(items, start=1):
            p = self.doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent      = Cm(indent + 0.8)
            pf.first_line_indent = Cm(-0.8)
            pf.space_after      = Pt(4)
            self.run(p, f"{i}.", bold=True)
            self.run(p, "\t" + text)

    # ── ตาราง ────────────────────────────────────────────────────────────────
    def table(self, headers, rows, widths=None, center_cols=()):
        t = self.doc.add_table(rows=1 + len(rows), cols=len(headers))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        self._borders(t)

        for i, h in enumerate(headers):
            cell = t.rows[0].cells[i]
            self._shade(cell, HEADER_BG)
            cp = cell.paragraphs[0]
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp.paragraph_format.space_before = Pt(3)
            cp.paragraph_format.space_after  = Pt(3)
            self.run(cp, h, bold=True, size=15)

        for ri, row_data in enumerate(rows):
            for ci, val in enumerate(row_data):
                cell = t.rows[ri + 1].cells[ci]
                cp = cell.paragraphs[0]
                cp.alignment = (WD_ALIGN_PARAGRAPH.CENTER if ci in center_cols
                                else WD_ALIGN_PARAGRAPH.LEFT)
                cp.paragraph_format.space_before = Pt(2)
                cp.paragraph_format.space_after  = Pt(2)
                self.run(cp, str(val), size=15)

        if widths:
            for ci, w in enumerate(widths):
                for row in t.rows:
                    row.cells[ci].width = Cm(w)

        self.para(after=4)
        return t

    def _shade(self, cell, fill):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), fill)
        tcPr.append(shd)

    def _borders(self, table):
        tbl = table._tbl
        tblPr = tbl.tblPr
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "6")
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), BORDER_CLR)
            borders.append(el)
        tblPr.append(borders)

    # ── ภาพประกอบ 16:9 พร้อมคำบรรยาย ─────────────────────────────────────────
    def figure(self, filename, caption, width_cm=CONTENT_CM):
        path = filename if os.path.isabs(filename) else os.path.join(self.shots, filename)
        if not path.endswith(".png"):
            path += ".png"
        if not os.path.exists(path):
            print(f"  ! ไม่พบภาพ {path} — ข้าม")
            return False

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after  = Pt(2)
        p.add_run().add_picture(path, width=Cm(width_cm))

        self.figure_no = getattr(self, "figure_no", 0) + 1
        cp = self.doc.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_after = Pt(12)
        self.run(cp, f"ภาพที่ {self.figure_no}  {caption}", size=14)
        return True

    # ── ปก / สารบัญ ───────────────────────────────────────────────────────────
    def cover(self, title, subtitle, kind, org, version):
        self.para(before=90, after=0)
        self.para(title, bold=True, size=34, align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
        self.para(subtitle, bold=True, size=22, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
        self.para(kind, size=18, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
        self.para(before=110, after=0)
        self.para(org, size=18, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
        self.para(version, size=16, align=WD_ALIGN_PARAGRAPH.CENTER)
        self.doc.add_page_break()

    def toc(self, entries):
        self.para("สารบัญ", bold=True, size=22, align=WD_ALIGN_PARAGRAPH.CENTER, after=14)
        for label, title in entries:
            p = self.doc.add_paragraph()
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.left_indent = Cm(0.8 if label.count(".") else 0)
            self.run(p, f"{label}  {title}", bold=not label.count("."))
        self.doc.add_page_break()

    # ── หมายเลขหน้า ──────────────────────────────────────────────────────────
    def page_numbers(self):
        footer = self.doc.sections[0].footer
        p = footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run()
        r.font.name = FONT
        r.font.size = Pt(14)
        r.font.color.rgb = BLACK
        _thai_run(r._r, 14)
        for tag, attrs, text in (
            ("w:fldChar", {"w:fldCharType": "begin"}, None),
            ("w:instrText", {"xml:space": "preserve"}, " PAGE "),
            ("w:fldChar", {"w:fldCharType": "end"}, None),
        ):
            el = OxmlElement(tag)
            for k, v in attrs.items():
                el.set(qn(k), v)
            if text:
                el.text = text
            r._r.append(el)

    def save(self, path):
        self.page_numbers()
        self.doc.save(path)
        print("บันทึกแล้ว:", path)
