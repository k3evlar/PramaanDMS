"""Narrative sentence templates for the FIR-Tamper dataset (English).

Each template has two phrasings with the same meaning (used for the reword
edit), plus typed slots:

- entity slots: values taken from the case (dates, names, amounts, vehicles)
- choice slots (c_*): a word picked from a list (used for the word swap edit)
- negation slots (n_*): a positive and a negative form (used for the negation edit)
- modal slots (m_*): a base form and a shifted modal or quantifier (used for the modal
  edit, E12), for example "saw" and "think I saw", or "all" and "some of"

Every slot appears in both phrasings, so an edit is always visible on the page.

Templates belong to one of two families (D96). Family A is used for train, val and test;
family B (its own scenarios and generic sentences) only for the test_unseen split, so that
split shares no sentence template with training.

All text is invented. Section numbers are not mentioned in narratives.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from .model import Sentence, Style, fmt_amount, fmt_date, fmt_time, fmt_vehicle


@dataclass(frozen=True)
class Template:
    tid: str
    phrasings: tuple[str, str]
    choices: dict[str, tuple[str, ...]] = field(default_factory=dict)
    negs: dict[str, tuple[str, str]] = field(default_factory=dict)  # slot -> (positive, negative)
    mods: dict[str, tuple[str, str]] = field(default_factory=dict)  # slot -> (base, shifted)


def _t(tid: str, p1: str, p2: str, choices: dict[str, tuple[str, ...]] | None = None,
       negs: dict[str, tuple[str, str]] | None = None,
       mods: dict[str, tuple[str, str]] | None = None) -> Template:
    return Template(tid, (p1, p2), choices or {}, negs or {}, mods or {})


JOBS = ("shopkeeper", "teacher", "tailor", "clerk", "driver", "farmer")
COLOURS = ("red", "black", "blue", "grey")
WEAPONS = ("wooden stick", "iron rod", "brick")

# Narrative entities (D45): dates, times, names, numbers, amounts and vehicle numbers
# inside the narrative get exact fingerprints, so a change to any of them is Major.
# Places and landmarks stay semantic (compared by the narrative hash).
ENTITY_SLOTS: dict[str, str] = {
    "date_incident": "date", "time_incident": "time", "amount": "number",
    "accused": "name", "complainant": "name", "witness": "name", "vehicle": "id",
}

# ---- FIR (first person, complainant) --------------------------------------
FIR_INTRO = _t("FIR_INTRO",
               "I, {complainant}, live at the above address with my family and work as a {c_job}.",
               "My name is {complainant}. I live at the above address with my family, and I work as a {c_job}.",
               {"c_job": JOBS})
FIR_CLOSE = _t("FIR_CLOSE",
               "I request that a case be registered and that strict action be taken against the accused.",
               "I request you to register a case and take strict action against the accused.")

FIR_CORE: dict[str, list[Template]] = {
    "house_theft": [
        _t("HT_LEFT", "On {date_incident} at about {time_incident}, we locked the house and went to visit relatives in a nearby village.",
           "On {date_incident}, at around {time_incident}, my family and I locked the house and left to visit relatives in a nearby village."),
        _t("HT_LOCK", "When we came back, I saw that the lock of the main door was broken.",
           "On our return, I found the lock of the main door broken."),
        _t("HT_LOSS", "Gold ornaments and cash worth {amount} were missing from the {c_store}.",
           "Someone had taken gold ornaments and cash worth {amount} from the {c_store}.",
           {"c_store": ("steel almirah in the bedroom", "wooden cupboard in the hall", "trunk in the store room")}),
        _t("HT_DOOR", "The {c_door} door of the house {n_was} found open.",
           "We found that the {c_door} door of the house {n_was} open.",
           {"c_door": ("back", "side", "kitchen")}, {"n_was": ("was", "was not")}),
        _t("HT_SEEN", "My neighbour told me that he {m_had} seen {accused} near my house that evening.",
           "According to my neighbour, he {m_had} seen {accused} near my house that evening.",
           mods={"m_had": ("had", "might have")}),
        _t("HT_BIKE", "{accused} left on a {c_colour} motorcycle bearing number {vehicle}.",
           "{accused} went away on a {c_colour} motorcycle with registration number {vehicle}.",
           {"c_colour": COLOURS}),
    ],
    "vehicle_theft": [
        _t("VT_PARK", "On {date_incident} at about {time_incident}, I parked my {c_colour} motorcycle bearing number {vehicle} near {landmark}.",
           "At around {time_incident} on {date_incident}, I left my {c_colour} motorcycle, number {vehicle}, parked near {landmark}.",
           {"c_colour": COLOURS}),
        _t("VT_GONE", "When I returned after about {c_minutes} minutes, the motorcycle was not there.",
           "About {c_minutes} minutes later, I came back and found that the motorcycle was gone.",
           {"c_minutes": ("twenty", "thirty", "forty-five")}),
        _t("VT_VALUE", "The value of the motorcycle is about {amount}.",
           "The motorcycle is worth about {amount}."),
        _t("VT_SEEN", "A shopkeeper nearby told me that he {m_saw} {accused} pushing the motorcycle towards the main road.",
           "A nearby shopkeeper said that he {m_saw} {accused} pushing the motorcycle towards the main road.",
           mods={"m_saw": ("saw", "thought he saw")}),
        _t("VT_LOCK", "I {n_had} locked the handle of the motorcycle before leaving.",
           "Before leaving, I {n_had} locked the handle of the motorcycle.",
           negs={"n_had": ("had", "had not")}),
    ],
    "assault": [
        _t("AS_WALK", "On {date_incident} at about {time_incident}, I was returning home from work near {landmark}.",
           "At around {time_incident} on {date_incident}, I was walking home from work near {landmark}."),
        _t("AS_STOP", "{accused} stopped me and started abusing me over an old dispute about a {c_dispute}.",
           "{accused} stopped me there and abused me because of an old dispute about a {c_dispute}.",
           {"c_dispute": ("boundary wall", "water connection", "parking space")}),
        _t("AS_HIT", "He hit me {m_times} on my {c_body} with a {c_weapon}, and I fell down.",
           "He struck my {c_body} {m_times} with a {c_weapon}, and I fell to the ground.",
           {"c_body": ("left arm", "head", "back"), "c_weapon": WEAPONS}, mods={"m_times": ("twice", "once")}),
        _t("AS_THREAT", "He {n_did} threaten to kill me if I went to the police.",
           "He {n_did} say that he would kill me if I went to the police.",
           negs={"n_did": ("did", "did not")}),
        _t("AS_PHONE", "During the attack, my mobile phone worth {amount} fell and was broken.",
           "My mobile phone, worth {amount}, fell and broke during the attack."),
        _t("AS_RUN", "He ran away on a scooter bearing number {vehicle}.",
           "He escaped on a scooter with registration number {vehicle}."),
    ],
    "cheating": [
        _t("CH_CALL", "On {date_incident} at about {time_incident}, I received a call from a person who said he was a bank officer.",
           "At around {time_incident} on {date_incident}, a caller who claimed to be a bank officer phoned me."),
        _t("CH_OTP", "He said that my account would be blocked unless I shared a one-time password.",
           "The caller told me that my account would be blocked if I did not share a one-time password."),
        _t("CH_SHARE", "I {n_did} share the password with him.",
           "I {n_did} give him the password.",
           negs={"n_did": ("did", "did not")}),
        _t("CH_DEBIT", "Soon after, {amount} was debited from my account in {c_parts} transactions.",
           "Shortly afterwards, {amount} was taken from my account in {c_parts} transactions.",
           {"c_parts": ("two", "three", "four")}),
        _t("CH_ACCT", "Later I learnt that the money {m_went} to an account held by {accused}.",
           "I later came to know that the money {m_went} to an account in the name of {accused}.",
           mods={"m_went": ("was sent", "may have been sent")}),
        _t("CH_BIKE", "{accused} was seen visiting the bank branch on a motorcycle bearing number {vehicle}.",
           "{accused} visited the bank branch on a motorcycle with registration number {vehicle}."),
    ],
    # ---- Family A scenarios added in v3 Stage 2 ----
    "chain_snatching": [
        _t("CN_WALK", "On {date_incident} at about {time_incident}, I was walking near {landmark} when two men came on a {c_colour} motorcycle.",
           "At around {time_incident} on {date_incident}, while I was walking near {landmark}, two men came up on a {c_colour} motorcycle.",
           {"c_colour": COLOURS}),
        _t("CN_PULL", "The pillion rider pulled the gold chain from my neck, and they sped away.",
           "The man sitting behind pulled my gold chain off my neck, and they rode away fast."),
        _t("CN_WORTH", "The chain weighed about {c_grams} grams and is worth about {amount}.",
           "The chain is worth about {amount} and weighed nearly {c_grams} grams.",
           {"c_grams": ("ten", "fifteen", "twenty")}),
        _t("CN_PLATE", "I {m_noted} that the motorcycle bore number {vehicle}.",
           "I {m_noted} the number of the motorcycle, which was {vehicle}.",
           mods={"m_noted": ("noted", "think I noted")}),
        _t("CN_RIDER", "Later, people in the area told me that the rider was {accused}.",
           "People in the area later told me that the rider was {accused}."),
        _t("CN_HURT", "My neck {n_was} hurt when the chain was pulled.",
           "When the chain was pulled, my neck {n_was} hurt.",
           negs={"n_was": ("was", "was not")}),
    ],
    "mobile_theft": [
        _t("MT_BUS", "On {date_incident} at about {time_incident}, I was travelling in a crowded bus near {landmark}.",
           "At around {time_incident} on {date_incident}, I was in a crowded bus near {landmark}."),
        _t("MT_KEPT", "My {c_colour} mobile phone worth {amount} was in the {c_pocket} of my bag.",
           "I had kept my {c_colour} mobile phone, worth {amount}, in the {c_pocket} of my bag.",
           {"c_colour": COLOURS, "c_pocket": ("front pocket", "side pocket", "inner pocket")}),
        _t("MT_GONE", "When I got down, I found that the phone was missing.",
           "After I got down, I saw that the phone was gone."),
        _t("MT_CLOSE", "A passenger said that {accused} {m_had} been standing close to me.",
           "According to a passenger, {accused} {m_had} been standing close to me.",
           mods={"m_had": ("had", "may have")}),
        _t("MT_LOCK", "I {n_had} locked the phone with a password.",
           "Before the journey, I {n_had} locked the phone with a password.",
           negs={"n_had": ("had", "had not")}),
        _t("MT_LEFT", "{accused} was later seen getting off at the next stop.",
           "{accused} was later seen leaving the bus at the next stop."),
    ],
    "criminal_trespass": [
        _t("TR_FOUND", "On {date_incident} at about {time_incident}, I found {accused} inside the compound of my house, uninvited.",
           "At around {time_incident} on {date_incident}, {accused} came into the compound of my house, uninvited."),
        _t("TR_WALL", "He had climbed over the {c_wall} to get in.",
           "He got in by climbing over the {c_wall}.",
           {"c_wall": ("back wall", "side gate", "front gate")}),
        _t("TR_POT", "When I asked him to leave, he threatened me and broke a flower pot worth {amount}.",
           "He threatened me when I asked him to leave, and broke a flower pot worth {amount}."),
        _t("TR_FAMILY", "In the house, {m_all} the members of my family saw him in the compound.",
           "At home, {m_all} the members of my family saw him in the compound.",
           mods={"m_all": ("all", "some of")}),
        _t("TR_SCOOTER", "He left on a scooter bearing number {vehicle}.",
           "He went away on a scooter with registration number {vehicle}."),
        _t("TR_BEFORE", "He {n_has} done this before.",
           "Before this, he {n_has} done the same thing.",
           negs={"n_has": ("has", "has not")}),
    ],
    "upi_fraud": [
        _t("UF_MSG", "On {date_incident} at about {time_incident}, I received a message about a reward on my mobile phone.",
           "At around {time_incident} on {date_incident}, a message about a reward came on my mobile phone."),
        _t("UF_CODE", "The message asked me to scan a code to receive the money.",
           "To receive the money, the message told me to scan a code."),
        _t("UF_DEBIT", "After I scanned the code, {amount} was debited from my bank account.",
           "Once I scanned the code, {amount} was taken from my bank account."),
        _t("UF_ACCT", "The bank told me that the money {m_went} to an account held by {accused}.",
           "As per the bank, the money {m_went} to an account of {accused}.",
           mods={"m_went": ("went", "may have gone")}),
        _t("UF_BEFORE", "I {n_had} received such a message before.",
           "Before this, I {n_had} received such a message.",
           negs={"n_had": ("had", "had not")}),
        _t("UF_INFORM", "I informed the bank on its {c_channel} within an hour.",
           "Within an hour, I informed the bank on its {c_channel}.",
           {"c_channel": ("helpline number", "customer care number", "mobile app")}),
    ],
    "shop_burglary": [
        _t("SB_OPEN", "On {date_incident} at about {time_incident}, I came to open my shop near {landmark} and found the shutter lock broken.",
           "At around {time_incident} on {date_incident}, when I came to open my shop near {landmark}, the shutter lock was broken."),
        _t("SB_CASH", "Cash worth {amount} was missing from the {c_box}.",
           "Someone had taken cash worth {amount} from the {c_box}.",
           {"c_box": ("cash drawer", "steel box", "locker")}),
        _t("SB_SHELF", "In the shop, {m_all} the goods on the front shelf were lying on the floor.",
           "I found {m_all} the goods from the front shelf lying on the floor.",
           mods={"m_all": ("all", "some of")}),
        _t("SB_WATCH", "The night watchman told me that he saw {accused} near the shop at midnight.",
           "According to the night watchman, he saw {accused} near the shop at midnight."),
        _t("SB_VAN", "A {c_colour} van bearing number {vehicle} was parked outside the shop that night.",
           "That night, a {c_colour} van with registration number {vehicle} was parked outside the shop.",
           {"c_colour": COLOURS}),
        _t("SB_CAMERA", "The CCTV camera of the shop {n_was} working at that time.",
           "At that time, the CCTV camera of the shop {n_was} working.",
           negs={"n_was": ("was", "was not")}),
    ],
    # ---- Family B scenarios (held out: test_unseen only) ----
    "road_accident": [
        _t("RA_CROSS", "On {date_incident} at about {time_incident}, I was crossing the road near {landmark} on foot.",
           "At around {time_incident} on {date_incident}, I was walking across the road near {landmark}."),
        _t("RA_HIT", "A {c_colour} car bearing number {vehicle} came at high speed and hit me.",
           "A {c_colour} car with registration number {vehicle} came very fast and struck me.",
           {"c_colour": COLOURS}),
        _t("RA_DRIVER", "The car was being driven by {accused}.",
           "The person driving the car was {accused}."),
        _t("RA_INJURY", "I suffered an injury to my {c_body} and was taken to the hospital.",
           "I was hurt on my {c_body} and had to be taken to the hospital.",
           {"c_body": ("leg", "right hand", "shoulder")}),
        _t("RA_STOP", "The driver {n_did} stop to help me.",
           "The driver of the car {n_did} stop to help me.",
           negs={"n_did": ("did", "did not")}),
        _t("RA_COST", "My medical expenses so far are about {amount}.",
           "So far, I have spent about {amount} on treatment."),
        _t("RA_PHONE", "The driver {m_was} talking on a mobile phone at that time.",
           "At that time, the driver {m_was} talking on a mobile phone.",
           mods={"m_was": ("was", "seemed to be")}),
    ],
    "breach_of_trust": [
        _t("BT_GAVE", "On {date_incident} at about {time_incident}, I gave {amount} to {accused} to buy goods for my shop.",
           "At around {time_incident} on {date_incident}, I handed {amount} to {accused} for buying goods for my shop."),
        _t("BT_PROMISE", "He promised to bring the goods within {c_days} days.",
           "He said that he would bring the goods within {c_days} days.",
           {"c_days": ("three", "five", "seven")}),
        _t("BT_KEPT", "He kept the money for himself.",
           "He used the money for himself."),
        _t("BT_RETURN", "When I asked about it, he said that he {m_would} return the money next month.",
           "He told me that he {m_would} return the money next month.",
           mods={"m_would": ("would", "might")}),
        _t("BT_LEFT", "He left the area on a motorcycle bearing number {vehicle}.",
           "He went away from the area on a motorcycle with registration number {vehicle}."),
        _t("BT_EARLIER", "I {n_had} given him money on earlier occasions too.",
           "On earlier occasions too, I {n_had} given him money.",
           negs={"n_had": ("had", "had not")}),
    ],
    "land_intimidation": [
        _t("LI_CAME", "On {date_incident} at about {time_incident}, {accused} came to my field near {landmark}.",
           "At around {time_incident} on {date_incident}, {accused} arrived at my field near {landmark}."),
        _t("LI_CLAIM", "He claimed that the land belonged to his family and told me to leave it.",
           "He said that the land was his family's and asked me to leave it."),
        _t("LI_THREAT", "He threatened that he would harm my {c_rel} if I came to the field again.",
           "He said that he would harm my {c_rel} if I came back to the field.",
           {"c_rel": ("son", "brother", "father")}),
        _t("LI_FENCE", "He damaged {m_all} the fence posts, and the loss is about {amount}.",
           "The loss is about {amount}, as he damaged {m_all} the fence posts.",
           mods={"m_all": ("all", "some of")}),
        _t("LI_TRACTOR", "He came there on a tractor bearing number {vehicle}.",
           "He reached there on a tractor with registration number {vehicle}."),
        _t("LI_RECORDS", "The land records {n_were} checked by the revenue office last year.",
           "Last year, the land records {n_were} checked by the revenue office.",
           negs={"n_were": ("were", "were not")}),
    ],
}

# First-person extra sentences, for long narratives (FIR and statement).
FIRST_EXTRAS: list[Template] = [
    _t("X1_IDENT", "I can identify the accused if I see him again.",
       "I will be able to recognise the accused if I see him again."),
    _t("X1_CCTV", "There is a CCTV camera at a shop near {landmark}, and its footage {m_may} help.",
       "A shop near {landmark} has a CCTV camera, and its footage {m_may} be useful.",
       mods={"m_may": ("may", "will")}),
    _t("X1_WITH", "My {c_rel} {n_was} with me at that time.",
       "At that time, my {c_rel} {n_was} with me.",
       {"c_rel": ("brother", "cousin", "friend")}, {"n_was": ("was", "was not")}),
    _t("X1_NOMONEY", "I have not given any money or property to the accused on any earlier occasion.",
       "I have never given money or property to the accused before."),
    _t("X1_FEAR", "This incident has caused great fear in my family.",
       "My family is very afraid after this incident."),
    _t("X1_REPORT", "I came to the police station as soon as I could to report the matter.",
       "I reached the police station at the earliest to report this matter."),
    _t("X1_KNOWN", "The accused lives in the same locality, and he is known to me.",
       "The accused is known to me, and he lives in the same locality."),
    _t("X1_NOTSEEN", "I have not seen the accused after the incident.",
       "Since the incident, I have not seen the accused."),
    _t("X1_CROWD", "Some people from the locality gathered at the spot after hearing the noise.",
       "After hearing the noise, some local people gathered at the spot."),
    _t("X1_WARN", "I had told the accused earlier to stay away from my family.",
       "Earlier, I had asked the accused to stay away from my family."),
    _t("X1_WORDS", "I am giving this in my own words, and it has been read over to me.",
       "This is in my own words, and it was read over to me."),
    _t("X1_COOP", "I will cooperate fully with the investigation.",
       "I will give full cooperation to the investigation."),
    _t("X1_BUSY", "The incident took place near {landmark}, which is a busy area.",
       "The place where it happened, near {landmark}, is usually busy."),
    _t("X1_LIGHTS", "The street lights in the area {n_were} working that night.",
       "That night, the street lights in the area {n_were} working.",
       negs={"n_were": ("were", "were not")}),
    _t("X1_SAFE", "I request that my identity and address be kept safe.",
       "Please keep my identity and address safe."),
    _t("X1_BEFORE", "I had seen the accused near my house a few days before the incident, on a {c_day}.",
       "A few days before the incident, on a {c_day}, I had seen the accused near my house.",
       {"c_day": ("Monday", "Wednesday", "Friday", "Sunday")}),
    _t("X1_SAW_AGAIN", "I saw {accused} again near {landmark} two days later.",
       "Two days later, I saw {accused} again near {landmark}."),
    _t("X1_LOSS", "The total loss in this matter is about {amount}.",
       "In this matter, the total loss is about {amount}."),
]

# ---- Witness statement (first person, witness) ----------------------------
STM_INTRO = _t("ST_INTRO", "I, {witness}, live in {district} and work as a {c_job}.",
               "My name is {witness}, and I work as a {c_job} in {district}.", {"c_job": JOBS})
STM_CORE: list[Template] = [
    _t("ST_WHERE", "On {date_incident} at about {time_incident}, I was near {landmark}.",
       "At around {time_incident} on {date_incident}, I was present near {landmark}."),
    _t("ST_FACE", "I {n_could} see his face clearly because the area was well lit.",
       "Because the area was well lit, I {n_could} see his face clearly.",
       negs={"n_could": ("could", "could not")}),
    _t("ST_BIKE", "He left on a {c_colour} motorcycle bearing number {vehicle}.",
       "He went away on a {c_colour} motorcycle with registration number {vehicle}.",
       {"c_colour": COLOURS}),
    _t("ST_AMOUNT", "The complainant later told me that property worth {amount} was involved.",
       "Later, the complainant told me that property worth {amount} was involved."),
    _t("ST_KNOW", "I {m_know} {accused} because he lives in the same area.",
       "As he lives in the same area, I {m_know} {accused}.",
       mods={"m_know": ("know", "think I know")}),
]
STM_EVENT: dict[str, Template] = {
    "house_theft": _t("ST_EV_HT", "I saw {accused} standing near the house of the complainant.",
                      "I noticed {accused} standing close to the complainant's house."),
    "vehicle_theft": _t("ST_EV_VT", "I saw {accused} pushing a motorcycle towards the main road.",
                        "I noticed {accused} pushing a motorcycle in the direction of the main road."),
    "assault": _t("ST_EV_AS", "I saw {accused} hitting the complainant with a {c_weapon}.",
                  "I watched {accused} strike the complainant with a {c_weapon}.", {"c_weapon": WEAPONS}),
    "cheating": _t("ST_EV_CH", "I saw {accused} withdrawing cash from the bank counter.",
                   "I noticed {accused} taking out cash at the bank counter."),
    "chain_snatching": _t("ST_EV_CN", "I saw {accused} snatch a chain from the complainant's neck.",
                          "I watched {accused} pull a chain off the complainant's neck."),
    "mobile_theft": _t("ST_EV_MT", "I saw {accused} take a phone out of the complainant's bag.",
                       "I noticed {accused} taking a phone from the complainant's bag."),
    "criminal_trespass": _t("ST_EV_TR", "I saw {accused} climbing into the complainant's compound.",
                            "I noticed {accused} getting into the complainant's compound."),
    "upi_fraud": _t("ST_EV_UF", "I saw {accused} using many bank cards at the cash machine.",
                    "I noticed {accused} using several bank cards at the cash machine."),
    "shop_burglary": _t("ST_EV_SB", "I saw {accused} near the complainant's shop late at night.",
                        "I noticed {accused} close to the complainant's shop late at night."),
    "road_accident": _t("ST_EV_RA", "I saw the car driven by {accused} hit the complainant.",
                        "I watched as the car driven by {accused} struck the complainant."),
    "breach_of_trust": _t("ST_EV_BT", "I was present when the complainant gave money to {accused}.",
                          "When the complainant handed money to {accused}, I was present."),
    "land_intimidation": _t("ST_EV_LI", "I saw {accused} threatening the complainant in the field.",
                            "I watched {accused} threaten the complainant in the field."),
}
STM_CLOSE = _t("ST_CLOSE", "I have given this statement of my own free will.",
               "This statement is given by me of my own free will.")

# ---- Charge sheet brief facts (third person) ------------------------------
CS_OPEN = _t("CS_OPEN", "The complainant {complainant} reported that on {date_incident} an offence took place at {place}.",
             "According to the complainant, {complainant}, an offence took place at {place} on {date_incident}.")
CS_EVENT: dict[str, Template] = {
    "house_theft": _t("CS_EV_HT", "Investigation showed that {accused} broke into the house and took gold ornaments and cash worth {amount}.",
                      "During investigation, it was found that {accused} broke the lock, entered the house and stole gold ornaments and cash worth {amount}."),
    "vehicle_theft": _t("CS_EV_VT", "Investigation showed that {accused} stole the motorcycle bearing number {vehicle}, worth {amount}.",
                        "It was found during investigation that {accused} had stolen the motorcycle, number {vehicle}, valued at {amount}."),
    "assault": _t("CS_EV_AS", "Investigation showed that {accused} attacked the complainant with a {c_weapon} and caused injuries.",
                  "It was found that {accused} assaulted the complainant with a {c_weapon}, causing injuries.", {"c_weapon": WEAPONS}),
    "cheating": _t("CS_EV_CH", "Investigation showed that {amount} was transferred from the complainant's account to an account held by {accused}.",
                   "It was found that {amount} had been moved from the complainant's account into an account of {accused}."),
    "chain_snatching": _t("CS_EV_CN", "Investigation showed that {accused} snatched the gold chain of the complainant, worth {amount}.",
                          "It was found that {accused} had snatched the complainant's gold chain, valued at {amount}."),
    "mobile_theft": _t("CS_EV_MT", "Investigation showed that {accused} stole the mobile phone of the complainant, worth {amount}, in a bus.",
                       "It was found that {accused} had stolen the complainant's mobile phone, valued at {amount}, in a bus."),
    "criminal_trespass": _t("CS_EV_TR", "Investigation showed that {accused} entered the compound of the complainant uninvited and caused damage worth {amount}.",
                            "It was found that {accused} had entered the complainant's compound uninvited, causing damage worth {amount}."),
    "upi_fraud": _t("CS_EV_UF", "Investigation showed that {amount} was taken from the complainant's account through a code sent by {accused}.",
                    "It was found that {amount} had been taken from the complainant's account using a code sent by {accused}."),
    "shop_burglary": _t("CS_EV_SB", "Investigation showed that {accused} broke the shutter lock of the shop and took cash worth {amount}.",
                        "It was found that {accused} had broken the shop's shutter lock and taken cash worth {amount}."),
    "road_accident": _t("CS_EV_RA", "Investigation showed that {accused} drove the car bearing number {vehicle} rashly and hit the complainant.",
                        "It was found that {accused} had driven the car, number {vehicle}, rashly and struck the complainant."),
    "breach_of_trust": _t("CS_EV_BT", "Investigation showed that {accused} kept {amount} that the complainant had given him for buying goods.",
                          "It was found that {accused} had used for himself {amount} given to him by the complainant for buying goods."),
    "land_intimidation": _t("CS_EV_LI", "Investigation showed that {accused} threatened the complainant and damaged his fence, causing a loss of {amount}.",
                            "It was found that {accused} had threatened the complainant and caused a loss of {amount} by damaging his fence."),
}
CS_CORE: list[Template] = [
    _t("CS_IDENT", "The accused was identified by witnesses at the spot.",
       "Witnesses at the spot identified the accused."),
    _t("CS_ADMIT", "The accused {n_did} admit his role during questioning.",
       "During questioning, the accused {n_did} admit his role.",
       negs={"n_did": ("did", "did not")}),
    _t("CS_SEIZE", "A {c_colour} motorcycle bearing number {vehicle} was seized from the accused.",
       "The police seized a {c_colour} motorcycle, number {vehicle}, from the accused.",
       {"c_colour": COLOURS}),
    _t("CS_STMTS", "Statements of {m_all} witnesses were recorded, and the relevant documents were collected.",
       "The statements of {m_all} witnesses were recorded, and the related documents were collected.",
       mods={"m_all": ("all", "some")}),
]
CS_CLOSE = _t("CS_CLOSE", "On the basis of the evidence collected, this charge sheet is submitted against the accused.",
              "Based on the evidence collected, this charge sheet is filed against the accused.")
THIRD_EXTRAS: list[Template] = [
    _t("X3_PLAN", "The site plan of the place of occurrence was prepared.",
       "A site plan of the place of occurrence was made."),
    _t("X3_EXAM", "The complainant was examined, and the statement was recorded.",
       "The complainant was examined, and the statement was taken down."),
    _t("X3_ARREST", "The accused was arrested and produced before the court.",
       "The accused was arrested and then produced before the court."),
    _t("X3_IDPROP", "The seized property {n_was} identified by the complainant.",
       "During investigation, the seized property {n_was} identified by the complainant.",
       negs={"n_was": ("was", "was not")}),
    _t("X3_CCTV", "CCTV footage from a shop near {landmark} was examined.",
       "The CCTV footage from a shop near {landmark} was checked."),
    _t("X3_CALLS", "The call records of the mobile numbers involved were obtained.",
       "Call records of the mobile numbers involved were collected."),
    _t("X3_REPORTS", "The relevant reports were obtained from the concerned offices.",
       "The concerned offices provided the relevant reports."),
    _t("X3_RECORD", "As per available records, the accused has no previous criminal record in {district}.",
       "The accused has no earlier criminal record in {district}, as per available records."),
    _t("X3_TIME", "The investigation was completed within the time allowed.",
       "The investigation was finished within the allowed time."),
    _t("X3_STORE", "The case property is kept safely in the police station store.",
       "The case property is safely kept in the store of the police station."),
    _t("X3_HOUR", "According to the witnesses, the incident took place at about {time_incident}.",
       "The incident happened at about {time_incident}, according to the witnesses."),
    _t("X3_SUPPORT", "The version of the complainant is supported by {m_all} the witnesses.",
       "The complainant's version is supported by {m_all} the witnesses.",
       mods={"m_all": ("all", "some of")}),
    _t("X3_FOUND", "The accused {accused} was found at his house.",
       "{accused} was found at his house by the police."),
]

# Sentences used for an added page (P_PAGE_ADDED) or an added sentence (N_SENTENCE_ADD)
# when the extras pool is used up.
ADDED_POOL: list[Template] = [
    _t("AD_ENQ", "Further enquiries were made in the locality on the next day.",
       "On the next day, more enquiries were made in the locality."),
    _t("AD_PEOPLE", "A few more people were questioned about the incident.",
       "Some more people were asked about the incident."),
    _t("AD_NOISE", "They said that they had heard a loud noise at that time.",
       "They stated that they had heard a loud noise at that time."),
    _t("AD_NOINFO", "No further information was received from them.",
       "They did not give any more information."),
    _t("AD_LOOK", "The matter is being looked into further.",
       "The matter is under further examination."),
    _t("AD_COPY", "A copy of this note is kept with the case papers.",
       "This note is kept, in copy, with the case papers."),
    _t("AD_SHOP", "The owner of a nearby shop also gave some details.",
       "Some details were also given by the owner of a nearby shop."),
    _t("AD_TRACE", "Efforts were made to trace the other persons involved.",
       "Attempts were made to find the other persons involved."),
    _t("AD_AMOUNT", "The loss was later stated again as about {amount}.",
       "Later, the loss was again stated as about {amount}."),
]

# ---- Family B generic templates (held out: test_unseen only, D96) ----------
# Same roles as the family A templates above, written separately so that no
# sentence template is shared between training and the test_unseen split.
FIR_INTRO_B = _t("B_FIR_INTRO", "I, {complainant}, am a resident of the above address, and I am a {c_job} by profession.",
                 "I am {complainant}, a {c_job} by profession, living at the above address.", {"c_job": JOBS})
FIR_CLOSE_B = _t("B_FIR_CLOSE", "I request the police to register my complaint and take action as per law.",
                 "Please register my complaint and take action as per law.")
STM_INTRO_B = _t("B_ST_INTRO", "My name is {witness}; I am a {c_job} and I live in {district}.",
                 "I, {witness}, am a {c_job} living in {district}.", {"c_job": JOBS})
STM_CORE_B: list[Template] = [
    _t("B_ST_WHERE", "On {date_incident} at about {time_incident}, I happened to be close to {landmark}.",
       "At around {time_incident} on {date_incident}, I happened to be near {landmark}."),
    _t("B_ST_FACE", "The light was good, so I {n_could} make out his face.",
       "I {n_could} make out his face, as the light was good.",
       negs={"n_could": ("could", "could not")}),
    _t("B_ST_VEH", "He got away on a {c_colour} vehicle with the number {vehicle}.",
       "He escaped on a {c_colour} vehicle numbered {vehicle}.", {"c_colour": COLOURS}),
    _t("B_ST_LOSS", "I was later told by the complainant that the loss was about {amount}.",
       "The complainant later told me that the loss came to about {amount}."),
    _t("B_ST_KNOW", "I {m_know} {accused} by face, as he stays nearby.",
       "As he stays nearby, I {m_know} {accused} by face.",
       mods={"m_know": ("know", "think I know")}),
]
STM_CLOSE_B = _t("B_ST_CLOSE", "What I have said above is true, and I have said it of my own accord.",
                 "I have said the above of my own accord, and it is true.")
CS_OPEN_B = _t("B_CS_OPEN", "As per the complaint of {complainant}, an incident took place on {date_incident} at {place}.",
               "On {date_incident}, an incident took place at {place}, as per the complaint of {complainant}.")
CS_CORE_B: list[Template] = [
    _t("B_CS_NAMED", "Eyewitnesses named the accused during the inquiry.",
       "During the inquiry, eyewitnesses named the accused."),
    _t("B_CS_CONFESS", "On being questioned, the accused {n_did} confess.",
       "The accused {n_did} confess when he was questioned.",
       negs={"n_did": ("did", "did not")}),
    _t("B_CS_VEH", "A {c_colour} vehicle numbered {vehicle} was taken into police custody.",
       "The police took a {c_colour} vehicle, numbered {vehicle}, into custody.", {"c_colour": COLOURS}),
    _t("B_CS_ACCOUNTS", "The accounts of {m_all} the witnesses were written down, and papers were gathered.",
       "The police wrote down the accounts of {m_all} the witnesses and gathered papers.",
       mods={"m_all": ("all", "some of")}),
]
CS_CLOSE_B = _t("B_CS_CLOSE", "The evidence gathered is enough, and the accused is sent up for trial.",
                "As the evidence gathered is enough, the accused is sent up for trial.")
FIRST_EXTRAS_B: list[Template] = [
    _t("B_X1_IDENT", "I am able to point out the accused if he is shown to me.",
       "If the accused is shown to me, I am able to point him out."),
    _t("B_X1_CAM", "A camera outside a house near {landmark} {m_may} have recorded the incident.",
       "The incident {m_may} have been recorded by a camera outside a house near {landmark}.",
       mods={"m_may": ("may", "must")}),
    _t("B_X1_WITH", "My {c_rel} {n_was} present along with me.",
       "Along with me, my {c_rel} {n_was} present.",
       {"c_rel": ("brother", "cousin", "friend")}, {"n_was": ("was", "was not")}),
    _t("B_X1_QUARREL", "I have had no quarrel with the accused in the past.",
       "In the past, I have had no quarrel with the accused."),
    _t("B_X1_SCARED", "Since that day, my children are scared to go out.",
       "My children are scared to go out since that day."),
    _t("B_X1_FAST", "I came to report the matter without delay.",
       "I reported the matter without any delay."),
    _t("B_X1_NEAR", "The accused stays in the next lane.",
       "The accused lives in the next lane."),
    _t("B_X1_AVOID", "After the incident, the accused has avoided me.",
       "The accused has avoided me after the incident."),
    _t("B_X1_SHOUT", "Hearing my shouts, a few neighbours came out of their houses.",
       "A few neighbours came out of their houses on hearing my shouts."),
    _t("B_X1_WARNED", "I had earlier warned the accused to keep away from my house.",
       "Earlier, I had warned the accused to keep away from my house."),
    _t("B_X1_READ", "The above was read out to me, and it is as I said.",
       "It was read out to me, and it is as I said."),
    _t("B_X1_HELP", "I will help the police in {m_every} way.",
       "I am ready to help the police in {m_every} way.",
       mods={"m_every": ("every", "some")}),
    _t("B_X1_DARK", "It {n_was} dark at that place at the time.",
       "At the time, it {n_was} dark at that place.",
       negs={"n_was": ("was", "was not")}),
    _t("B_X1_NOTICED", "I had noticed the accused near {landmark} on a {c_day} before the incident.",
       "On a {c_day} before the incident, I had noticed the accused near {landmark}.",
       {"c_day": ("Tuesday", "Thursday", "Saturday")}),
    _t("B_X1_AGAIN", "Three days later, I saw {accused} once more near {landmark}.",
       "I saw {accused} once more near {landmark} three days later."),
    _t("B_X1_TOTAL", "The total loss I suffered is about {amount}.",
       "I suffered a total loss of about {amount}."),
]
THIRD_EXTRAS_B: list[Template] = [
    _t("B_X3_SKETCH", "A rough sketch of the spot was drawn.",
       "The spot was shown in a rough sketch."),
    _t("B_X3_RETAKE", "The statement of the complainant was taken again.",
       "The complainant's statement was taken again."),
    _t("B_X3_CUSTODY", "The accused was taken into custody and sent to the court.",
       "The accused was sent to the court after being taken into custody."),
    _t("B_X3_RECOG", "The complainant {n_did} recognise the recovered articles.",
       "On seeing the recovered articles, the complainant {n_did} recognise them.",
       negs={"n_did": ("did", "did not")}),
    _t("B_X3_CAM", "Camera recordings from near {landmark} were collected and seen.",
       "Recordings from cameras near {landmark} were collected and seen."),
    _t("B_X3_PHONES", "Details of the phone numbers used were collected from the service provider.",
       "The service provider gave details of the phone numbers used."),
    _t("B_X3_PAPERS", "Papers from the offices concerned were collected.",
       "The offices concerned sent the required papers."),
    _t("B_X3_PAST", "As per police records, the accused has no earlier case in {district}.",
       "The accused has no earlier case in {district}, as per police records."),
    _t("B_X3_DONE", "The inquiry was finished within the time fixed by law.",
       "Within the time fixed by law, the inquiry was finished."),
    _t("B_X3_KEPT", "The recovered articles are kept safely in the police station.",
       "In the police station, the recovered articles are kept safely."),
    _t("B_X3_TIME", "The witnesses said the incident happened at about {time_incident}.",
       "As per the witnesses, the incident happened at about {time_incident}."),
    _t("B_X3_BACK", "The account of the complainant is backed by {m_all} the witnesses.",
       "The complainant's account is backed by {m_all} the witnesses.",
       mods={"m_all": ("all", "some of")}),
    _t("B_X3_TRACED", "{accused} was traced to a relative's house.",
       "The police traced {accused} to a relative's house."),
]
ADDED_POOL_B: list[Template] = [
    _t("B_AD_INQ", "More inquiries were made in the area on the following day.",
       "On the following day, more inquiries were made in the area."),
    _t("B_AD_PERSONS", "Some more persons were spoken to about the incident.",
       "A few more persons were spoken to about the incident."),
    _t("B_AD_SHOUT", "They stated that they had heard shouting at that time.",
       "They said that they had heard shouting at that time."),
    _t("B_AD_NOMORE", "They had no more details to give.",
       "They could give no more details."),
    _t("B_AD_ON", "Further inquiry in the matter is going on.",
       "The matter is still under inquiry."),
    _t("B_AD_FILE", "A copy of this report is placed in the case file.",
       "This report is placed, in copy, in the case file."),
    _t("B_AD_TEA", "A tea seller nearby also shared some details.",
       "Some details were also shared by a tea seller nearby."),
    _t("B_AD_OTHERS", "Efforts are on to find the others involved.",
       "Efforts are being made to find the others involved."),
    _t("B_AD_AMOUNT", "The loss was again put at about {amount}.",
       "Later, the loss was again put at about {amount}."),
]

# Scenarios of family B appear only in the test_unseen split.
FAMILY_B_SCENARIOS: tuple[str, ...] = ("road_accident", "breach_of_trust", "land_intimidation")


def family_of(scenario: str) -> str:
    return "B" if scenario in FAMILY_B_SCENARIOS else "A"


GENERIC: dict[str, dict[str, Any]] = {
    "A": {"fir_intro": FIR_INTRO, "fir_close": FIR_CLOSE, "stm_intro": STM_INTRO, "stm_core": STM_CORE,
          "stm_close": STM_CLOSE, "cs_open": CS_OPEN, "cs_core": CS_CORE, "cs_close": CS_CLOSE,
          "first_extras": FIRST_EXTRAS, "third_extras": THIRD_EXTRAS, "added": ADDED_POOL},
    "B": {"fir_intro": FIR_INTRO_B, "fir_close": FIR_CLOSE_B, "stm_intro": STM_INTRO_B, "stm_core": STM_CORE_B,
          "stm_close": STM_CLOSE_B, "cs_open": CS_OPEN_B, "cs_core": CS_CORE_B, "cs_close": CS_CLOSE_B,
          "first_extras": FIRST_EXTRAS_B, "third_extras": THIRD_EXTRAS_B, "added": ADDED_POOL_B},
}

ALL_TEMPLATES: dict[str, Template] = {}
for _tpl in ([FIR_INTRO, FIR_CLOSE, STM_INTRO, STM_CLOSE, CS_OPEN, CS_CLOSE]
             + [t for ts in FIR_CORE.values() for t in ts] + FIRST_EXTRAS + STM_CORE
             + list(STM_EVENT.values()) + list(CS_EVENT.values()) + CS_CORE + THIRD_EXTRAS + ADDED_POOL
             + [FIR_INTRO_B, FIR_CLOSE_B, STM_INTRO_B, STM_CLOSE_B, CS_OPEN_B, CS_CLOSE_B]
             + STM_CORE_B + CS_CORE_B + FIRST_EXTRAS_B + THIRD_EXTRAS_B + ADDED_POOL_B):
    if _tpl.tid in ALL_TEMPLATES:
        raise ValueError(f"duplicate template id {_tpl.tid}")
    ALL_TEMPLATES[_tpl.tid] = _tpl


def slots_of(tpl: Template, phrasing: int) -> list[str]:
    import string
    return [f for _, f, _, _ in string.Formatter().parse(tpl.phrasings[phrasing]) if f]


def make_sentence(tpl: Template, case: dict[str, Any], rng: random.Random) -> Sentence:
    """Fill a template from case facts. Choice and negation slots are picked at random."""
    slots = sorted(set(slots_of(tpl, 0)) | set(slots_of(tpl, 1)))
    values: list[tuple[str, Any]] = []
    for s in slots:
        if s in tpl.choices:
            values.append((s, rng.choice(tpl.choices[s])))
        elif s in tpl.negs:
            values.append((s, tpl.negs[s][0]))  # base documents use the positive form
        elif s in tpl.mods:
            values.append((s, tpl.mods[s][0]))  # base documents use the base modal form
        else:
            values.append((s, case[s]))
    return Sentence(tpl.tid, rng.randint(0, 1), tuple(values))


def render_sentence(s: Sentence, style: Style) -> str:
    tpl = ALL_TEMPLATES[s.template_id]
    vals: dict[str, str] = {}
    for k, v in s.values:
        if k == "date_incident":
            vals[k] = fmt_date(v, style)
        elif k == "time_incident":
            vals[k] = fmt_time(v, style)
        elif k == "amount":
            vals[k] = fmt_amount(v, style)
        elif k == "vehicle":
            vals[k] = fmt_vehicle(v, style)
        else:
            vals[k] = str(v)
    text = tpl.phrasings[s.phrasing].format(**vals)
    if s.punct_edit:
        text = text.replace(",", "", 1)
    return text


def build_narrative(doc_type: str, scenario: str, case: dict[str, Any], rng: random.Random,
                    long: bool) -> tuple[Sentence, ...]:
    """Build the narrative for one document. Long narratives add extra sentences.

    The generic sentences come from the scenario's template family (A or B).
    """
    g = GENERIC[family_of(scenario)]
    if doc_type == "FIR":
        core = [g["fir_intro"]] + list(FIR_CORE[scenario])
        if not long:
            # Short narratives keep the intro and drop one or two middle sentences.
            drop = rng.sample(range(2, len(core)), k=rng.randint(1, 2))
            core = [t for i, t in enumerate(core) if i not in drop]
        body = core
        extras = g["first_extras"]
        close = g["fir_close"]
    elif doc_type == "STATEMENT":
        core = [g["stm_intro"], g["stm_core"][0], STM_EVENT[scenario]] + g["stm_core"][1:]
        if not long:
            drop = rng.sample(range(3, len(core)), k=rng.randint(1, 2))
            core = [t for i, t in enumerate(core) if i not in drop]
        body = core
        extras = g["first_extras"]
        close = g["stm_close"]
    else:
        core = [g["cs_open"], CS_EVENT[scenario]] + g["cs_core"]
        if not long:
            drop = rng.sample(range(2, len(core)), k=1)
            core = [t for i, t in enumerate(core) if i not in drop]
        body = core
        extras = g["third_extras"]
        close = g["cs_close"]
    if long:
        n_extra = rng.randint(9, min(13, len(extras)))
        picked = rng.sample(extras, k=n_extra)
        # Keep core order; place extras after the core, in random order.
        body = body + picked
    sentences = [make_sentence(t, case, rng) for t in body + [close]]
    return tuple(sentences)


def template_has_entity(tpl: Template) -> bool:
    return any(slot in ENTITY_SLOTS for i in (0, 1) for slot in slots_of(tpl, i))


def sentence_entities(s: Sentence) -> tuple[tuple[str, Any], ...]:
    """The narrative entities of a sentence, as (slot, value) pairs (D45)."""
    return tuple((k, v) for k, v in s.values if k in ENTITY_SLOTS)


def sentence_negations(s: Sentence) -> tuple[tuple[str, Any], ...]:
    """The negation slots of a sentence and their current form."""
    negs = ALL_TEMPLATES[s.template_id].negs
    return tuple((k, v) for k, v in s.values if k in negs)


def sentence_modals(s: Sentence) -> tuple[tuple[str, Any], ...]:
    """The modal or quantifier slots of a sentence and their current form."""
    mods = ALL_TEMPLATES[s.template_id].mods
    return tuple((k, v) for k, v in s.values if k in mods)


def unused_templates(doc_type: str, used: set[str], with_entity: bool | None = None,
                     family: str = "A") -> list[Template]:
    """Templates of the document's family not yet in it, optionally only those with (or without) entities."""
    g = GENERIC[family]
    pool = g["third_extras"] if doc_type == "CHARGESHEET" else g["first_extras"]
    out = [t for t in pool if t.tid not in used]
    out += [t for t in g["added"] if t.tid not in used]
    if with_entity is not None:
        out = [t for t in out if template_has_entity(t) == with_entity]
    return out
