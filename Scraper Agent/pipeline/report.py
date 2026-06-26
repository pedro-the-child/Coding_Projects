import pandas as pd
from pathlib import Path

def report(csv_path:str):
    df = pd.read_csv(csv_path)
    found = df["person_id"].nunique() if len(df) else 0
    pct_email = (df["email_primary"].notnull().mean()*100) if len(df) else 0
    pct_phone = (df["phone_primary"].notnull().mean()*100) if len(df) else 0
    rep = pd.DataFrame([{
        "jurisdiction": df["jurisdiction"].iloc[0] if len(df) else "",
        "found_members": int(found),
        "pct_email": round(pct_email,1),
        "pct_phone": round(pct_phone,1),
    }])
    out = Path("data/reports")/ (Path(csv_path).stem + "_report.csv")
    rep.to_csv(out, index=False)
    return str(out)
