import pandas as pd
from pathlib import Path

def export(jur_name:str, people:list[dict]):
    rows=[]
    for p in people:
        rows.append({
            "jurisdiction": jur_name,
            "body_name": p.get("body_name"),
            "person_id": p["person_id"],
            "full_name": p.get("full_name"),
            "role_title": p.get("role_title"),
            "chamber": p.get("chamber"),
            "district": p.get("district"),
            "party": p.get("party"),
            "email_primary": (p["emails"][0] if p.get("emails") else None),
            "phone_primary": (p["phones"][0] if p.get("phones") else None),
            "source_count": len(p.get("sources",[]))
        })
    out = Path("data/outputs"); out.mkdir(parents=True, exist_ok=True)
    csv_path = out / f"{jur_name.replace(' ','_').lower()}.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    return str(csv_path)
