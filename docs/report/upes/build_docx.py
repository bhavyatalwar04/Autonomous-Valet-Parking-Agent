"""Build the submission report (Word) in the UPES sample-report format.

    python docs/report/assemble.py           # 1. section files -> docs/report/report.md
    python docs/report/upes/build_docx.py    # 2. report.md -> UPES structure -> .docx

Step 2 writes docs/report/upes/report_upes.md (the report in the template's
section order, see restructure.py) and docs/report/P13_Autonomous_Valet_Parking_report.docx.
Needs python-docx and Pillow (pip install python-docx pillow).

The template's own title page, declaration, front-matter pages, styles, page
border and section/page-number setup are kept; its sample text is replaced,
and its sample body is replaced by the report. When the file is first opened,
Word offers to update its fields: answer Yes to fill in the index, the lists
of figures and tables, and the figure/table numbers.
"""
import copy, re, sys
from pathlib import Path
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm, RGBColor, Emu
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from restructure import restructure, WRITING  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
TEMPLATE = HERE / "AISR_Sample_Project_Report.docx"
SOURCE = REPORT_DIR / "report.md"
MD = HERE / "report_upes.md"
BASE = REPORT_DIR                      # image paths in report.md are relative to docs/report/
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORT_DIR / "P13_Autonomous_Valet_Parking_report.docx"

MD.write_text(restructure(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
lines = MD.read_text(encoding="utf-8").splitlines()

TITLE = "Autonomous Valet Parking Agent"
MEMBERS = [("Devansh Singh Rawat", "500124378"), ("Bhavya Talwar", "500121992"),
           ("Harshil Mittal", "500121907"), ("Mohammad Shahvez", "500124132")]
# Writing Allocation table: keep in step with WRITING in restructure.py. Pages are
# measured from the built document (body section lengths, rounded).
ALLOCATION = [("M1", "Devansh Singh Rawat (500124378)", "1, 2, 5, 6, 7.1, 12.2–12.3, Appendix", "9"),
              ("M2", "Bhavya Talwar (500121992)", "Abstract, 7.2, 7.4", "10"),
              ("M3", "Harshil Mittal (500121907)", "3, 4, 7.3, 12.1", "9"),
              ("M4", "Mohammad Shahvez (500124132)", "8, 9, References", "10"),
              ("All", "Every member", "10 (own row and entry), 11 (own reflection), Declaration", "-")]
TABLE_CAPTIONS = [
    "Syllabus topics and where they are used in the project",
    "Layers and modules of the agent",
    "Data passed between the modules",
    "Sensors on the car and their use",
    "Inputs to the route planner",
    "Outputs of the route planner",
    "Events that trigger replanning, and the response",
    "States of the parking state machine",
    "Latest-main Webots run to bay A2",
    "Modes of the control module",
    "Limits on the target speed",
    "Planner comparison over six routes",
    "E1: controller comparison on the L-route",
    "E3: step response of the speed controller variants",
    "E3: effect of feed-forward in a full parking run",
    "E4: share of runs that parked, against GPS noise",
    "M3 parking in Webots, old and tuned settings",
    "Whole-agent scenarios (offline)",
    "Parking success in every bay, by row",
    "Normal run to A2: offline against Webots",
    "Summary of the results",
]
TEXT_W_CM = 21.0 - 3.0 - 2.5
MONO = "Courier New"

doc = Document(TEMPLATE)
P = doc.paragraphs
T = doc.tables

# ---------------------------------------------------------------- helpers
def set_runs(par, *texts):
    """Keep the paragraph's run formatting, replace the run texts in order."""
    runs = par.runs
    for r, t in zip(runs, texts):
        r.text = t
    for r in runs[len(texts):]:
        r._r.getparent().remove(r._r)

def add_field(par, instr, placeholder=""):
    def fld(kind):
        r = par.add_run(); e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), kind); r._r.append(e); return r
    fld("begin")
    r = par.add_run(); t = OxmlElement("w:instrText"); t.set(qn("xml:space"), "preserve"); t.text = f" {instr} "; r._r.append(t)
    fld("separate")
    run = par.add_run(placeholder)
    fld("end")
    return run

