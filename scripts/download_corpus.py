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

# ── SOUTH ───────────────────────────────────────────────────────────────────
"paddy_tamilnadu_pop.txt": """Paddy (Rice) Package of Practices - Tamil Nadu
Rice is the staple crop of Tamil Nadu, grown in Kuruvai, Samba and Thaladi seasons. Recommended varieties: ADT-43, ADT-45, CO-51 and TKM-13 for irrigated conditions.
Stem borer and brown planthopper (BPH) are the major pests. For BPH spray Imidacloprid 17.8 SL at 125 ml/ha and avoid excessive nitrogen. For stem borer apply Cartap hydrochloride 4G at 25 kg/ha.
Fertilizer: apply 150 kg N, 50 kg P2O5 and 50 kg K2O per hectare for irrigated rice. Apply nitrogen in three to four splits. Apply full phosphorus as basal.
Irrigation: maintain thin film of water; adopt alternate wetting and drying to save water. Recommended for Cauvery delta region.
""",
"groundnut_tamilnadu_pop.txt": """Groundnut Package of Practices - Tamil Nadu
Groundnut is a major oilseed in Tamil Nadu. Recommended varieties: TMV-7, VRI-2, CO-7 and the bunch type spreading varieties.
Leaf miner and red hairy caterpillar are key pests. Tikka leaf spot is managed by spraying Mancozeb at 2 g per litre.
Fertilizer: apply 25 kg N, 50 kg P2O5 and 75 kg K2O per hectare. Apply gypsum at 500 kg/ha at flowering for better pod and kernel development. Ensure adequate calcium at pegging.
Sowing: rainfed kharif and irrigated rabi. Seed rate 125 kg/ha for bunch varieties.
""",
"cotton_telangana_pop.txt": """Cotton Package of Practices - Telangana
Cotton is the principal commercial crop of Telangana, largely Bt cotton. Pink bollworm and sucking pests (jassids, whitefly) are major threats.
For pink bollworm install pheromone traps at 8 per hectare, monitor and spray Emamectin benzoate 5 SG at 0.4 g per litre when ETL is crossed. Avoid extending the crop beyond December to break the pest cycle.
Fertilizer: apply 120 kg N, 60 kg P2O5 and 60 kg K2O per hectare for irrigated Bt cotton in splits up to flowering.
Spacing: 90 x 60 cm. Practice rotation and timely termination of the crop.
""",
"chilli_andhra_pop.txt": """Chilli Package of Practices - Andhra Pradesh
Andhra Pradesh is the largest chilli producing state, especially the Guntur region. Recommended varieties: LCA-334, LCA-625 and Teja for high pungency.
Thrips, mites and fruit borer are key pests; leaf curl (viral, vectored by thrips) is the major problem. Spray Fipronil 5 SC at 2 ml per litre for thrips and remove infected plants.
Fertilizer: apply 150 kg N, 60 kg P2O5 and 100 kg K2O per hectare in splits. Apply micronutrients if deficiency symptoms appear.
Irrigation: drip irrigation with mulching gives best results in Guntur black soils.
""",
"coconut_kerala_pop.txt": """Coconut Package of Practices - Kerala
Coconut is the most important plantation crop of Kerala. Recommended varieties: West Coast Tall, Chowghat Orange Dwarf and hybrids like Kerasankara.
Rhinoceros beetle and red palm weevil are major pests. For rhinoceros beetle apply naphthalene balls or treat the topmost leaf axils; set up pheromone traps for red palm weevil.
Root wilt is a serious disease in Kerala; remove and burn severely affected palms and apply balanced nutrition.
Fertilizer: apply 500 g N, 320 g P2O5 and 1200 g K2O per palm per year in two splits with the monsoon. Apply organic manure and Magnesium for healthy palms.
""",
"rubber_kerala_pop.txt": """Rubber Package of Practices - Kerala
Natural rubber is a key plantation crop of Kerala's humid zone. Recommended clones: RRII-105, RRII-414 and RRII-430.
Abnormal leaf fall (Phytophthora) and powdery mildew are major diseases. Spray Bordeaux mixture 1 percent or apply oil-based copper fungicide before the monsoon for leaf fall control.
Tapping should begin when the trunk girth reaches 50 cm at 125 cm height. Adopt controlled upward tapping and rain-guarding for monsoon yields.
Fertilizer: apply recommended NPK mixture in two doses; maintain leguminous cover crops to improve soil and reduce erosion on slopes.
""",
"turmeric_telangana_pop.txt": """Turmeric Package of Practices - Telangana
Turmeric is an important spice crop in Telangana. Recommended varieties: Duggirala, Mydukur and improved varieties with high curcumin.
Rhizome rot and leaf spot are common; treat seed rhizomes with Carbendazim before planting and ensure good drainage to prevent rot.
Fertilizer: apply 60 kg N, 50 kg P2O5 and 120 kg K2O per hectare with heavy organic manure (FYM 25 t/ha). Earthing up twice improves rhizome development.
Harvest at 8 to 9 months when leaves turn yellow and dry. Cure rhizomes by boiling and drying for good colour.
""",

