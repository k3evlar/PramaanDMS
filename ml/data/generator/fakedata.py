"""Invented values for the FIR-Tamper dataset.

Nothing here refers to a real person, place, vehicle, phone or case.

- Names are common Indian given names and surnames combined at random.
- District, police station and locality names are invented. Any match with a
  real place is a coincidence.
- Phone numbers start with "10". Indian mobile numbers start with 6 to 9, so
  these cannot reach a real phone (TODO: verify the numbering rule in Phase 2).
- Vehicle numbers use the state code "ZZ", which is not a real state code.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

MALE_FIRST: list[str] = [
    "Ramesh", "Suresh", "Mahesh", "Rajesh", "Dinesh", "Mukesh", "Anil", "Sunil",
    "Vijay", "Ajay", "Sanjay", "Manoj", "Rakesh", "Arun", "Vinod", "Pramod",
    "Ashok", "Deepak", "Naresh", "Harish", "Gopal", "Mohan", "Kishan", "Ravi",
    "Sandeep", "Pankaj", "Alok", "Nitin", "Rohit", "Amit", "Vikas", "Yogesh",
    "Hemant", "Satish", "Lalit", "Bharat", "Kamal", "Prakash", "Raghav", "Tarun",
]

FEMALE_FIRST: list[str] = [
    "Sunita", "Anita", "Kavita", "Savita", "Geeta", "Seema", "Rekha", "Asha",
    "Usha", "Meena", "Pooja", "Neha", "Priya", "Ritu", "Kiran", "Manju",
    "Suman", "Lata", "Radha", "Sarita", "Nisha", "Jyoti", "Shobha", "Anjali",
    "Pushpa", "Kamla", "Rani", "Deepa", "Sapna", "Vandana",
]

SURNAMES: list[str] = [
    "Sharma", "Verma", "Gupta", "Yadav", "Singh", "Kumar", "Patel", "Joshi",
    "Mishra", "Pandey", "Tiwari", "Chauhan", "Rathore", "Saxena", "Agarwal",
    "Mehta", "Shah", "Nair", "Reddy", "Rao", "Das", "Bose", "Ghosh", "Sinha",
    "Thakur", "Rawat", "Bisht", "Negi", "Kulkarni", "Deshmukh", "Pillai",
    "Menon", "Khan", "Qureshi", "Ansari", "Gill", "Sandhu", "Bhatt", "Dubey",
    "Shukla",
]

# Invented district names.
DISTRICTS: list[str] = [
    "Navgarh", "Kesarpur", "Dhanauli", "Ambikanagar", "Sitalpur",
    "Rajkhet", "Bhavanpur", "Chandoli", "Meghpura", "Tulsigram",
]

# Police station name parts. Combined with a district they form an invented station.
STATION_NAMES: list[str] = [
    "Kotwali", "Civil Lines", "Sadar Bazar", "Railway Colony", "Industrial Area",
    "Lake View", "Hill Road", "Cantonment", "Old City", "New Market",
]

LOCALITIES: list[str] = [
    "Gandhi Colony", "Station Road", "Old Market", "Shanti Vihar", "Ram Nagar",
    "Nehru Park Extension", "Subhash Marg", "Ganga Vihar", "Mill Area",
    "Teachers Colony", "Azad Nagar", "Patel Chowk", "Rose Garden Lane",
    "Sector 4", "Sector 11", "Bus Stand Road", "Hospital Road", "Canal Road",
]

LANDMARKS: list[str] = [
    "the bus stand", "the water tank", "the government school",
    "the vegetable market", "the petrol pump", "the temple gate",
    "the post office", "the railway crossing", "the community hall",
    "the public library",
]

COURT_TYPES: list[str] = [
    "Court of the Judicial Magistrate First Class",
    "Court of the Chief Judicial Magistrate",
    "Court of the Additional Chief Judicial Magistrate",
]

# Rank display text -> rank code (CRITICAL_FIELDS.md, text (rank) rule).
RANKS: dict[str, str] = {
    "Sub-Inspector": "SUB_INSPECTOR",
    "Inspector": "INSPECTOR",
    "Assistant Sub-Inspector": "ASSISTANT_SUB_INSPECTOR",
}

VEHICLE_SERIES: list[str] = ["AB", "CD", "EF", "GH", "JK", "LM", "PQ", "RS", "TU", "XY"]


@dataclass(frozen=True)
class Person:
    """A person as printed on a document."""

    first: str
    last: str
    gender: str  # "M" or "F"
    honorific: str  # "", "Shri" or "Smt" (kept as written, CRITICAL_FIELDS.md Q1)

    @property
    def name(self) -> str:
        base = f"{self.first} {self.last}"
        return f"{self.honorific} {base}" if self.honorific else base


def make_person(rng: random.Random, gender: str | None = None, used: set[str] | None = None,
                honorific_rate: float = 0.4) -> Person:
    """Make a person whose plain name is not already in `used`."""
    while True:
        g = gender or rng.choice(["M", "M", "F"])
        first = rng.choice(MALE_FIRST if g == "M" else FEMALE_FIRST)
        last = rng.choice(SURNAMES)
        key = f"{first} {last}"
        if used is not None and key in used:
            continue
        if used is not None:
            used.add(key)
        hon = ""
        if rng.random() < honorific_rate:
            hon = "Shri" if g == "M" else "Smt"
        return Person(first=first, last=last, gender=g, honorific=hon)


def relation_for(p: Person, rng: random.Random) -> str:
    """Relation marker printed before a relative's name."""
    if p.gender == "M":
        return "S/o"
    return rng.choice(["D/o", "W/o"])