def add_hyperlink(par, url, text, bold=False):
    rel = par.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), rel)
    r = OxmlElement("w:r"); rpr = OxmlElement("w:rPr")
    if bold: rpr.append(OxmlElement("w:b"))
    c = OxmlElement("w:color"); c.set(qn("w:val"), "0563C1"); rpr.append(c)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rpr.append(u)
    r.append(rpr)
    t = OxmlElement("w:t"); t.text = text; t.set(qn("xml:space"), "preserve"); r.append(t)
    h.append(r); par._p.append(h)

ESC = "\x00"
TOKEN = re.compile(r"(`[^`]+`|\*\*.+?\*\*|(?<![\w*])\*(?!\s).+?(?<!\s)\*(?![\w*])|(?<!\w)_(?!\s)[^_]+?(?<!\s)_(?!\w)|\[[^\]]+\]\([^)]+\)|https?://[^\s)|]+)")

def setbi(r, bold, italic):
    if bold is not None: r.bold = bold
    if italic is not None: r.italic = italic

def inline(par, text, bold=None, italic=None, size=None):
    text = text.replace("\\*", ESC).replace("\\_", "_").replace("\\|", "|")
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            r = par.add_run(part[1:-1].replace(ESC, "*")); r.font.name = MONO
            r.font.size = Pt((size or 12) - 1.5); setbi(r, bold, italic)
        elif part.startswith("**") and part.endswith("**") and len(part) > 4:
            inline(par, part[2:-2].replace(ESC, "\\*"), True, italic, size)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            inline(par, part[1:-1].replace(ESC, "\\*"), bold, True, size)
        elif part.startswith("_") and part.endswith("_") and len(part) > 2:
            inline(par, part[1:-1].replace(ESC, "\\*"), bold, True, size)
        elif part.startswith("[") and "](" in part:
            label, url = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part).groups()
            if url.startswith("http"):
                add_hyperlink(par, url, label.replace(ESC, "*"), bold)
            else:
                r = par.add_run(label.replace(ESC, "*")); setbi(r, bold, italic)
                if size: r.font.size = Pt(size)
        elif part.startswith("http"):
            add_hyperlink(par, part, part, bold)
        else:
            r = par.add_run(part.replace(ESC, "*")); setbi(r, bold, italic)
            if size: r.font.size = Pt(size)

def set_cell_borders(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000"); borders.append(e)
    tblPr.append(borders)

def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcolor)
    tcPr.append(sh)

def split_row(row):
    row = row.strip().strip("|")
    cells, cur, i = [], "", 0
    while i < len(row):
        if row[i] == "\\" and i + 1 < len(row) and row[i + 1] == "|":
            cur += "\\|"; i += 2; continue
        if row[i] == "|":
            cells.append(cur.strip()); cur = ""
        else:
            cur += row[i]
        i += 1
    cells.append(cur.strip())
    return cells

def caption(kind, text, before_table=False):
    c = doc.add_paragraph(style="Caption")
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if before_table:
        c.paragraph_format.keep_with_next = True
    r = c.add_run(f"{kind} "); r.bold = True
    n = add_field(c, f"SEQ {kind} \\* ARABIC", "1"); n.bold = True
    r = c.add_run(": "); r.bold = True
    inline(c, text)
    for run in c.runs[5:]:
        if run.bold is None:
            run.bold = False
    return c

