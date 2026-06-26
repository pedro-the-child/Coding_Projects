from dataclasses import dataclass
import csv, re

@dataclass
class Jurisdiction:
    input_str: str
    name: str
    level: str
    country: str
    region: str
    aliases: list[str]

def load_aliases(path="configs/aliases.csv"):
    rows=[]
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            r["aliases"] = [a.strip() for a in (r["aliases"] or "").split("|") if a.strip()]
            rows.append(r)
    return rows

def normalize(input_str:str)->Jurisdiction:
    for r in load_aliases():
        all_terms = {r["normalized_name"].lower(), *[a.lower() for a in r["aliases"]]}
        if input_str.lower() in all_terms or any(a in input_str.lower() for a in all_terms):
            return Jurisdiction(input_str, r["normalized_name"], r["level"], r["country"], r["region"], r["aliases"])
    cleaned = re.sub(r'\bcouncil\b','',input_str, flags=re.I).strip()
    name = f"{cleaned} Council"
    return Jurisdiction(input_str, name, "city", "US", "", [name])