def make_phone(rng: random.Random) -> str:
    """Ten digits starting with 10 (not a valid Indian mobile prefix)."""
    return "10" + "".join(str(rng.randint(0, 9)) for _ in range(8))


def make_vehicle(rng: random.Random) -> str:
    """Canonical vehicle number with the invented state code ZZ."""
    return f"ZZ{rng.randint(1, 40):02d}{rng.choice(VEHICLE_SERIES)}{rng.randint(1000, 9999)}"


def make_officer_id(rng: random.Random) -> str:
    return f"ZZP{rng.randint(100000, 999999)}"


def make_address(rng: random.Random, district: str) -> str:
    return f"House No. {rng.randint(1, 399)}, {rng.choice(LOCALITIES)}, {district}"


# ---------------------------------------------------------------------------
# Evidence and custody (FIR-Tamper v3 Stage 2, D96)
# ---------------------------------------------------------------------------

# Items listed as property involved (FIR) or seized (charge sheet), per scenario.
PROPERTY_ITEMS: dict[str, list[str]] = {
    "house_theft": ["Wrist watch", "Jewellery box", "Leather purse", "Mobile phone"],
    "vehicle_theft": ["Motorcycle", "Helmet", "Key ring", "Saddle bag"],
    "assault": ["Wooden stick", "Iron rod", "Torn shirt", "Mobile phone"],
    "cheating": ["Mobile phone", "SIM card", "Bank passbook", "Debit card"],
    "chain_snatching": ["Neck chain", "Motorcycle", "Helmet", "Jacket"],
    "mobile_theft": ["Mobile phone", "Phone cover", "Shoulder bag", "Power bank"],
    "criminal_trespass": ["Flower pot", "Gate lock", "Ladder", "Torch"],
    "upi_fraud": ["Mobile phone", "SIM card", "Bank passbook", "Laptop"],
    "shop_burglary": ["Cash box", "Shutter lock", "Iron rod", "Cloth bag"],
    "road_accident": ["Side mirror", "Bumper piece", "Mobile phone", "Helmet"],
    "breach_of_trust": ["Receipt book", "Cash bag", "Mobile phone", "Diary"],
    "land_intimidation": ["Fence post", "Tractor key", "Iron rod", "Spade"],
}
ITEM_COLOURS: list[str] = ["black", "grey", "red", "blue", "white", "brown", "green", "yellow"]
QTY_WORDS: list[str] = ["one", "two", "three", "four"]

# Printed purpose of each custody entry, in order (row 31).
CUSTODY_PURPOSES: list[str] = [
    "Seized at the spot by",
    "Deposited in the police station store (malkhana) with",
    "Sent to the forensic science laboratory through",
    "Received back in the store by",
]


def make_item(rng: random.Random, scenario: str, exclude: set[str]) -> str:
    """One property item, for example 'Mobile phone (black), quantity: one'."""
    item = rng.choice([i for i in PROPERTY_ITEMS[scenario] if i not in exclude])
    qty = rng.choice(["one", "one", "two"])
    return f"{item} ({rng.choice(ITEM_COLOURS)}), quantity: {qty}"


def make_exhibit_id(rng: random.Random, year: int, k: int) -> str:
    return f"EX/{rng.randint(100, 899) + k}/{year}"
