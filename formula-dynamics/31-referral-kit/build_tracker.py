#!/usr/bin/env python3
"""Referral tracker workbook: one row per referred customer, commission worked out for you.

    uv run --no-project --with openpyxl python build_tracker.py

Opens in Numbers, Excel or Google Sheets. The two commission rates and the payout terms sit on
the SETTINGS tab as yellow-flagged placeholders until Nate sets them; every row reads them from
there, so changing one cell re-prices the whole sheet.
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

OUT = Path(__file__).resolve().parent / "renders" / "FD-referral-tracker.xlsx"
CODE = "OMARIE"  # keep in step with build_referral_kit.py
ROWS = 200

RED, INK, WHITE, GREY = "FE0F13", "08080A", "FFFFFF", "9A9AA2"
HEAD = Font(name="Arial", bold=True, color=WHITE)
HEAD_FILL = PatternFill("solid", fgColor=INK)
RED_FILL = PatternFill("solid", fgColor=RED)
PLACE_FILL = PatternFill("solid", fgColor="FFF2B3")
thin = Side(style="thin", color="D0D0D6")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()

# ---- SETTINGS -------------------------------------------------------------------------------
st = wb.active
st.title = "SETTINGS"
st.column_dimensions["A"].width = 38
st.column_dimensions["B"].width = 18
st.column_dimensions["C"].width = 60
st["A1"] = "FORMULA DYNAMICS  ·  REFERRAL SETTINGS"
st["A1"].font = Font(name="Arial", bold=True, size=14, color=WHITE)
st["A1"].fill = HEAD_FILL
st.merge_cells("A1:C1")
rows = [
    ("Referral code", CODE, "PLACEHOLDER until Nate confirms the code name."),
    ("Commission on SERVICE (%)", None, "PLACEHOLDER. Blank until Nate sets it; commission shows blank till then."),
    ("Commission on PARTS (%)", None, "PLACEHOLDER. Blank until Nate sets it; commission shows blank till then."),
    ("Commission counts on", "Paid invoice, before tax", "PLACEHOLDER. Confirm with Nate (before or after tax, parts at cost or retail)."),
    ("Offer for the referred customer", "None yet", "PLACEHOLDER. Nate decides if there is one."),
    ("How the shop records the code", "Code written on the invoice / work order", "PLACEHOLDER. Confirm Nate's checkout process."),
    ("Payout timing", "Monthly", "PLACEHOLDER. Confirm with Nate."),
]
for i, (a, b, c) in enumerate(rows, start=3):
    st.cell(i, 1, a).font = Font(name="Arial", bold=True)
    cell = st.cell(i, 2, b)
    cell.fill = PLACE_FILL
    cell.border = BOX
    if i in (4, 5):
        cell.number_format = "0.0%"
    st.cell(i, 3, c).font = Font(name="Arial", italic=True, color="7A7A82")
st["A11"] = "Yellow cells are placeholders. Change them here; the LOG tab updates itself."
st["A11"].font = Font(name="Arial", italic=True)
st["A12"] = ("How a row works: put the customer, pick Service or Parts, type the invoice total. "
             "The rate and the commission owed fill in. Pick Yes under 'Paid to Omarie?' once paid.")
st["A12"].font = Font(name="Arial", italic=True)

SERVICE_RATE = "SETTINGS!$B$4"
PARTS_RATE = "SETTINGS!$B$5"

# ---- LOG ------------------------------------------------------------------------------------
lg = wb.create_sheet("LOG")
cols = [
    ("Date in", 12, "mm/dd/yyyy"),
    ("Customer (first name + last initial)", 26, None),
    ("Car", 22, None),
    ("Work done (e.g. brake service)", 24, None),
    ("Service or Parts", 14, None),
    ("How they came in", 18, None),
    ("Invoice #", 12, None),
    ("Invoice total ($)", 15, '"$"#,##0.00'),
    ("Commission rate", 14, "0.0%"),
    ("Commission owed ($)", 18, '"$"#,##0.00'),
    ("Paid to Omarie?", 14, None),
    ("Date paid", 12, "mm/dd/yyyy"),
    ("Notes", 34, None),
]
for c, (name, width, _) in enumerate(cols, start=1):
    cell = lg.cell(1, c, name)
    cell.font = HEAD
    cell.fill = RED_FILL if name in ("Commission owed ($)",) else HEAD_FILL
    cell.alignment = Alignment(wrap_text=True, vertical="center")
    lg.column_dimensions[cell.column_letter].width = width
lg.row_dimensions[1].height = 34
lg.freeze_panes = "A2"

for r in range(2, ROWS + 2):
    for c, (_, _, fmt) in enumerate(cols, start=1):
        cell = lg.cell(r, c)
        cell.border = BOX
        if fmt:
            cell.number_format = fmt
    # rate follows the Type column; owed = invoice x rate, blank until there is an invoice
    lg.cell(r, 9).value = f'=IF(AND(E{r}="Parts",{PARTS_RATE}<>""),{PARTS_RATE},IF(AND(E{r}="Service",{SERVICE_RATE}<>""),{SERVICE_RATE},""))'
    lg.cell(r, 10).value = f'=IF(AND(ISNUMBER(H{r}),ISNUMBER(I{r})),ROUND(H{r}*I{r},2),"")'

last = ROWS + 1
for rng, opts in ((f"E2:E{last}", '"Service,Parts"'),
                  (f"F2:F{last}", '"Code in message,QR scan,Phone call,Walk-in"'),
                  (f"K2:K{last}", '"No,Yes"')):
    dv = DataValidation(type="list", formula1=opts, allow_blank=True)
    lg.add_data_validation(dv)
    dv.add(rng)
lg.conditional_formatting.add(f"A2:M{last}", FormulaRule(formula=['$K2="Yes"'],
                              fill=PatternFill("solid", fgColor="E3F4E8")))

# ---- SUMMARY --------------------------------------------------------------------------------
sm = wb.create_sheet("SUMMARY", 0)
sm.column_dimensions["A"].width = 34
sm.column_dimensions["B"].width = 18
sm["A1"] = "REFERRALS  ·  " + CODE
sm["A1"].font = Font(name="Arial", bold=True, size=16, color=WHITE)
sm["A1"].fill = HEAD_FILL
sm.merge_cells("A1:B1")
lines = [
    ("Referred customers", f'=COUNTA(LOG!B2:B{last})', "0"),
    ("Invoice total referred ($)", f'=SUM(LOG!H2:H{last})', '"$"#,##0.00'),
    ("Commission earned ($)", f'=SUM(LOG!J2:J{last})', '"$"#,##0.00'),
    ("Commission paid ($)", f'=SUMIF(LOG!K2:K{last},"Yes",LOG!J2:J{last})', '"$"#,##0.00'),
    ("Commission still owed ($)", "=B5-B6", '"$"#,##0.00'),
]
for i, (a, f, fmt) in enumerate(lines, start=3):
    sm.cell(i, 1, a).font = Font(name="Arial", bold=(i == 7))
    cell = sm.cell(i, 2, f)
    cell.number_format = fmt
    cell.border = BOX
    if i == 7:
        cell.font = Font(name="Arial", bold=True, color=RED)
sm["A9"] = "Rates and terms are placeholders on the SETTINGS tab until Nate signs off."
sm["A9"].font = Font(name="Arial", italic=True, color="7A7A82")

OUT.parent.mkdir(exist_ok=True)
wb.save(OUT)
print(OUT)
