import os
import csv
from functools import lru_cache
from typing import Optional

# Agro-climatic zone by state
AGRO_ZONES = {
    "Punjab": "IGP-Northwest", "Haryana": "IGP-Northwest",
    "Delhi": "IGP-Northwest", "Chandigarh": "IGP-Northwest",
    "Himachal Pradesh": "Western Himalaya",
    "Jammu and Kashmir": "Western Himalaya", "Ladakh": "Western Himalaya",
    "Uttarakhand": "Western Himalaya",
    "Uttar Pradesh": "IGP-Central",
    "Bihar": "IGP-East",
    "West Bengal": "Eastern", "Odisha": "Eastern",
    "Jharkhand": "Eastern", "Chhattisgarh": "Eastern",
    "Assam": "Northeast", "Meghalaya": "Northeast", "Manipur": "Northeast",
    "Nagaland": "Northeast", "Arunachal Pradesh": "Northeast",
    "Mizoram": "Northeast", "Tripura": "Northeast", "Sikkim": "Northeast",
    "Madhya Pradesh": "Central",
    "Maharashtra": "Deccan", "Goa": "South-Coastal",
    "Gujarat": "Arid-Semi", "Dadra and Nagar Haveli": "Arid-Semi",
    "Rajasthan": "Arid",
    "Karnataka": "Deccan-South",
    "Andhra Pradesh": "Deccan-South", "Telangana": "Deccan-South",
    "Tamil Nadu": "South", "Puducherry": "South",
    "Kerala": "South-Coastal", "Lakshadweep": "South-Coastal",
    "Andaman and Nicobar Islands": "Island",
}

# Fallback mapping: first 2 digits of pincode -> approximate state
PINCODE_PREFIX_STATE = {
    "11": "Delhi", "12": "Haryana", "13": "Haryana", "14": "Punjab",
    "15": "Punjab", "16": "Punjab", "17": "Himachal Pradesh",
    "18": "Jammu and Kashmir", "19": "Jammu and Kashmir",
    "20": "Uttar Pradesh", "21": "Uttar Pradesh", "22": "Uttar Pradesh",
    "23": "Uttar Pradesh", "24": "Uttar Pradesh", "25": "Uttar Pradesh",
    "26": "Uttar Pradesh", "27": "Uttar Pradesh", "28": "Uttar Pradesh",
    "30": "Rajasthan", "31": "Rajasthan", "32": "Rajasthan",
    "33": "Rajasthan", "34": "Rajasthan",
    "36": "Gujarat", "37": "Gujarat", "38": "Gujarat", "39": "Gujarat",
    "40": "Maharashtra", "41": "Maharashtra", "42": "Maharashtra",
    "43": "Maharashtra", "44": "Maharashtra",
    "45": "Madhya Pradesh", "46": "Madhya Pradesh", "47": "Madhya Pradesh",
    "48": "Madhya Pradesh", "49": "Chhattisgarh",
    "50": "Telangana", "51": "Andhra Pradesh", "52": "Andhra Pradesh",
    "53": "Andhra Pradesh",
    "56": "Karnataka", "57": "Karnataka", "58": "Karnataka", "59": "Karnataka",
    "60": "Tamil Nadu", "61": "Tamil Nadu", "62": "Tamil Nadu",
    "63": "Tamil Nadu", "64": "Tamil Nadu",
    "67": "Kerala", "68": "Kerala", "69": "Kerala",
    "70": "West Bengal", "71": "West Bengal", "72": "West Bengal",
    "73": "West Bengal",
    "74": "West Bengal", "75": "Odisha", "76": "Odisha", "77": "Odisha",
    "78": "Assam", "79": "Assam",
    "80": "Bihar", "81": "Bihar", "82": "Bihar", "83": "Bihar", "84": "Bihar",
    "85": "Jharkhand",
}

_pincode_db: dict = {}
_loaded = False


def _load_pincode_db():
    global _pincode_db, _loaded
    if _loaded:
        return
    csv_path = os.getenv("PINCODE_DB_PATH", "data/pincodes.csv")
    if not os.path.exists(csv_path):
        print(f"WARNING: {csv_path} not found. Using prefix-only fallback.")
        _loaded = True
        return
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pin = (row.get("pincode") or row.get("Pincode") or "").strip()
            if pin:
                _pincode_db[pin] = {
                    "district": (row.get("districtname") or row.get("District") or "Unknown").strip(),
                    "state": (row.get("statename") or row.get("State") or "Unknown").strip(),
                    "division": (row.get("divisionname") or row.get("Division") or "").strip(),
                }
    print(f"Loaded {len(_pincode_db)} pincodes from {csv_path}")
    _loaded = True


@lru_cache(maxsize=10000)
def get_region_from_pincode(pincode: str) -> Optional[dict]:
    _load_pincode_db()

    pincode = pincode.strip()
    if not pincode.isdigit() or len(pincode) != 6:
        return None

    # Exact match
    if pincode in _pincode_db:
        info = _pincode_db[pincode]
        state = info["state"]
        return {
            "pincode": pincode,
            "district": info["district"],
            "state": state,
            "agro_zone": AGRO_ZONES.get(state, "Unknown"),
            "division": info.get("division", ""),
        }

    # Prefix fallback
    prefix = pincode[:2]
    state = PINCODE_PREFIX_STATE.get(prefix)
    if state:
        return {
            "pincode": pincode,
            "district": "Unknown",
            "state": state,
            "agro_zone": AGRO_ZONES.get(state, "Unknown"),
            "division": "",
        }

    return None
