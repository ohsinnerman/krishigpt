#!/usr/bin/env python3
"""
Cross-platform corpus + pincode downloader for KrishiGPT.

Strategy (resilient for a time-boxed build):
  1. Try to download real agricultural HTML pages (TNAU Agritech etc.).
  2. ALWAYS write a curated seed corpus of state-tagged docs so the demo
     works even if every network download fails.
  3. Try to download a pincode CSV; if it fails, the prefix fallback in
     pincode_mapper.py still resolves every pincode.

Usage: python scripts/download_corpus.py
"""
import os
from pathlib import Path

try:
    import httpx
except ImportError:
    httpx = None

ROOT = Path(__file__).parent.parent
CORPUS = ROOT / "backend" / "data" / "corpus"
PINCODE_CSV = ROOT / "backend" / "data" / "pincodes.csv"

CORPUS.mkdir(parents=True, exist_ok=True)

# Real sources to attempt (best-effort; failures are fine).
TNAU = "https://agritech.tnau.ac.in"
WEB_SOURCES = {
    "paddy_tnau_en.html": f"{TNAU}/agriculture/agri_cereals_paddy.html",
    "wheat_tnau_en.html": f"{TNAU}/agriculture/agri_cereals_wheat.html",
    "groundnut_tnau_en.html": f"{TNAU}/agriculture/agri_oilseeds_groundnut.html",
    "tomato_tnau_en.html": f"{TNAU}/horticulture/horti_vegetables_tomato.html",
    "sugarcane_tnau_en.html": f"{TNAU}/agriculture/agri_sugarcrops_sugarcane.html",
}

PINCODE_SOURCES = [
    "https://raw.githubusercontent.com/sanand0/pincode/master/pincode.csv",
    "https://raw.githubusercontent.com/datameet/Pincode/master/all_india_PO.csv",
]


def try_download(url: str, dest: Path) -> bool:
    if httpx is None:
        return False
    try:
        with httpx.Client(timeout=20, follow_redirects=True, verify=False) as client:
            r = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200 and len(r.content) > 500:
                dest.write_bytes(r.content)
                print(f"  OK   {dest.name}  ({len(r.content)} bytes)")
                return True
            print(f"  FAIL {dest.name}  (HTTP {r.status_code})")
    except Exception as e:
        print(f"  FAIL {dest.name}  ({type(e).__name__})")
    return False


def download_web_corpus():
    print("Downloading web corpus (best-effort)...")
    for name, url in WEB_SOURCES.items():
        try_download(url, CORPUS / name)


def write_seed_corpus():
    """Guaranteed curated docs so the demo always has region-tagged content.
    Filenames embed the state so the ingestion state-tagger picks them up."""
    print("Writing curated seed corpus...")
    for name, body in SEED_DOCS.items():
        (CORPUS / name).write_text(body, encoding="utf-8")
        print(f"  seed {name}")


def download_pincodes():
    print("Downloading pincode CSV (best-effort)...")
    for url in PINCODE_SOURCES:
        if try_download(url, PINCODE_CSV):
            return
    print("  No pincode CSV — prefix fallback in pincode_mapper.py will be used.")


# ── Curated seed documents (concise, realistic, state-tagged via filename) ──────
# These mirror ICAR Package-of-Practices style content. They are intentionally
# specific so retrieval + region boosting are demonstrable.

