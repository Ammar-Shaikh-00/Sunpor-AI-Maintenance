import httpx

ML = "http://127.0.0.1:8001"

# Get cleaning report
report = httpx.get(f"{ML}/ingestion/cleaning-report").json()
print("=== CLEANING REPORT ===")
print(f"total_received:    {report['total_received']}")
print(f"total_valid:       {report['total_valid']}")
print(f"total_invalid:     {report['total_invalid']}")
print(f"quality_counts:    {report['quality_counts']}")
print(f"duplicate_dropped: {report['duplicate_dropped']}")

# Get full feature vector to see bad_quality_ratio per group
fv = httpx.get(f"{ML}/features/process_state").json()
print()
print("=== BAD QUALITY RATIO PER GROUP (5min window) ===")
windows = fv.get("windows", {})
w5 = windows.get("5min", {})
sfs = w5.get("signal_features", {})
for sid, sf in sfs.items():
    if sf.get("has_bad_quality"):
        print(
            f"  signal_id={sid} | group={sf.get('signal_group')} "
            f"| last_val={sf.get('last_val')} "
            f"| has_bad_quality=True"
        )
