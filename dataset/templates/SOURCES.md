# Template sources

Checked on 15 October 2026.

Our generator draws its own page layouts. It does not fill or copy any official form. The sources below were used only to choose which fields appear and in what order.

## Obtained

| File | What it is | Source | Used for |
|---|---|---|---|
| `official/MEG_circular_3_2024_FIR.pdf` | Meghalaya Police, Office of the Director General of Police, Circular No. 03/2024 (First Information Report). Annexure-1 (pages 14 and 15) is the prescribed FIR format, with 26 numbered items. The circular refers to BNSS sections, so it dates from after the new criminal laws. | https://megpolice.gov.in/sites/default/files/circular-no.3-2024-first-information-report.pdf | Field list and order of our FIR layout (district, police station, FIR number, acts and sections, date and time of occurrence, information received at PS, place of occurrence, complainant particulars, suspects, property value, contents, action taken, officer signature and seal). |

## Not obtained

| Form | What happened |
|---|---|
| Blank FIR form (Puducherry Police, "FORM IF1", Integrated Form, CrPC era) | Found in search results at `police.py.gov.in/Police manual/Forms pdf/`. Every URL tried on 15 October 2026 returned HTTP 404. |
| Blank final report / charge sheet form (Puducherry Police, "FORM IF5", Section 173 CrPC era) | Same site. Returned HTTP 404. |
| Official BNSS-era charge sheet form | No official blank form found online. Our charge sheet layout uses the items commonly listed for a final report (district, police station, FIR number and date, charge sheet number and date, court, acts and sections, accused with parentage and age, victims, property, vehicles, list of witnesses, brief facts, investigating officer). TODO: verify against an official state format. |
| Witness statement form | No standard form found. Statements are usually written on plain paper. Our layout is a simple header plus the statement body. |
| Court order or court-stamped copy | Not a document type in scope (SCOPE.md). A court receipt stamp is added as a tamper variant (`A_COURT_STAMP`) instead. |

A Uttar Pradesh Police CCTNS PDF was also downloaded. It turned out to be a Hindi user guide for filling the final form on CCTNS, not a blank form, so it was deleted.

## Action for the team

If someone can get blank official FIR, final report and statement formats (for example from a state police website or a police station), add them to `official/` and note the source here. The layouts in `ml/data/generator/render.py` can then be brought closer to them.