table_no = [0]
def add_table(rows):
    header = split_row(rows[0])
    is_appendix_or_contrib = header[0] in ("No.", "S. No.")
    if not is_appendix_or_contrib:
        caption("Table", TABLE_CAPTIONS[table_no[0]], before_table=True)
        table_no[0] += 1
    aligns = []
    for spec in split_row(rows[1]):
        aligns.append(WD_ALIGN_PARAGRAPH.RIGHT if spec.endswith(":") and not spec.startswith(":")
                      else WD_ALIGN_PARAGRAPH.CENTER if spec.startswith(":") and spec.endswith(":")
                      else WD_ALIGN_PARAGRAPH.LEFT)
    body = [split_row(r) for r in rows[2:]]
    ncol = len(header)
    t = doc.add_table(rows=1 + len(body), cols=ncol)
    set_cell_borders(t)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    lens = [max(len(re.sub(r"[*`_]", "", (r + [""] * ncol)[c])) for r in [header] + body) for c in range(ncol)]
    lens = [min(max(l, 5), 55) for l in lens]
    widths = [Cm(TEXT_W_CM * l / sum(lens)) for l in lens]
    for ri, cells in enumerate([header] + body):
        cells = (cells + [""] * ncol)[:ncol]
        for ci, txt in enumerate(cells):
            cell = t.cell(ri, ci); cell.width = widths[ci]
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(1); p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ri == 0 else (aligns[ci] if ci < len(aligns) else WD_ALIGN_PARAGRAPH.LEFT)
            inline(p, txt, bold=(ri == 0), size=10)
    trPr = t.rows[0]._tr.get_or_add_trPr()
    h = OxmlElement("w:tblHeader"); h.set(qn("w:val"), "true"); trPr.append(h)
    sp = doc.add_paragraph(); sp.paragraph_format.space_after = Pt(0); sp.paragraph_format.line_spacing = 1.0

def add_image(path, alt):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True; p.paragraph_format.line_spacing = 1.0
    with Image.open(path) as im:
        w, h = im.size
    width = Cm(14)
    if width * h / w > Cm(9.5):
        width = int(Cm(9.5) * w / h)
    p.add_run().add_picture(str(path), width=Emu(int(width)))
    p.runs[-1]._r.xpath(".//wp:docPr")[0].set("descr", alt)

def body_par(text, italic=False):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    inline(p, text, italic=italic)
    return p

def move_after(anchor_el, new_el):
    anchor_el.addnext(new_el)
    return new_el

def toc_paragraph(instr, placeholder):
    p = doc.add_paragraph()
    add_field(p, instr, placeholder)
    return p

# ---------------------------------------------------------------- template styles
st = doc.styles
h3 = st["Heading 3"]
h3.font.name, h3.font.size, h3.font.bold, h3.font.italic = "Times New Roman", Pt(12), True, True
h3.font.color.rgb = RGBColor(0, 0, 0)
rf = h3.element.rPr.rFonts
for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
    rf.attrib.pop(qn(f"w:{attr}"), None)
for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
    rf.set(qn(f"w:{attr}"), "Times New Roman")
h3.paragraph_format.space_before, h3.paragraph_format.space_after = Pt(6), Pt(3)
for name in ("Heading 1", "Heading 2", "Heading 3"):
    st[name].paragraph_format.keep_with_next = True

# ---------------------------------------------------------------- title page
set_runs(P[3], TITLE)
set_runs(P[7], "Project No.:", "\tP13")
set_runs(P[8], "Group No.:", "\tG08")
set_runs(P[9], "Batch:", "\tB3")
set_runs(P[15], "Academic Year 2026-2027   |   November 2026")

def fill_member_table(t, rowvals):
    for ri, vals in enumerate(rowvals, start=1):
        for ci, v in enumerate(vals):
            if v is None:
                continue
            cell_p = t.cell(ri, ci).paragraphs[0]
            set_runs(cell_p, v) if cell_p.runs else cell_p.add_run(v)
    for row in list(t.rows)[1 + len(rowvals):]:
        row._tr.getparent().remove(row._tr)

fill_member_table(T[0], [(str(i), n, s) for i, (n, s) in enumerate(MEMBERS, 1)])

# declaration
set_runs(P[18], P[18].runs[0].text.replace(
    "Obstacle-Avoiding Delivery Robot using Reactive Behaviours and PID Speed Control in Webots", TITLE))
