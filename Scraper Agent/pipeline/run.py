from pipeline.normalize import normalize
from pipeline.model_search import discover_official_urls
from pipeline.fetch import fetch_with_cache
from pipeline.parse import parse_doc
from pipeline.extract import extract_from_page
from pipeline.resolve import cluster_people
from pipeline.export import export
from pipeline.report import report

def run(jur_input:str):
    jur = normalize(jur_input)
    print(f"[normalize] {jur.name} ({jur.level})")
    urls = discover_official_urls(jur.name)
    print(f"[model-search] {len(urls)} candidate URLs")
    fetched = [fetch_with_cache(u) for u in urls]
    print(f"[fetch] {len(fetched)} pages")
    pages = [parse_doc(r) for r in fetched]
    print(f"[parse] {len(pages)} parsed")
    all_people=[]
    for p in pages:
        all_people += extract_from_page(p, jur.name)
    print(f"[extract] raw people: {len(all_people)}")
    merged = cluster_people(all_people, threshold=90)
    print(f"[resolve] unique people: {len(merged)}")
    csv = export(jur.name, merged)
    rpt = report(csv)
    print(f"[export] {csv}")
    print(f"[report] {rpt}")

if __name__=="__main__":
    import sys
    run(" ".join(sys.argv[1:]) or "Austin City Council")
