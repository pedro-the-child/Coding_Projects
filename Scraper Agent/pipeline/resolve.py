from rapidfuzz import fuzz
from collections import defaultdict
import uuid

def _norm(n): return " ".join((n or "").split()).lower()  # Normalize names: strip whitespace, lowercase

def cluster_people(people:list[dict], threshold=90):  # Group similar people using fuzzy matching
    clusters=[]; used=[False]*len(people)  # Track which people are already clustered
    for i,p in enumerate(people):  # For each person
        if used[i]: continue  # Skip if already clustered
        group=[i]; used[i]=True  # Start new cluster with this person
        for j,q in enumerate(people):  # Compare with all other people
            if used[j]: continue  # Skip if already clustered
            if fuzz.token_set_ratio(_norm(p.get("full_name","")), _norm(q.get("full_name","")))>=threshold:  # Check name similarity
                group.append(j); used[j]=True  # Add to cluster if similar enough
        clusters.append(group)  # Save this cluster
    merged=[]  # Final deduplicated people
    for g in clusters:  # For each cluster
        base=people[g[0]].copy()  # Use first person as base
        base["person_id"]=str(uuid.uuid4())  # Generate unique ID
        emails=set(); phones=set(); sources=set()  # Collect all contact info
        for idx in g:  # For each person in cluster
            emails.update(people[idx].get("emails",[]))  # Merge emails
            phones.update(people[idx].get("phones",[]))  # Merge phones
            sources.add(people[idx].get("source_url"))  # Track sources
        base["emails"]=sorted(emails); base["phones"]=sorted(phones)  # Convert sets to sorted lists
        base["sources"]=sorted(sources)  # Track all source URLs
        merged.append(base)  # Add to final results
    return merged