# ── NORTH ───────────────────────────────────────────────────────────────────
"paddy_uttarpradesh_pop.txt": """Paddy (Rice) Package of Practices - Uttar Pradesh
Rice is a major kharif crop in Uttar Pradesh. Recommended varieties: Pusa Basmati-1121, Sarju-52, NDR-359 and Pant Dhan varieties.
Stem borer, leaf folder and bacterial leaf blight are common. For bacterial leaf blight avoid excess nitrogen and use resistant varieties; for stem borer apply Cartap hydrochloride 4G at 25 kg/ha.
Fertilizer: apply 120 kg N, 60 kg P2O5 and 40 kg K2O per hectare. Apply nitrogen in three splits, full phosphorus and potash as basal.
Transplant 25 to 30 day old seedlings. Maintain standing water during tillering. Suited to the IGP-Central plains.
""",
"sugarcane_uttarpradesh_pop.txt": """Sugarcane Package of Practices - Uttar Pradesh
Uttar Pradesh is the largest sugarcane producing state. Recommended varieties: Co-0238, CoS-8436 and CoSe-92423 for the subtropical belt.
Top borer and early shoot borer are major pests; apply Chlorantraniliprole and practice trash mulching. Red rot is the most damaging disease - use red-rot resistant varieties and disease-free setts.
Fertilizer: apply 150 kg N, 60 kg P2O5 and 60 kg K2O per hectare. Apply nitrogen in splits up to grand growth phase.
Plant in autumn (October) or spring (February-March). Adopt trench method for higher yields.
""",
"mustard_haryana_pop.txt": """Mustard (Rapeseed-Mustard) Package of Practices - Haryana
Mustard is a major rabi oilseed in Haryana. Recommended varieties: RH-749, RH-725 and Pusa Bold.
Aphid is the most serious pest in the flowering stage; spray Imidacloprid 17.8 SL at 100 ml/ha or Dimethoate when aphid colonies appear. White rust and Alternaria blight are managed with Mancozeb spray.
Fertilizer: apply 80 kg N, 40 kg P2O5, 40 kg K2O and 40 kg Sulphur per hectare. Sulphur is critical for oil content in mustard.
Sowing: mid-October. Seed rate 4 to 5 kg/ha. First irrigation at 30 to 35 days. Suited to the IGP-Northwest zone.
""",
"wheat_haryana_pop.txt": """Wheat Package of Practices - Haryana
Wheat is the principal rabi crop of Haryana. Recommended varieties: WH-1105, HD-3086, DBW-187 and WH-1124 for timely sown irrigated conditions.
Fertilizer: apply 150 kg N, 60 kg P2O5 and 30 kg K2O per hectare. Apply half nitrogen and full phosphorus and potash as basal; apply remaining nitrogen as Urea topdressing at first and second irrigation.
Yellow rust is the major disease - spray Propiconazole 25 EC at 0.1 percent on appearance of pustules. Karnal bunt may occur in late sown crop.
Sowing: first fortnight of November. Critical irrigation at crown root initiation (21 days after sowing).
""",
"bajra_rajasthan_pop.txt": """Pearl Millet (Bajra) Package of Practices - Rajasthan
Pearl millet (bajra) is the principal rainfed cereal of arid Rajasthan. Recommended hybrids: HHB-67 Improved, RHB-177 and Pusa Composite varieties tolerant to drought and downy mildew.
Downy mildew is the major disease - treat seed with Metalaxyl and rogue out infected plants. Shoot fly and white grub are key pests.
Fertilizer: apply 40 kg N and 20 kg P2O5 per hectare under rainfed conditions; increase nitrogen under assured moisture.
Sowing: with onset of monsoon (late June to July). Seed rate 4 kg/ha. Highly suited to the Arid zone with low and erratic rainfall.
""",
"mustard_rajasthan_pop.txt": """Mustard Package of Practices - Rajasthan
Rajasthan is the largest mustard producing state. Recommended varieties: RH-749, Giriraj, NRCHB-101 and Pusa Mustard varieties.
Aphid is the most damaging pest at flowering and pod formation; spray Imidacloprid 17.8 SL at 100 ml/ha. White rust is controlled with Mancozeb 0.2 percent spray.
Fertilizer: apply 60 kg N, 30 kg P2O5 and 40 kg Sulphur per hectare for rainfed; increase under irrigation. Sulphur boosts oil content.
Sowing: mid-October to early November. Seed rate 4 to 5 kg/ha. Provide one or two irrigations at branching and pod-filling where available.
""",
"chana_rajasthan_pop.txt": """Chickpea (Chana/Gram) Package of Practices - Rajasthan
Chickpea is a major rabi pulse of Rajasthan. Recommended varieties: GNG-1581, RSG-888 and wilt-resistant desi types.
Pod borer (Helicoverpa) is the key pest - install pheromone traps, encourage natural enemies and spray Emamectin benzoate or NPV when ETL is crossed. Fusarium wilt is managed with resistant varieties and seed treatment with Trichoderma.
Fertilizer: apply 20 kg N and 40 kg P2O5 per hectare as basal; chickpea fixes its own nitrogen, so avoid excess N. Treat seed with Rhizobium culture.
Sowing: October to early November. Suited to the Arid and semi-arid zones with residual soil moisture.
""",
}


if __name__ == "__main__":
    download_web_corpus()
    write_seed_corpus()
    download_pincodes()
    print("\nDone. Next: python scripts/build_index.py")
