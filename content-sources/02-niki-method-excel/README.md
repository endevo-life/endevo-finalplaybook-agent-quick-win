# 02 — Niki's method (Excel)

Upload Niki's refined method spreadsheet — the "start here → deliver Final
Playbook" workbook with the left-to-right sheets she's tuned over time.

- Drop the `.xlsx`/`.xls`/`.csv` (or a Google Sheets export) directly here.
- If it's multiple linked sheets, keep them together / note the tab order.
- A screenshot of the sheet layout also helps me read the left-to-right flow.

What gets mined from these: the **deterministic delivery order** (which sheet/
step comes first, second, …), the domain each step belongs to (digital, legal,
financial, physical, communication/beliefs), and the "basic steps first" rules.

Niki's column structure maps to the content model roughly as:

| Niki's sheet concept | Content-library field |
|---|---|
| Step / row order (left-to-right, top-down) | `priorityOrder` / action-item sequence |
| Step description | `actionItem.text` |
| Exact wording she says | `actionItem.script` |
| Domain (digital/legal/financial/physical/comms) | `actionItem.domain` |
| "only if X applies" | `actionItem.flag` (situational gate) |

Once it's here I'll produce a mapping in `../_processed/` for you to confirm
before anything touches the live library.