fill_member_table(T[1], [(n, s, None) for n, s in MEMBERS])

# ---------------------------------------------------------------- abstract (from the markdown)
ab_start = lines.index("# Abstract") + 1
ab_end = next(i for i in range(ab_start, len(lines)) if lines[i].startswith("# "))
ab_pars = [l.strip() for l in lines[ab_start:ab_end] if l.strip() and l.strip() != "---"]
keywords = [l for l in ab_pars if l.startswith("**Keywords:**")][0]
ab_text = [l for l in ab_pars if not l.startswith("**Keywords:**")]
abstract_p, kw_p, note_p = P[23], P[24], P[25]
first_run = abstract_p.runs[0]
set_runs(abstract_p, "")
inline(abstract_p, ab_text[0])
anchor = abstract_p._p
for txt in ab_text[1:]:
    np_ = copy.deepcopy(abstract_p._p)
    for r in np_.findall(qn("w:r")):
        np_.remove(r)
    anchor.addnext(np_); anchor = np_
    from docx.text.paragraph import Paragraph
    inline(Paragraph(np_, abstract_p._parent), txt)
set_runs(kw_p, "Keywords:", " " + keywords.replace("**Keywords:**", "").strip())
# the placeholder line carries the page break to the Index; keep the break, drop the text
set_runs(note_p, "")
note_p.paragraph_format.space_after = Pt(0)
# set_runs may have removed the run holding the page break; make sure one exists
if 'w:type="page"' not in note_p._p.xml:
    note_p.add_run().add_break(WD_BREAK.PAGE)

# ---------------------------------------------------------------- index, lists of figures / tables
def outline_body(par):
    """Keep the look of Heading 1 but take the paragraph out of the index."""
    h = st["Heading 1"]
    par.style = st["Normal"]
    par.paragraph_format.space_before, par.paragraph_format.space_after = Pt(12), Pt(6)
    par.paragraph_format.line_spacing = 1.15
    for r in par.runs:
        r.bold = True; r.font.size = h.font.size; r.font.name = "Times New Roman"

index_h = P[26]
outline_body(index_h)
for p in P[27:46]:
    p._p.getparent().remove(p._p)
toc = toc_paragraph('TOC \\o "1-1" \\h \\z \\u', "Right-click and choose Update Field to build the index.")
move_after(index_h._p, toc._p)
pb = doc.add_paragraph(); pb.add_run().add_break(WD_BREAK.PAGE)
move_after(toc._p, pb._p)

lof_h, lot_h = P[46], P[48]
for p in (P[47], P[49], P[50]):
    p._p.getparent().remove(p._p)
lof = toc_paragraph('TOC \\h \\z \\c "Figure"', "Update field to list the figures.")
move_after(lof_h._p, lof._p)
lot = toc_paragraph('TOC \\h \\z \\c "Table"', "Update field to list the tables.")
move_after(lot_h._p, lot._p)
pb2 = doc.add_paragraph(); pb2.add_run().add_break(WD_BREAK.PAGE)
move_after(lot._p, pb2._p)

# writing allocation
wa = T[2]
for ri, (m, name, secs, pages) in enumerate(ALLOCATION, start=1):
    vals = (m, name, secs, pages)
    for ci, v in enumerate(vals):
        cp = wa.cell(ri, ci).paragraphs[0]
        if cp.runs:
            set_runs(cp, v)
        elif v:
            cp.add_run(v)
for row in list(wa.rows)[1 + len(ALLOCATION):]:
    row._tr.getparent().remove(row._tr)

# ---------------------------------------------------------------- remove the sample body
body = doc.element.body
front_end = P[53]._p          # paragraph carrying the front-matter section break
assert front_end.pPr is not None and front_end.pPr.sectPr is not None
el = front_end.getnext()
while el is not None and el.tag != qn("w:sectPr"):
    nxt = el.getnext(); body.remove(el); el = nxt