SEED_DOCS = {
"paddy_karnataka_pop.txt": """Paddy (Rice) Package of Practices - Karnataka
Stem borer is a major pest of paddy in Karnataka. Symptoms: dead hearts in vegetative stage and white ears at flowering. Management: apply Cartap hydrochloride 4G at 25 kg/ha or Chlorantraniliprole 0.4G at 10 kg/ha in standing water. Drain the field before application. Cultural control: remove and destroy egg masses, avoid excess nitrogen, and use light traps to monitor moth activity.
Recommended varieties for Karnataka: Jyothi, IR-64, BR-2655, Tunga, and Thanu for irrigated conditions.
Fertilizer schedule (irrigated paddy): apply 100 kg N, 50 kg P2O5 and 50 kg K2O per hectare. Apply nitrogen in three splits - basal, tillering and panicle initiation. Apply full phosphorus as basal dose.
Irrigation: maintain 5 cm standing water during active tillering. Drain water 10 days before harvest.
""",
"wheat_punjab_pop.txt": """Wheat Package of Practices - Punjab
Wheat is the main rabi crop of Punjab. Recommended varieties: HD-3086, PBW-725, WH-1105 and DBW-187 for timely sown irrigated conditions.
Fertilizer dose for wheat in Punjab: apply 120 kg N, 60 kg P2O5 and 30 kg K2O per hectare. Apply half nitrogen and full phosphorus and potash as basal at sowing. Apply remaining nitrogen as Urea topdressing at first irrigation (21 days after sowing) and second irrigation.
Urea dose: approximately 110 kg Urea per acre split across basal and two topdressings. Yellow rust is the major disease - spray Propiconazole 25 EC at 0.1 percent if pustules appear.
Sowing time: first fortnight of November. Seed rate: 100 kg per hectare. Irrigation at crown root initiation stage (21 days) is most critical.
""",
"cotton_gujarat_pop.txt": """Cotton Package of Practices - Gujarat
Cotton is a major cash crop of Gujarat. Whitefly and pink bollworm are key pests. For pink bollworm install pheromone traps at 5 per hectare and spray Profenophos 50 EC at 2 ml per litre when ETL is crossed.
Recommended Bt cotton hybrids suited to Gujarat: G.Cot.Hy-8, and approved Bt hybrids for the region.
Fertilizer: apply 240 kg N, 60 kg P2O5 and 0 kg K2O per hectare for irrigated Bt cotton, in splits. Apply nitrogen in 4 splits up to flowering.
Spacing: 120 x 45 cm for Bt cotton. Avoid waterlogging. Practice crop rotation with pulses to reduce wilt incidence.
""",
"sugarcane_maharashtra_pop.txt": """Sugarcane Package of Practices - Maharashtra
Sugarcane is widely grown in the Deccan region of Maharashtra. Recommended varieties: Co-86032, CoM-0265 and Co-92005.
Fertilizer: apply 250 kg N, 115 kg P2O5 and 115 kg K2O per hectare. Apply nitrogen in splits at planting, tillering and grand growth phase.
Early shoot borer is a serious pest. Apply Chlorantraniliprole or Cartap granules and practice trash mulching. Maintain proper drainage in heavy soils to prevent root rot.
Irrigation: critical stages are germination, tillering and grand growth. Adopt drip irrigation to save water in water-scarce Maharashtra.
""",
"groundnut_andhra_pop.txt": """Groundnut Package of Practices - Andhra Pradesh
Groundnut is the principal oilseed of Andhra Pradesh. Recommended varieties: K-6, Dharani, Kadiri-9 and TMV-2.
Tikka leaf spot and rust are major diseases. Spray Chlorothalonil or Mancozeb at 2.5 g per litre at first appearance and repeat after 15 days.
Fertilizer: apply 20 kg N, 40 kg P2O5 and 50 kg K2O per hectare. Apply gypsum at 500 kg per hectare at pegging stage for better pod filling.
Sowing: kharif - June to July with onset of monsoon. Seed rate 100-125 kg kernels per hectare. Ensure calcium availability at pegging for good kernel development.
""",
"pmfby_scheme_india.txt": """Pradhan Mantri Fasal Bima Yojana (PMFBY) - Crop Insurance Scheme
PMFBY provides crop insurance against yield loss due to natural calamities, pests and diseases. It is a pan-India government scheme.
Eligibility: all farmers including sharecroppers and tenant farmers growing notified crops in notified areas are eligible. Enrollment is voluntary.
Premium: farmers pay 2 percent of sum insured for kharif crops, 1.5 percent for rabi crops, and 5 percent for commercial and horticultural crops. The balance premium is shared by central and state governments.
Documents needed: Aadhaar card, bank account details, land records (khasra/khatauni) or tenancy agreement, and sowing certificate. Apply at the nearest bank, Common Service Centre (CSC), or through the PMFBY portal before the cutoff date notified for each season.
""",
"pmkisan_scheme_india.txt": """Pradhan Mantri Kisan Samman Nidhi (PMKISAN) - Income Support Scheme
PMKISAN is a pan-India central scheme providing income support of Rs 6000 per year to eligible farmer families, paid in three equal installments of Rs 2000 every four months directly into bank accounts.
Eligibility: all landholding farmer families with cultivable land are eligible. Excluded: institutional landholders, income tax payers, government employees and pensioners drawing high pensions.
Documents needed: Aadhaar card, bank account details and land ownership records. Register at the PMKISAN portal or through the local revenue officer / village accountant. Beneficiary status can be checked online on the PMKISAN portal using Aadhaar or account number.
""",
"kcc_scheme_india.txt": """Kisan Credit Card (KCC) - Agricultural Credit Scheme
The Kisan Credit Card provides farmers timely and affordable credit for crop cultivation and allied activities. It is available across India through commercial banks, cooperative banks and regional rural banks.
Eligibility: all farmers - individual or joint cultivators, tenant farmers, sharecroppers, and self-help groups are eligible. Credit limit is based on cropping pattern and scale of finance.
Interest: short-term crop loans up to Rs 3 lakh carry an effective interest of 4 percent per annum with prompt repayment incentive and interest subvention.
Documents needed: identity proof (Aadhaar), address proof, and land records. Apply at any bank branch with the prescribed form. KCC is valid for 5 years subject to annual review.
""",
}


if __name__ == "__main__":
    download_web_corpus()
    write_seed_corpus()
    download_pincodes()
    print("\nDone. Next: python scripts/build_index.py")
