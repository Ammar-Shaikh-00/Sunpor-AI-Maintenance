import httpx

BASE_URL = "http://100.93.158.60:8000"
with httpx.Client(timeout=30.0) as client:
    login = client.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@sunpor.local", "password": "Admin@123456"},
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ts = client.get(f"{BASE_URL}/signal-timeseries/latest", headers=headers)
    ts.raise_for_status()
    rows = ts.json()

out_of_range = [r for r in rows if r["quality"].upper() != "GOOD"]

print(f"Total signals: {len(rows)}")
print(f"Non-GOOD quality: {len(out_of_range)}")
print()
for r in out_of_range:
    print(
        f"  signal_id={r['signal_id']} | tag={r['wincc_tag']} "
        f"| quality={r['quality']} "
        f"| value_raw={r['value_raw']} "
        f"| value_scaled={r['value_scaled']}"
    )