# ---------------------------------------------------------------- report body
i = lines.index("# 1. Introduction")
in_refs = False
while i < len(lines):
    ln = lines[i]; s = ln.strip()
    m = re.match(r"^(#{1,3}) (.*)$", ln)
    if m:
        level, text = len(m.group(1)), m.group(2).strip()
        if level == 1:
            mm = re.match(r"^(\d+)\. (.*)$", text)
            text = f"{mm.group(1)}.  {mm.group(2)}" if mm else text
            in_refs = text == "References"
        h = doc.add_heading(level=level); inline(h, text)
        i += 1; continue

    if s.startswith("```"):
        i += 1; code = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            code.append(lines[i]); i += 1
        i += 1
        p = doc.add_paragraph(); p.paragraph_format.line_spacing = 1.0; p.paragraph_format.keep_together = True
        pPr = p._p.get_or_add_pPr()
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), "F2F2F2"); pPr.append(sh)
        for k, cl in enumerate(code):
            r = p.add_run(cl); r.font.name = MONO; r.font.size = Pt(8.5)
            if k < len(code) - 1: r.add_break()
        continue

    m = re.match(r"^!\[(.*)\]\((.+)\)\s*$", s)
    if m:
        add_image((BASE / m.group(2)).resolve(), m.group(1))
        i += 1; continue

    if s.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            rows.append(lines[i]); i += 1
        add_table(rows); continue

    m = re.match(r"^(\s*)([-*]|\d+\.) (.*)$", ln)
    if m:
        indent = len(m.group(1)) // 2
        marker = m.group(2)
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        left = Cm(0.9 + 0.7 * indent)
        p.paragraph_format.left_indent = left; p.paragraph_format.first_line_indent = Cm(-0.6)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.tab_stops.add_tab_stop(left)
        p.add_run(("•" if marker in "-*" else marker) + "\t")
        text = m.group(3); i += 1
        while i < len(lines) and lines[i].startswith("  ") and lines[i].strip() and not re.match(r"^\s*([-*]|\d+\.) ", lines[i]):
            text += " " + lines[i].strip(); i += 1
        inline(p, text); continue

    if not s:
        i += 1; continue

    if in_refs and re.match(r"^\[\d+\] ", s):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.left_indent = Cm(1.0); p.paragraph_format.first_line_indent = Cm(-1.0)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(1.0))
        num, rest = s.split(" ", 1)
        p.add_run(num + "\t"); inline(p, rest)
        i += 1; continue

    # paragraph (soft-wrapped lines; a line ending in two spaces is a hard break)
    parts = [ln.rstrip("\n")]; i += 1
    while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||!\[|```|\s*([-*]|\d+\.) )", lines[i].strip()):
        parts.append(lines[i]); i += 1
    if len(parts) == 1:
        text = parts[0].strip()
        if text.startswith("*") and not text.startswith("**") and text.endswith("*") and not text.endswith("**"):
            inner = text[1:-1]
            if inner.startswith("Figure"):
                caption("Figure", re.sub(r"^Figure \d+:\s*", "", inner))
            else:
                body_par(inner, italic=True)
            continue
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT if any(x.endswith("  ") for x in parts[:-1]) else WD_ALIGN_PARAGRAPH.JUSTIFY
    for k, part in enumerate(parts):
        hard = part.endswith("  ")
        inline(p, part.strip() + ("" if hard or k == len(parts) - 1 else " "))
        if hard and k < len(parts) - 1:
            p.add_run().add_break()

assert table_no[0] == len(TABLE_CAPTIONS), (table_no[0], len(TABLE_CAPTIONS))
doc.core_properties.title = f"{TITLE}: project report"
doc.core_properties.author = "Group G08"
# ask Word to update the index, lists and caption numbers when the file is opened
settings = doc.settings.element
if settings.find(qn("w:updateFields")) is None:
    uf = OxmlElement("w:updateFields"); uf.set(qn("w:val"), "true"); settings.append(uf)
doc.save(OUT)
print("saved", OUT, "tables captioned:", table_no[0])
