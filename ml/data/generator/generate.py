"""Build base (original) documents with invented content."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from . import fakedata as fd
from .model import (AMOUNT_FORMATS, DATE_FORMATS, DOC_PREFIX, FIR_FORMATS, FONTS, PHONE_FORMATS,
                    SECTION_FORMATS, TIME_FORMATS, VEHICLE_FORMATS, Doc, Signature, Stamp, Style)
from .narrative import FAMILY_B_SCENARIOS, build_narrative, family_of

# Family A scenarios (train, val, test). The first four are the v0 scenarios.
SCENARIOS: tuple[str, ...] = ("house_theft", "vehicle_theft", "assault", "cheating",
                              "chain_snatching", "mobile_theft", "criminal_trespass", "upi_fraud",
                              "shop_burglary")
# Family B scenarios: held out for the test_unseen split only (D96).
HELD_OUT_SCENARIOS: tuple[str, ...] = FAMILY_B_SCENARIOS

# BNS section numbers used as example values. The mapping of numbers to offences
# is not verified here (TODO: verify against the BNS 2023 Gazette text before the
# paper or demo describes these as the correct sections for each offence).
SCENARIO_SECTIONS: dict[str, list[str]] = {
    "house_theft": ["BNS:305", "BNS:331(4)"],
    "vehicle_theft": ["BNS:303(2)"],
    "assault": ["BNS:115(2)", "BNS:351(2)", "BNS:352"],
    "cheating": ["BNS:318(4)", "BNS:319(2)"],
    "chain_snatching": ["BNS:304(2)"],
    "mobile_theft": ["BNS:303(2)"],
    "criminal_trespass": ["BNS:329(3)", "BNS:351(2)"],
    "upi_fraud": ["BNS:318(4)", "BNS:319(2)"],
    "shop_burglary": ["BNS:331(4)", "BNS:305"],
    "road_accident": ["BNS:281", "BNS:125(a)"],
    "breach_of_trust": ["BNS:316(2)"],
    "land_intimidation": ["BNS:351(2)", "BNS:329(3)"],
}
COMMON_INTENTION = "BNS:3(5)"
SECTION_POOL: list[str] = ["BNS:303(2)", "BNS:305", "BNS:309(4)", "BNS:115(2)", "BNS:117(2)",
                           "BNS:118(1)", "BNS:318(4)", "BNS:319(2)", "BNS:324(4)", "BNS:329(3)",
                           "BNS:331(4)", "BNS:351(2)", "BNS:352", "BNS:304(2)", "BNS:281", "BNS:125(a)",
                           "BNS:316(2)"]

AMOUNT_RANGE: dict[str, tuple[int, int]] = {
    "house_theft": (20000, 800000),
    "vehicle_theft": (25000, 150000),
    "assault": (6000, 45000),
    "cheating": (10000, 500000),
    "chain_snatching": (20000, 150000),
    "mobile_theft": (8000, 90000),
    "criminal_trespass": (2000, 30000),
    "upi_fraud": (5000, 300000),
    "shop_burglary": (10000, 400000),
    "road_accident": (5000, 200000),
    "breach_of_trust": (20000, 600000),
    "land_intimidation": (5000, 80000),
}

# All documents are dated after the BNS commencement date (1 July 2024, D26),
# so clean samples must not trigger the backdating rule.
FIRST_INCIDENT = date(2024, 7, 5)
LAST_INCIDENT = date(2026, 6, 30)
LAST_DOC_DATE = date(2026, 9, 30)

PS_STAMP_COLOURS: list[tuple[float, float, float]] = [(0.33, 0.18, 0.62), (0.12, 0.25, 0.66)]


def _rand_date(rng: random.Random, lo: date, hi: date) -> date:
    return lo + timedelta(days=rng.randint(0, (hi - lo).days))


def _rand_time(rng: random.Random, lo_h: int = 6, hi_h: int = 22) -> str:
    return f"{rng.randint(lo_h, hi_h):02d}:{rng.choice(range(0, 60, 5)):02d}"


def _amount(rng: random.Random, scenario: str) -> int:
    lo, hi = AMOUNT_RANGE[scenario]
    if rng.random() < 0.25 and hi >= 100000:
        return rng.randint(max(1, lo // 100000), hi // 100000) * 100000  # round lakhs
    step = rng.choice([500, 1000, 1])
    return max(lo, (rng.randint(lo, hi) // step) * step)


def random_style(rng: random.Random) -> Style:
    return Style(
        font=rng.choice(FONTS),
        font_size=rng.choice([10.0, 10.5, 11.0]),
        leading=rng.choice([1.3, 1.4]),
        margin=rng.choice([56.0, 62.0, 70.0]),
        date_fmt=rng.choice(DATE_FORMATS),
        time_fmt=rng.choice(TIME_FORMATS),
        amount_fmt=rng.choice(AMOUNT_FORMATS),
        vehicle_fmt=rng.choice(VEHICLE_FORMATS),
        phone_fmt=rng.choice(PHONE_FORMATS),
        fir_fmt=rng.choice(FIR_FORMATS),
        section_fmt=rng.choice(SECTION_FORMATS),
        name_upper=rng.random() < 0.2,
    )


def make_base_doc(doc_type: str, index: int, scenario: str, long: bool,
                  rng: random.Random) -> Doc:
    used: set[str] = set()
    district = rng.choice(fd.DISTRICTS)
    station = rng.choice(fd.STATION_NAMES)
    incident = _rand_date(rng, FIRST_INCIDENT, LAST_INCIDENT)
    t_incident = _rand_time(rng)
    report = incident + timedelta(days=rng.choice([0, 0, 1, 1, 2, 3]))
    if report == incident:
        h = min(23, int(t_incident[:2]) + rng.randint(1, 3))
        t_report = f"{h:02d}:{rng.choice(range(0, 60, 5)):02d}"
    else:
        t_report = _rand_time(rng, 8, 21)
    fir_number = f"{rng.randint(1, 950)}/{report.year}"
    landmark = rng.choice(fd.LANDMARKS)
    place = f"{rng.choice(fd.LOCALITIES)}, near {landmark}"

    complainant = fd.make_person(rng, used=used)
    comp_relative = fd.make_person(rng, gender="M", used=used, honorific_rate=0.3)
    n_accused = rng.choice([1, 1, 2, 3]) if doc_type != "STATEMENT" else rng.choice([1, 1, 2])
    accused = [fd.make_person(rng, gender="M", used=used, honorific_rate=0.15) for _ in range(n_accused)]
    acc_relatives = [fd.make_person(rng, gender="M", used=used, honorific_rate=0.3) for _ in accused]
    acc_ages = [rng.randint(19, 60) for _ in accused]
    if rng.random() < 0.3:
        victims = [complainant]  # the complainant is also the victim
    else:
        victims = [fd.make_person(rng, used=used) for _ in range(rng.choice([1, 1, 2]))]
    n_wit = 1 if doc_type == "STATEMENT" else rng.randint(2, 5)
    witnesses = [fd.make_person(rng, used=used) for _ in range(n_wit)]

    sections = list(SCENARIO_SECTIONS[scenario])
    if len(sections) > 1 and rng.random() < 0.35:
        sections = [rng.choice(sections)]  # one law section only
    if n_accused > 1 and rng.random() < 0.6:
        sections.append(COMMON_INTENTION)
    amount = _amount(rng, scenario)
    vehicles = [fd.make_vehicle(rng) for _ in range(rng.choice([1, 1, 2]))]
    phones = [fd.make_phone(rng) for _ in range(rng.choice([1, 2]) if doc_type == "FIR" else 1)]
    officer = fd.make_person(rng, used=used, honorific_rate=0.0)
    rank = rng.choice(list(fd.RANKS.values()))

    stmt_date = report + timedelta(days=rng.randint(1, 20))
    cs_date = min(LAST_DOC_DATE, report + timedelta(days=rng.randint(30, 85)))

    # Evidence and custody (rows 28 to 31, D96). Items are listed in FIRs and charge sheets;
    # exhibit IDs, the seizure date and the custody chain appear in charge sheets.
    items: list[str] = []
    for _ in range(rng.choice([1, 2, 3])):
        items.append(fd.make_item(rng, scenario, {i.split(" (")[0] for i in items}))
    seizure = report + timedelta(days=rng.randint(0, 7))
    n_entries = rng.choice([2, 3, 4])
    holders = [fd.make_person(rng, gender="M", used=used, honorific_rate=0.0).name for _ in range(n_entries)]
    c_dates = [seizure]
    for gap in [(0, 1), (2, 10), (5, 20)][: n_entries - 1]:
        c_dates.append(c_dates[-1] + timedelta(days=rng.randint(*gap)))
    cs_date = max(cs_date, c_dates[-1] + timedelta(days=3))
    exhibits = [fd.make_exhibit_id(rng, seizure.year, k) for k in range(len(items))]
    cs_number = f"{rng.randint(1, 400)}/{cs_date.year}"
    court = f"{rng.choice(fd.COURT_TYPES)}, {district}"

    all_fields: dict[str, Any] = {
        "fir_number": fir_number,
        "police_station": station,
        "district": district,
        "date_of_report": report.isoformat(),
        "time_of_report": t_report,
        "date_of_incident": incident.isoformat(),
        "time_of_incident": t_incident,
        "place_of_incident": place,
        "complainant_name": complainant.name,
        "complainant_relative_name": comp_relative.name,
        "accused_names": tuple(p.name for p in accused),
        "accused_relative_names": tuple(p.name for p in acc_relatives),
        "accused_ages": tuple(acc_ages),
        "victim_names": tuple(p.name for p in victims),
        "witness_names": tuple(p.name for p in witnesses),
        "law_sections": tuple(sections),
        "property_value": amount,
        "vehicle_numbers": tuple(vehicles),
        "phone_numbers": tuple(phones),
        "officer_name": officer.name,
        "officer_rank": rank,
        "officer_id": fd.make_officer_id(rng),
        "date_of_statement": stmt_date.isoformat(),
        "charge_sheet_number": cs_number,
        "charge_sheet_date": cs_date.isoformat(),
        "court_name": court,
        "complainant_address": fd.make_address(rng, district),
        "property_items": tuple(items),
        "exhibit_ids": tuple(exhibits),
        "seizure_date": seizure.isoformat(),
        "custody_holders": tuple(holders),
        "custody_dates": tuple(d.isoformat() for d in c_dates),
    }
    from .model import fields_for
    fields = {k: all_fields[k] for k in fields_for(doc_type)}
    relations = {
        "complainant": fd.relation_for(complainant, rng),
        "accused": tuple(fd.relation_for(p, rng) for p in accused),
        "custody": tuple(fd.CUSTODY_PURPOSES[:n_entries]),
    }

    case = {
        "complainant": complainant.name, "accused": accused[0].name, "witness": witnesses[0].name,
        "date_incident": incident.isoformat(), "time_incident": t_incident, "amount": amount,
        "vehicle": vehicles[0], "landmark": landmark, "place": place, "district": district,
    }
    narrative = build_narrative(doc_type, scenario, case, rng, long)

    doc_id = f"{DOC_PREFIX[doc_type]}-{index:04d}"
    ps_stamp = Stamp(kind="ps", ring_text=f"POLICE STATION {station.upper()} * {district.upper()} *",
                     center_text="P.S.", page=-1, color=rng.choice(PS_STAMP_COLOURS),
                     angle=rng.uniform(-14, 14))
    sigs = [Signature("officer", rng.randint(1, 10**9))]
    if doc_type == "FIR":
        sigs.insert(0, Signature("complainant", rng.randint(1, 10**9)))
    elif doc_type == "STATEMENT":
        sigs.insert(0, Signature("witness", rng.randint(1, 10**9)))
    style = random_style(rng)
    style = Style(**{**style.__dict__, "pdf_title": f"{doc_type} {doc_id}"})
    return Doc(doc_id=doc_id, doc_type=doc_type, scenario=scenario, fields=fields,
               relations=relations, narrative=narrative, stamps=(ps_stamp,),
               signatures=tuple(sigs), style=style,
               meta={"long": long, "n_sentences": len(narrative), "family": family_of(scenario)})
