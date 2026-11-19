"""Rearrange the assembled report (docs/report/report.md) into the section
structure of the UPES sample report (AISR_Sample_Project_Report.docx).

Used by build_docx.py; can also be run on its own:

    python docs/report/upes/restructure.py      # writes docs/report/upes/report_upes.md

The section files in docs/report/ stay the source of the text. This step only
moves their sections under the template's headings. It changes no wording,
except that:
  - section cross-references are renumbered to the new structure;
  - the 'Organisation of the report' paragraph is rewritten for the new order;
  - the report-writing split agreed by the team (WRITING below) is applied to
    the Contribution table, the members' entries and the Results author note.
Template-only parts (the Section 7 lead-in, Co-learning Reflection, Appendix)
are added, with placeholders where each member must write their own text.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SRC = HERE.parent / "report.md"
DEFAULT_OUT = HERE / "report_upes.md"

MEMBERS = ("Devansh Singh Rawat", "Bhavya Talwar", "Harshil Mittal", "Mohammad Shahvez")

# Report-writing split agreed by the team ("Option C"), in the new section numbers.
WRITING = {
    "Devansh Singh Rawat": "1, 2, 5, 6, 7.1, 12.2–12.3, Appendix",
    "Bhavya Talwar": "Abstract, 7.2, 7.4; assembled the report",
    "Harshil Mittal": "3, 4, 7.3, 12.1",
    "Mohammad Shahvez": "8, 9, References",
}
REPORT_BULLET = {
    "Devansh Singh Rawat": "- **Report**: Sections 1 (Introduction), 2 (Problem Statement and Objectives), "
                           "5 (Syllabus Mapping and Theory), 6 (System Design), 7.1 (World and Sensors), "
                           "12.2 (Limitations) and 12.3 (Future work), and the Appendix.",
    "Harshil Mittal": "- **Report**: Sections 3 (Literature and Industry Review), 4 (Novelty), "
                      "7.3 (Parking Manoeuvres) and 12.1 (Conclusion).",
    "Mohammad Shahvez": "- **Report**: Sections 8 (Simulation Setup) and 9 (Results and Analysis), and the References.",
}
BHAVYA_REPORT = "the Abstract and Sections 7.2 (Route Planner) and 7.4 (Control)"
RESULTS_AUTHOR = "Mohammad Shahvez"

ORGANISATION = (
    "Section 2 states the problem, the objectives and the assumptions. Section 3 reviews the literature "
    "the agent builds on, and Section 4 presents what is new, with the measurements for each point. "
    "Section 5 maps the syllabus topics onto the project. Section 6 gives the system design: how the four "
    "modules form one agent. Section 7 describes the methods and algorithms of each module: World and "
    "Sensors (7.1), Route Planner (7.2), Parking Manoeuvres (7.3) and Control (7.4). Section 8 gives the "
    "simulation setup, and Section 9 the experiments and comparisons. Section 10 states who did what, and "
    "Section 11 gives each member's co-learning reflection. Section 12 concludes, with the limitations and "
    "future work. The references and an appendix of links and logs follow.")
METHODS_LEAD = ("This section describes the methods and algorithms of the four modules, in the order the data "
                "flows through the agent: sensing (7.1), route planning (7.2), the parking manoeuvre (7.3) "
                "and control (7.4).")


def new_num(old):
    """Old section number (assemble.py order) -> number in the UPES structure."""
    p = old.split(".")
    top, rest = p[0], p[1:]
    if top == "1" and rest:
        return {"1": "1.1", "2": "2.1", "3": "2.2", "4": "5", "5": "2.3", "6": "1.2"}[rest[0]]
    if top == "2":
        return ".".join(["6"] + rest)
    if top in ("5", "6", "7", "8"):
        return ".".join(["7", str(int(top) - 4)] + rest)
    if top == "9" and rest:
        if rest[0] == "1":
            return "8"
        return ".".join(["9", str(int(rest[0]) - 1)] + rest[1:])
    if top == "11":
        return "12.1"
    if top == "12":
        return ".".join(["12"] + ([str(int(rest[0]) + 1)] if rest else []))
    return old


def remap(text):
    """Renumber 'Section N' cross-references in a line of the old report."""
    text = text.replace("Sections 5 to 8", "Sections 7.1 to 7.4")
    text = re.sub(r"\bSection (\d+(?:\.\d+)*)",
                  lambda m: "the References" if m.group(1) == "13" else f"Section {new_num(m.group(1))}", text)
    return re.sub(r"\bSections (\d+(?:\.\d+)*) and (\d+(?:\.\d+)*)",
                  lambda m: f"Sections {new_num(m.group(1))} and {new_num(m.group(2))}", text)


def parse(lines):
    """Split the assembled report into top-level sections and their subsections."""
    body = lines[lines.index("---") + 1:]          # skip the title page
    h1, cur, sub = {}, None, None
    for ln in body:
        m1 = re.match(r"^# (?:(\d+)\. )?(.*)$", ln)
        m2 = re.match(r"^## (\d+(?:\.\d+)*) (.*)$", ln)
        if m1:
            cur = {"title": m1.group(2), "intro": [], "subs": []}
            h1[m1.group(1) or m1.group(2)] = cur
            sub = None
        elif m2 and cur is not None:
            sub = (m2.group(1), m2.group(2), [])
            cur["subs"].append(sub)
        elif cur is not None:
            (sub[2] if sub else cur["intro"]).append(ln)
    return h1


def restructure(source_text):
    h1 = parse(source_text.splitlines())
    subs = lambda key: {num: (title, ls) for num, title, ls in h1[key]["subs"]}
    o = []
    H1 = lambda t: o.extend(["", f"# {t}", ""])
    H2 = lambda t: o.extend(["", f"## {t}", ""])
    add = lambda ls: o.extend(remap(l) for l in ls)

    H1("Abstract"); add(h1["Abstract"]["intro"])

    s1 = subs("1")
    H1("1. Introduction"); add(h1["1"]["intro"])
    H2("1.1 " + s1["1.1"][0]); add(s1["1.1"][1])
    H2("1.2 " + s1["1.6"][0]); o.append(ORGANISATION)

    H1("2. Problem Statement and Objectives")
    H2("2.1 " + s1["1.2"][0]); add(s1["1.2"][1])
    H2("2.2 " + s1["1.3"][0]); add(s1["1.3"][1])
    H2("2.3 " + s1["1.5"][0]); add(s1["1.5"][1])

    H1("3. Literature and Industry Review"); add(h1["3"]["intro"])
    for num, t, ls in h1["3"]["subs"]:
        H2(f"{num} {t}"); add(ls)
    H1("4. Novelty"); add(h1["4"]["intro"])
    for num, t, ls in h1["4"]["subs"]:
        H2(f"{num} {t}"); add(ls)

    H1("5. Syllabus Mapping and Theory"); add(s1["1.4"][1])

    H1("6. System Design"); add(h1["2"]["intro"])
    for num, t, ls in h1["2"]["subs"]:
        H2(f"{new_num(num)} {t}"); add(ls)

    H1("7. Methodology and Algorithms"); o.append(METHODS_LEAD)
    for old in ("5", "6", "7", "8"):
        title = re.sub(r"^(\d+\. )", "", h1[old]["title"])
        H2(f"{new_num(old)} {title}"); add(h1[old]["intro"])
        for num, t, ls in h1[old]["subs"]:
            o.extend(["", f"### {new_num(num)} {t}", ""]); add(ls)

    H1("8. Simulation Setup"); add(subs("9")["9.1"][1])

    H1("9. Results and Analysis")
    add(l.replace("**Section written by:** Bhavya Talwar", f"**Section written by:** {RESULTS_AUTHOR}")
        for l in h1["9"]["intro"])
    for num, t, ls in h1["9"]["subs"]:
        if num == "9.1":
            continue
        H2(f"{new_num(num)} {t}")
        for l in ls:
            m = re.match(r"^### (\d+(?:\.\d+)*) (.*)$", l)
            o.append(f"### {new_num(m.group(1))} {m.group(2)}" if m else remap(l))

    H1("10. Contribution")
    sno = 0
    for l in h1["10"]["intro"]:
        if l.startswith("| Member |"):
            l = "| S. No. | Name and SAP ID | Module | Report sections | Signature |"
        elif l.startswith("|---"):
            l = "|---|---|---|---|---|"
        elif l.startswith("|"):
            _, name, sap, module, secs, _ = [c.strip() for c in l.split("|")]
            sno += 1
            l = f"| {sno} | {name} ({sap}) | {module} | {WRITING.get(name, secs)} |  |"
        o.append(l)
    for num, t, ls in h1["10"]["subs"]:
        H2(f"{num} {t}")
        member = next(n for n in MEMBERS if t.startswith(n))
        for l in ls:
            if l.startswith("- **Report**:"):
                l = re.sub(r"the Abstract and Sections 1 \(Introduction\).*?13 \(References\)", BHAVYA_REPORT, l)
                o.append(l)
            else:
                o.append(remap(l))
        if member in REPORT_BULLET:
            while o and not o[-1].strip():
                o.pop()
            o.extend(["", REPORT_BULLET[member], ""])

    H1("11. Co-learning Reflection")
    o.append("Each member describes what they learned on their own, what they learned from team-mates, "
             "and what they taught others.")
    for name in MEMBERS:
        short = "Shahvez" if name.startswith("Mohammad") else name.split()[0]
        o.extend(["", f"**{name}:** *[To be written by {short}: 5–8 lines.]*"])

    H1("12. Conclusion and Future Scope")
    H2("12.1 Conclusion"); add(h1["11"]["intro"])
    add(h1["12"]["intro"])
    for num, t, ls in h1["12"]["subs"]:
        H2(f"{new_num(num)} {t}"); add(ls)

    H1("References"); add(h1["13"]["intro"])

    H1("Appendix: Links and Logs")
    o.extend(["**GitHub repository:** https://github.com/bhavyatalwar04/Autonomous-Valet-Parking-Agent", "",
              "**YouTube video (Unlisted):** *[link to be added after upload]*", "",
              "**Meeting log**", "",
              "| No. | Date | Duration | Attendees | Decisions |", "|---|---|---|---|---|",
              "| 1 |  |  |  |  |", "| 2 |  |  |  |  |", "| 3 |  |  |  |  |", "",
              "**Peer-assessment sheets:** attach one sheet per member (format in the Project Instructions, Section 4)."])

    text = "\n".join(o).strip() + "\n"
    return re.sub(r"\n{3,}", "\n\n", text)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    out.write_text(restructure(src.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"wrote {out}")
