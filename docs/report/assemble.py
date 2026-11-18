"""Assemble the full project report from the section files in docs/report/.

    python docs/report/assemble.py          ->  docs/report/report.md

Each section is written and edited in its own file, so every member keeps
their own part. This script puts them in order, numbers the sections,
subsections and figures, adds a title page and a table of contents, and
prints a rough page estimate (the report must be 25-35 pages).

To change the order or a title, edit SECTIONS below. Sections 3 (Literature
Review), 4 (Novelty), 10 (Contribution) and 13 (References) are fixed by the
course; the others fill the numbers around them.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# (number, title, file). Number None = unnumbered front matter.
SECTIONS = [
    (None, "Abstract", "section_abstract.md"),
    (1, "Introduction", "section_introduction.md"),
    (2, "System Overview", "section_system_overview.md"),
    (3, "Literature Review", "section3_literature_review.md"),
    (4, "Novelty", "section4_novelty.md"),
    (5, "World and Sensors (M1)", "section_world_sensors.md"),
    (6, "Route Planner (M2)", "section_m2_route_planner.md"),
    (7, "Parking Manoeuvres (M3)", "section_m3_parking.md"),
    (8, "Control (M4)", "section_m4_control.md"),
    (9, "Results", "section_results.md"),
    (10, "Contribution", "section10_contribution.md"),
    (11, "Conclusion", "section_conclusion.md"),
    (12, "Limitations and Future Work", "section_limitations_future_work.md"),
    (13, "References", "section13_references.md"),
]

TITLE_PAGE = """# Autonomous Valet Parking Agent

**Project report**

CSAI4014 Algorithms for Intelligent Systems and Robotics (AISR)
B.Tech CSE (AI & ML), Semester VII

Project P13 · Group G08 · Batch B3

| Member | SAP ID | Module |
|---|---|---|
| Devansh Singh Rawat | 500124378 | M1 – World and Sensors |
| Bhavya Talwar | 500121992 | M2 – Route Planner, integration |
| Harshil Mittal | 500121907 | M3 – Parking Manoeuvres |
| Mohammad Shahvez | 500124132 | M4 – Control and Results |

Submitted to: [course instructor]
Date: [submission date]

Code: https://github.com/bhavyatalwar04/Autonomous-Valet-Parking-Agent
"""

NUMBERED = re.compile(r"^\d+(\.\d+)+\s")
IMAGE = re.compile(r"^!\[(.*)\]\((.+)\)\s*$")


def section_body(number, path):
    """The section's text with its own top heading removed and its
    subheadings and figures numbered. Returns (lines, toc entries, figures)."""
    with open(os.path.join(HERE, path), encoding="utf-8") as handle:
        lines = handle.read().split("\n")
    assert lines[0].startswith("# "), f"{path} must start with a '# ' heading"
    out, toc = [], []
    sub = subsub = 0
    in_code = False
    for line in lines[1:]:
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and number is not None and line.startswith("## "):
            sub += 1
            subsub = 0
            text = line[3:].strip()
            if not NUMBERED.match(text):
                text = f"{number}.{sub} {text}"
            toc.append(("  ", text))
            line = "## " + text
        elif not in_code and number is not None and line.startswith("### "):
            subsub += 1
            text = line[4:].strip()
            if not NUMBERED.match(text):
                text = f"{number}.{sub}.{subsub} {text}"
            line = "### " + text
        out.append(line)
    return out, toc


def assemble():
    parts, toc = [TITLE_PAGE], []
    figure = 0
    for number, title, path in SECTIONS:
        heading = title if number is None else f"{number}. {title}"
        toc.append(("", heading))
        body, sub_toc = section_body(number, path)
        toc.extend(sub_toc)
        numbered = []
        for line in body:
            m = IMAGE.match(line)
            if m:
                figure += 1
                caption, src = m.groups()
                numbered.append(f"![Figure {figure}: {caption}]({src})")
                numbered.append("")
                numbered.append(f"*Figure {figure}: {caption}*")
            else:
                numbered.append(line)
        parts.append(f"# {heading}\n" + "\n".join(numbered).rstrip() + "\n")
    contents = "# Contents\n\n" + "\n".join(
        f"{indent}- {text}" for indent, text in toc if not text.startswith("Abstract"))
    report = parts[0] + "\n---\n\n" + parts[1] + "\n---\n\n" + contents + "\n\n---\n\n" \
        + "\n\n".join(parts[2:])
    out = os.path.join(HERE, "report.md")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(report)
    return out, report, figure


def estimate_pages(report, figures, words_per_page):
    """Rough A4 page count for a given text density, plus space for tables,
    figures, code blocks and the front matter. About 550 words fit a page at
    11 pt single spacing, about 400 at 12 pt with 1.5 spacing."""
    text = re.sub(r"```.*?```", "", report, flags=re.S)
    words = len(re.findall(r"[A-Za-z0-9]+", text))
    table_rows = len([l for l in report.split("\n") if l.startswith("|")])
    code_lines = sum(block.count("\n") for block in re.findall(r"```.*?```", report, flags=re.S))
    pages = words / words_per_page + table_rows * 0.035 + figures * 0.4 + code_lines / 50 + 3
    return words, table_rows, pages


if __name__ == "__main__":
    out, report, figures = assemble()
    words, rows, dense = estimate_pages(report, figures, 550)
    _, _, loose = estimate_pages(report, figures, 400)
    print(f"wrote {os.path.relpath(out)}: {words} words, {rows} table rows, {figures} figures")
    print(f"estimated length: about {dense:.0f} pages at 11 pt single spacing, "
          f"{loose:.0f} at 12 pt 1.5 spacing (target 25-35)")
