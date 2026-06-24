"""
Curated, DETAILED seed corpus for KrishiGPT — modeled on ICAR Package of Practices
and Government of India scheme guidelines.

These are a curated prototype corpus (not scraped from live ICAR PDFs, whose public
URLs are dead). Each document is written to be richly multi-topic so the assistant can
answer a wide variety of farmer questions — varieties, sowing, spacing, seed rate,
fertilizer schedule, irrigation, multiple pests with dosages, multiple diseases, weed
management, and harvest/yield/storage — all from the document itself.

Filenames embed the state so the ingestion state-tagger picks them up.
"""

SEED_DOCS = {

# ════════════════════════════════════ SOUTH ════════════════════════════════════

"paddy_karnataka_pop.txt": """ICAR Package of Practices - Paddy (Rice) - Karnataka

SEASON AND CLIMATE: Paddy in Karnataka is grown in Kharif (June-July sowing) under irrigated and rainfed conditions, and in Summer/Rabi in command areas. It needs warm humid weather and assured water.

RECOMMENDED VARIETIES: For irrigated conditions use Jyothi, IR-64, Tunga, Thanu, BR-2655 and Jaya. For hill zones use Intan and MTU-1001. Short-duration varieties (110-120 days) suit late-sown crops; medium-duration (130-140 days) give higher yields where water is assured.

NURSERY AND SOWING: Raise nursery with 600 sq m for one hectare. Seed rate 30 kg/ha for transplanting. Treat seed with Carbendazim 2 g/kg to prevent seed-borne disease. Transplant 25-30 day old seedlings at 20 x 15 cm spacing, 2-3 seedlings per hill.

FERTILIZER SCHEDULE: Apply 100 kg N, 50 kg P2O5 and 50 kg K2O per hectare for irrigated paddy. Apply full phosphorus and half potash as basal. Apply nitrogen in three splits - basal, active tillering (25 days) and panicle initiation (50 days). Apply zinc sulphate 25 kg/ha if zinc deficiency (bronzing) appears. For one acre, this is about 40 kg N, 20 kg P2O5 and 20 kg K2O.

IRRIGATION: Maintain 2-5 cm standing water during tillering and flowering. Avoid water stress at panicle initiation and flowering. Drain the field 10 days before harvest. Adopt alternate wetting and drying (AWD) to save water where supply is limited.

PESTS:
- Stem borer: causes dead hearts in vegetative stage and white ears at flowering. Apply Cartap hydrochloride 4G at 25 kg/ha or Chlorantraniliprole 0.4G at 10 kg/ha in standing water; drain before application. Remove and destroy egg masses, use light traps.
- Brown planthopper (BPH): causes hopperburn (circular drying patches). Drain water, avoid excess nitrogen, and spray Imidacloprid 17.8 SL at 125 ml/ha or Pymetrozine 50 WG at 300 g/ha.
- Leaf folder: spray Flubendiamide 480 SC at 50 ml/ha when damage exceeds threshold.

DISEASES:
- Blast: diamond-shaped lesions on leaves and neck rot. Spray Tricyclazole 75 WP at 0.6 g/litre. Avoid excess nitrogen and use resistant varieties.
- Bacterial leaf blight: yellow-water-soaked lesions. Use resistant varieties, avoid stagnant water, and spray copper oxychloride 3 g/litre.
- Sheath blight: greenish-grey lesions on sheath. Spray Hexaconazole 5 EC at 2 ml/litre.

WEED MANAGEMENT: Apply Pretilachlor 50 EC at 3-5 days after transplanting, or hand weed twice at 20 and 40 days. Maintain a thin water film to suppress weeds.

HARVEST AND STORAGE: Harvest when 80% of grains turn straw-colored and moisture is around 20-22%. Dry grain to 12-13% moisture before storage. Store in clean, dry, airtight bins to prevent storage pests. Average yield 5-6 t/ha under good management.
""",

"ragi_karnataka_pop.txt": """ICAR Package of Practices - Finger Millet (Ragi) - Karnataka

OVERVIEW: Finger millet (ragi) is a major dryland cereal of Karnataka, drought-hardy and nutritious. Grown mainly in Kharif under rainfed conditions in the southern dry and eastern dry zones.

VARIETIES: GPU-28, GPU-48, ML-365, Indaf-9 and KMR-301 are recommended; GPU-28 is blast-tolerant and widely grown.

SOWING: Sow with onset of monsoon (June-July). Seed rate 10 kg/ha for line sowing, 5 kg/ha for transplanting. Spacing 30 x 10 cm. Treat seed with Carbendazim 2 g/kg against blast.

FERTILIZER: Apply 50 kg N, 40 kg P2O5 and 25 kg K2O per hectare. Apply half nitrogen and full phosphorus and potash as basal; topdress remaining nitrogen at 30 days. Apply 5 t/ha farmyard manure.

PESTS AND DISEASES: Blast (neck and finger blast) is the major disease - spray Tricyclazole 75 WP at 0.6 g/litre and use resistant varieties like GPU-28. Pink stem borer is managed with Cartap hydrochloride 4G at 8 kg/ha.

IRRIGATION AND HARVEST: Largely rainfed; give protective irrigation at flowering if a dry spell occurs. Harvest when fingers turn brown. Yield 2.5-3.5 t/ha. Ragi stores very well for years if dried to 12% moisture.
""",

"paddy_tamilnadu_pop.txt": """ICAR Package of Practices - Paddy (Rice) - Tamil Nadu

SEASONS: Tamil Nadu grows rice in three seasons - Kuruvai (June-July), Samba (Aug-Sept) and Thaladi/Navarai. The Cauvery delta is the rice bowl of the state.

VARIETIES: ADT-43, ADT-45, ADT-37 (short duration), CO-51, TKM-13 and BPT-5204 for medium duration. ADT-43 is popular for Kuruvai due to its short 110-day duration.

NURSERY AND TRANSPLANTING: Seed rate 30 kg/ha (transplanted), 60 kg/ha (direct seeded). Treat seed with Carbendazim. Transplant 21-25 day old seedlings at 20 x 10 cm. SRI (System of Rice Intensification) uses 12-14 day seedlings, single seedling per hill at 25 x 25 cm and saves water.

FERTILIZER: Apply 150 kg N, 50 kg P2O5 and 50 kg K2O per hectare for irrigated rice. Apply nitrogen in 3-4 splits using the leaf colour chart. Apply full P and half K basal. Use Azospirillum and Phosphobacteria biofertilizers.

IRRIGATION: Maintain shallow submergence (2 cm) and adopt AWD in the delta to save water. Critical stages are tillering, panicle initiation and flowering.

PESTS: Brown planthopper is a serious pest in the delta - drain water and spray Imidacloprid 17.8 SL at 125 ml/ha. Stem borer - apply Cartap hydrochloride 4G at 25 kg/ha. Gall midge - use resistant varieties and Phorate granules.

DISEASES: Blast - spray Tricyclazole 75 WP 0.6 g/litre. Bacterial leaf blight - copper oxychloride spray and resistant varieties. Tungro virus (vectored by green leafhopper) - control the vector and remove infected plants.

WEEDS AND HARVEST: Pre-emergence Pretilachlor at 3 DAT; one hand weeding at 30-35 days. Harvest at physiological maturity; dry to 12-13%. Yield 5-7 t/ha.
""",

"groundnut_tamilnadu_pop.txt": """ICAR Package of Practices - Groundnut - Tamil Nadu

OVERVIEW: Groundnut is the principal oilseed of Tamil Nadu, grown in Kharif (rainfed) and Rabi/Summer (irrigated).

VARIETIES: TMV-7, VRI-2, VRI-8, CO-7 and bold-seeded spreading types. Bunch varieties suit irrigated short-duration crops.

SOWING: Seed rate 125 kg/ha (kernels) for bunch types at 30 x 10 cm. Treat seed with Trichoderma viride 4 g/kg and Rhizobium culture. Gypsum-treated soil improves pod filling.

FERTILIZER: Apply 25 kg N, 50 kg P2O5 and 75 kg K2O per hectare. Apply gypsum at 500 kg/ha at the pegging stage (40-45 days) for calcium - this is critical for kernel development. Apply micronutrient mixture if needed.

IRRIGATION: Critical stages are flowering, pegging and pod development. Avoid water stress at pegging. Stop irrigation 10 days before harvest.

PESTS: Leaf miner and red hairy caterpillar - spray Quinalphos 25 EC at 2 ml/litre. Thrips and aphids (vector bud necrosis virus) - spray Imidacloprid.

DISEASES: Tikka leaf spot (early and late) and rust - spray Chlorothalonil or Mancozeb at 2.5 g/litre at first appearance and repeat after 15 days. Stem rot - apply Trichoderma and avoid waterlogging.

HARVEST: Harvest when leaves yellow and inner shell shows dark veins. Dry pods to 8-9% moisture. Yield 2-2.5 t/ha (irrigated).
""",

"cotton_telangana_pop.txt": """ICAR Package of Practices - Cotton - Telangana

OVERVIEW: Cotton (mostly Bt hybrids) is the principal commercial crop of Telangana, grown largely rainfed on black and red soils.

VARIETIES: Approved Bt cotton hybrids for the region; desi cotton in rainfed shallow soils. Choose bollworm-resistant Bt hybrids suited to the area.

SOWING: Sow with monsoon onset (June-July). Spacing 90 x 60 cm for hybrids. Seed rate 1.5-2 kg/ha for Bt hybrids. Treat seed with Imidacloprid for early sucking-pest protection.

FERTILIZER: Apply 120 kg N, 60 kg P2O5 and 60 kg K2O per hectare for irrigated Bt cotton, in splits up to flowering. Apply full P and K basal; N in 4 splits. Foliar spray of 2% DAP and Magnesium sulphate at flowering boosts boll setting.

PESTS:
- Pink bollworm: the key pest. Install pheromone traps at 8 per hectare, monitor, and spray Emamectin benzoate 5 SG at 0.4 g/litre or Profenophos when ETL is crossed. Do NOT extend the crop beyond December - timely termination breaks the pest cycle.
- Sucking pests (jassids, whitefly, thrips): spray Acetamiprid 20 SP at 0.2 g/litre or Diafenthiuron.

DISEASES: Bacterial blight and Alternaria leaf spot - spray copper oxychloride and Mancozeb. Wilt - rotate with non-host crops and use tolerant hybrids.

IRRIGATION AND HARVEST: Critical stages are flowering and boll development; avoid stress. Pick in 3-4 rounds as bolls open. Avoid mixing trash. Yield 15-25 quintals seed cotton/ha under good management.
""",

"chilli_andhra_pop.txt": """ICAR Package of Practices - Chilli - Andhra Pradesh

OVERVIEW: Andhra Pradesh (Guntur region) is the largest chilli producer in India, grown both for dry chilli and as a high-value irrigated crop.

VARIETIES: LCA-334, LCA-625, Teja (high pungency), and G-4. Teja is preferred for high capsaicin and export.

NURSERY AND PLANTING: Raise nursery and transplant 40-45 day old seedlings at 60 x 45 cm. Treat seed with Trichoderma. Seed rate 1-1.5 kg/ha.

FERTILIZER: Apply 150 kg N, 60 kg P2O5 and 100 kg K2O per hectare in splits. Apply 25 t/ha FYM. Foliar spray of micronutrients corrects flower drop.

PESTS:
- Thrips: cause upward leaf curl (murda complex) and transmit virus. Spray Fipronil 5 SC at 2 ml/litre or Spinosad. Remove severely infected plants.
- Mites: cause downward leaf curl. Spray Dicofol or Spiromesifen.
- Fruit borer: spray Emamectin benzoate.

DISEASES: Leaf curl (viral, thrips-vectored) is the major problem - manage the vector and rogue out infected plants. Anthracnose/die-back and fruit rot - spray Carbendazim + Mancozeb at 2 g/litre.

IRRIGATION AND HARVEST: Drip irrigation with mulching gives best results in Guntur black soils. Harvest red ripe fruits at intervals; dry to 10% moisture for storage. Yield 2-3 t/ha dry chilli.
""",

"turmeric_telangana_pop.txt": """ICAR Package of Practices - Turmeric - Telangana

OVERVIEW: Turmeric is an important irrigated spice crop in Telangana, valued for curcumin content.

VARIETIES: Duggirala, Mydukur, Armoor, and improved high-curcumin varieties. Select disease-free seed rhizomes.

PLANTING: Plant mother and finger rhizomes in June-July at 30 x 20 cm. Seed rate 2000-2500 kg rhizomes/ha. Treat seed rhizomes with Carbendazim 0.1% + Quinalphos before planting. Mulch with green leaves at planting and again at 45 days.

FERTILIZER: Apply 60 kg N, 50 kg P2O5 and 120 kg K2O per hectare, with heavy organic manure (FYM 25-30 t/ha). Apply nitrogen in splits. Earthing up twice (60 and 90 days) improves rhizome development.

PESTS AND DISEASES: Rhizome rot and leaf spot are common - ensure good drainage, treat seed rhizomes, and spray Mancozeb 2.5 g/litre for leaf spot. Shoot borer - spray Quinalphos at monthly intervals.

IRRIGATION AND HARVEST: Needs 15-25 irrigations; maintain moisture during rhizome bulking. Harvest at 8-9 months when leaves dry. Cure by boiling and drying for good colour. Yield 25-30 t/ha fresh rhizome.
""",

"coconut_kerala_pop.txt": """ICAR Package of Practices - Coconut - Kerala

OVERVIEW: Coconut is the most important plantation crop of Kerala, grown across the humid coastal plains and midlands.

VARIETIES: West Coast Tall, Chowghat Orange Dwarf (for tender nuts), and hybrids like Kerasankara (WCT x COD) and Chandrasankara for high yield.

PLANTING: Plant 9-12 month old seedlings at 7.5 x 7.5 m (175 palms/ha) in pits of 1 x 1 x 1 m filled with topsoil, FYM and salt. Plant at the start of the monsoon.

FERTILIZER: Apply 500 g N, 320 g P2O5 and 1200 g K2O per palm per year in two splits with the monsoons. Apply 50 kg FYM and Magnesium and add common salt for potassium uptake. Adult palms respond strongly to potassium.

PESTS:
- Rhinoceros beetle: bores into the crown. Treat the top three leaf axils with a mixture of sand and naphthalene balls; hook out beetles; use pheromone traps.
- Red palm weevil: grubs tunnel the trunk. Avoid injury to the stem, fill leaf axils with insecticide, and use pheromone traps for monitoring.

DISEASES: Root (wilt) disease is serious in Kerala - remove and burn severely affected palms, apply balanced nutrition and good drainage. Bud rot (Phytophthora) - remove affected tissue and apply Bordeaux paste; spray 1% Bordeaux mixture before the monsoon.

IRRIGATION AND HARVEST: Irrigate 200 litres per palm once in 4-7 days in summer; drip is efficient. Harvest mature nuts every 45 days. Yield 80-120 nuts per palm per year for good hybrids.
""",

"rubber_kerala_pop.txt": """ICAR/Rubber Board Package of Practices - Natural Rubber - Kerala

OVERVIEW: Natural rubber is a major plantation crop of Kerala's humid zone, grown on well-drained lateritic slopes.

CLONES: RRII-105, RRII-414, RRII-430 and PB-260 are recommended high-yielding clones. RRII-105 is widely planted.

PLANTING: Plant budded stumps or polybag plants at 4.9 x 4.9 m (about 420 plants/ha) at the start of the monsoon. Establish leguminous cover crops (Mucuna, Pueraria) to control erosion and improve soil.

FERTILIZER: Apply recommended NPK mixture in two doses during pre-monsoon and post-monsoon. Young rubber needs higher nitrogen; mature tapping rubber needs balanced NPK with magnesium.

TAPPING: Begin tapping when trunk girth reaches 50 cm at 125 cm height (usually 6-7 years). Adopt controlled half-spiral alternate-daily tapping. Use rain-guards to continue tapping through the monsoon.

DISEASES: Abnormal leaf fall (Phytophthora) is the major monsoon disease - spray oil-based copper fungicide or Bordeaux mixture before the monsoon. Powdery mildew on young flush - dust sulphur. Pink disease on the trunk - apply Bordeaux paste.

YIELD: Mature, well-managed RRII-105 yields about 1500-2000 kg dry rubber per hectare per year.
""",

# ════════════════════════════════════ NORTH ════════════════════════════════════

"wheat_punjab_pop.txt": """ICAR Package of Practices - Wheat - Punjab

OVERVIEW: Wheat is the principal rabi crop of Punjab in the rice-wheat system of the IGP-Northwest.

VARIETIES: HD-3086, PBW-725, PBW-826, WH-1105 and DBW-187 for timely-sown irrigated conditions. For late sowing use PBW-771 and HD-3059.

SOWING: Sow in the first fortnight of November for timely crop. Seed rate 100 kg/ha at 20-22.5 cm row spacing. Treat seed with Tebuconazole against loose smut. Late sowing reduces yield by about 1% per day after mid-November.

FERTILIZER: Apply 120 kg N, 60 kg P2O5 and 30 kg K2O per hectare. Apply half nitrogen and full phosphorus and potash as basal at sowing. Apply remaining nitrogen as Urea topdressing - first at crown root initiation/first irrigation (21 days) and second at second irrigation. Roughly 110 kg Urea per acre split across basal and two topdressings.

IRRIGATION: The most critical irrigation is at crown root initiation (21 days after sowing). Other critical stages: tillering, jointing, flowering, milk and dough. Usually 4-6 irrigations.

PESTS AND DISEASES:
- Yellow (stripe) rust: the major disease - spray Propiconazole 25 EC at 0.1% (200 ml/acre) on appearance of yellow pustules. Grow rust-resistant varieties.
- Aphids: usually controlled by natural enemies; spray only if severe.
- Loose smut and Karnal bunt: managed by seed treatment and resistant varieties.

WEEDS: Phalaris minor (gulli danda) is the major weed - apply Clodinafop or Sulfosulfuron post-emergence; rotate herbicides to avoid resistance. Broadleaf weeds - 2,4-D.

HARVEST: Harvest at 12-14% grain moisture when straw turns golden. Avoid burning residue; manage stubble with Happy Seeder. Yield 5-6 t/ha.
""",

"wheat_haryana_pop.txt": """ICAR Package of Practices - Wheat - Haryana

OVERVIEW: Wheat is the principal rabi crop of Haryana in the IGP-Northwest zone, mostly in rotation with rice or cotton.

VARIETIES: WH-1105, WH-1124, HD-3086 and DBW-187 for timely-sown irrigated conditions. WH-1124 is suited to late sowing.

SOWING: Sow in the first fortnight of November. Seed rate 100 kg/ha at 20 cm rows. Treat seed against loose smut with Tebuconazole.

FERTILIZER: Apply 150 kg N, 60 kg P2O5 and 30 kg K2O per hectare. Apply half N and full P and K basal; topdress remaining N as Urea at first and second irrigation. Apply Zinc sulphate 25 kg/ha in zinc-deficient soils.

IRRIGATION: Crown root initiation (21 DAS) is the most critical irrigation. Typically 4-6 irrigations depending on soil and rainfall.

PESTS AND DISEASES: Yellow rust - spray Propiconazole 25 EC at 0.1%. Termites in light soils - treat seed/soil with Chlorpyriphos. Karnal bunt in late-sown crop - use resistant varieties.

WEEDS: Phalaris minor - Clodinafop or Pinoxaden post-emergence; broadleaf weeds with 2,4-D or Metsulfuron. HARVEST: at 12-14% moisture. Yield 4.5-5.5 t/ha.
""",

"mustard_haryana_pop.txt": """ICAR Package of Practices - Mustard (Rapeseed-Mustard) - Haryana

OVERVIEW: Mustard is a major rabi oilseed of Haryana, grown rainfed and under limited irrigation.

VARIETIES: RH-749, RH-725, RH-30 and Pusa Bold. RH-749 is high-yielding and widely grown.

SOWING: Sow mid-October for best yields. Seed rate 4-5 kg/ha at 30 x 10 cm spacing. Thin to maintain plant population. Treat seed with Apron/Metalaxyl against downy mildew.

FERTILIZER: Apply 80 kg N, 40 kg P2O5, 40 kg K2O and 40 kg Sulphur per hectare. Sulphur is critical for oil content and yield in mustard - apply gypsum or elemental sulphur. Apply half N basal and half at first irrigation.

IRRIGATION: First irrigation at 30-35 days (branching), second at flowering/pod-filling where water is available. One or two irrigations markedly raise yield.

PESTS AND DISEASES: Mustard aphid is the most serious pest at flowering - spray Imidacloprid 17.8 SL at 100 ml/ha or Dimethoate when colonies appear; spray in the evening to protect pollinators. White rust and Alternaria blight - spray Mancozeb 0.2%.

HARVEST: Harvest when pods turn yellow-brown and seeds are firm; avoid shattering by harvesting in the morning. Yield 1.5-2 t/ha.
""",

"paddy_uttarpradesh_pop.txt": """ICAR Package of Practices - Paddy (Rice) - Uttar Pradesh

OVERVIEW: Rice is a major kharif crop in Uttar Pradesh across the IGP-Central plains, including basmati belts.

VARIETIES: Pusa Basmati-1121 and Pusa Basmati-1509 (basmati), Sarju-52, NDR-359, MTU-7029 (Swarna) and Pant Dhan for non-basmati.

NURSERY AND TRANSPLANTING: Seed rate 30 kg/ha for transplanting. Transplant 25-30 day old seedlings at 20 x 15 cm, 2-3 seedlings per hill. Treat seed with Carbendazim.

FERTILIZER: Apply 120 kg N, 60 kg P2O5 and 40 kg K2O per hectare. Apply nitrogen in three splits, full phosphorus and potash basal. Apply Zinc sulphate 25 kg/ha if khaira (zinc deficiency) appears.

IRRIGATION: Maintain shallow submergence during tillering; avoid stress at panicle initiation and flowering. Drain 10 days before harvest.

PESTS AND DISEASES: Stem borer - Cartap hydrochloride 4G at 25 kg/ha. Bacterial leaf blight - avoid excess nitrogen and use resistant varieties. Brown planthopper - drain and spray Imidacloprid. Blast - Tricyclazole 75 WP 0.6 g/litre. False smut in basmati - spray copper fungicide at boot stage.

WEEDS AND HARVEST: Pre-emergence Pretilachlor; one hand weeding. Harvest at maturity; for basmati harvest at the right moisture to preserve aroma and grain length. Yield 4-6 t/ha.
""",

"sugarcane_uttarpradesh_pop.txt": """ICAR Package of Practices - Sugarcane - Uttar Pradesh

OVERVIEW: Uttar Pradesh is the largest sugarcane producing state, grown in the subtropical belt.

VARIETIES: Co-0238 (dominant), CoS-8436, CoSe-92423 and Co-15023. Use only red-rot resistant varieties and disease-free three-budded setts.

PLANTING: Plant in autumn (October) or spring (February-March). Seed rate about 35,000-40,000 three-budded setts per hectare. Treat setts with Carbendazim 0.1% and hot-water treatment against grassy shoot. Adopt trench or pit method for higher yields.

FERTILIZER: Apply 150 kg N, 60 kg P2O5 and 60 kg K2O per hectare. Apply nitrogen in splits up to the grand growth phase (June-July). Apply full P and K basal. Earthing up supports the crop and improves yield.

PESTS AND DISEASES: Early shoot borer and top borer - apply Chlorantraniliprole or Cartap granules and practice trash mulching. Pyrilla (leaf hopper) - encourage the parasitoid Epiricania. Red rot is the most damaging disease - use resistant varieties, disease-free setts, and rogue out affected clumps.

IRRIGATION AND HARVEST: Critical stages are germination, tillering and grand growth. Harvest at 10-12 months at peak maturity (brix test). Yield 70-90 t/ha. Ratoon management can give a second crop.
""",

"bajra_rajasthan_pop.txt": """ICAR Package of Practices - Pearl Millet (Bajra) - Rajasthan

OVERVIEW: Pearl millet (bajra) is the principal rainfed cereal of arid Rajasthan, highly drought-tolerant.

VARIETIES: HHB-67 Improved (very early, downy-mildew resistant), RHB-177, RHB-173 and Pusa Composite. HHB-67 Improved escapes terminal drought due to its short duration.

SOWING: Sow with the onset of monsoon (late June-July). Seed rate 4 kg/ha at 45 x 12 cm. Treat seed with Metalaxyl against downy mildew and thiram.

FERTILIZER: Apply 40 kg N and 20 kg P2O5 per hectare under rainfed conditions; raise nitrogen to 60-80 kg under assured moisture. Apply half N basal, half at 30 days with rainfall.

PESTS AND DISEASES: Downy mildew (green ear) is the major disease - treat seed with Metalaxyl, use resistant hybrids, and rogue out infected plants. Shoot fly and white grub - treat seed/soil with Chlorpyriphos. Blast and ergot - use clean seed and resistant varieties.

IRRIGATION AND HARVEST: Largely rainfed; one protective irrigation at grain filling raises yield if available. Harvest earheads when grains harden. Yield 1.5-2.5 t/ha. Bajra stores well in dry conditions.
""",

"mustard_rajasthan_pop.txt": """ICAR Package of Practices - Mustard - Rajasthan

OVERVIEW: Rajasthan is the largest mustard producing state, grown rainfed on residual moisture and under limited irrigation in the arid/semi-arid zone.

VARIETIES: RH-749, Giriraj, NRCHB-101, Pusa Mustard-25 and RGN-73. Choose varieties suited to early or late sowing and to white-rust pressure.

SOWING: Sow mid-October to early November. Seed rate 4-5 kg/ha at 30 x 10 cm. Treat seed with Metalaxyl against downy mildew.

FERTILIZER: Apply 60 kg N, 30 kg P2O5 and 40 kg Sulphur per hectare for rainfed; raise N to 80 kg under irrigation. Sulphur strongly increases oil content - apply gypsum at 200-250 kg/ha.

IRRIGATION: First irrigation at branching (30-35 days), second at siliqua (pod) development. Even one irrigation greatly increases yield in this dry region.

PESTS AND DISEASES: Mustard aphid is the key pest at flowering/pod-filling - spray Imidacloprid 17.8 SL at 100 ml/ha; spray in the evening to spare bees. White rust and Alternaria blight - spray Mancozeb 0.2%. Orobanche (broomrape) parasitic weed - hand-pull before flowering.

HARVEST: Harvest at pod-yellowing, thresh after sun-drying. Yield 1.5-2 t/ha (irrigated), 1-1.2 t/ha (rainfed).
""",

"chana_rajasthan_pop.txt": """ICAR Package of Practices - Chickpea (Chana/Gram) - Rajasthan

OVERVIEW: Chickpea is a major rabi pulse of Rajasthan, grown on residual soil moisture in the arid and semi-arid zones; it fixes its own nitrogen.

VARIETIES: GNG-1581, GNG-1958, RSG-888 and wilt-resistant desi types. Choose Fusarium-wilt-resistant varieties.

SOWING: Sow October to early November. Seed rate 60-80 kg/ha (desi) at 30 x 10 cm. Treat seed with Trichoderma + Carbendazim, then with Rhizobium and PSB culture for nitrogen fixation and phosphorus uptake.

FERTILIZER: Apply 20 kg N and 40 kg P2O5 per hectare as basal only; avoid excess nitrogen because chickpea fixes atmospheric nitrogen. Apply sulphur in deficient soils.

IRRIGATION: Mostly grown on conserved moisture; one irrigation at pre-flowering and another at pod development raise yield where available. Avoid waterlogging.

PESTS AND DISEASES: Pod borer (Helicoverpa) is the key pest - install pheromone traps, encourage natural enemies, spray NPV or Emamectin benzoate / Chlorantraniliprole when ETL is crossed. Fusarium wilt - use resistant varieties and seed treatment with Trichoderma. Avoid early sowing in warm soils to reduce wilt.

HARVEST: Harvest when plants dry and pods rattle. Yield 1.5-2 t/ha. Store dry seed with neem leaves to deter bruchids.
""",

# ════════════════════════════════════ WEST / CENTRAL ════════════════════════════

"cotton_gujarat_pop.txt": """ICAR Package of Practices - Cotton - Gujarat

OVERVIEW: Cotton is a major cash crop of Gujarat, grown irrigated and rainfed on black and medium soils; the state is a leading Bt cotton producer.

VARIETIES: Approved Bt cotton hybrids; G.Cot.Hy-8 and desi cotton (G.Cot-21) for rainfed shallow soils. Desi cotton tolerates sucking pests better.

SOWING: Spacing 120 x 45 cm for Bt cotton. Seed rate 1.5-2 kg/ha. Treat seed with Imidacloprid for early sucking-pest protection. Sow with monsoon onset or under pre-sowing irrigation.

FERTILIZER: Apply 240 kg N, 60 kg P2O5 and 0 kg K2O per hectare for irrigated Bt cotton (K only if soil test shows deficiency). Apply nitrogen in 4 splits up to flowering. Foliar 2% DAP and Magnesium at flowering improves boll retention.

PESTS:
- Whitefly: vector of leaf curl virus - spray Diafenthiuron 50 WP at 1 g/litre or Acetamiprid; avoid indiscriminate sprays that flare whitefly.
- Pink bollworm: install pheromone traps at 5 per hectare; spray Profenophos 50 EC at 2 ml/litre when ETL is crossed; terminate the crop on time.
- Jassids and thrips: spray Acetamiprid 20 SP.

DISEASES: Leaf curl virus (whitefly-borne) - manage the vector, rogue out infected plants. Bacterial blight - copper oxychloride spray. Wilt - rotate with pulses and use tolerant hybrids.

IRRIGATION AND HARVEST: Critical stages flowering and boll development; avoid waterlogging. Pick in 3-4 rounds. Yield 15-25 quintals seed cotton/ha.
""",

"groundnut_gujarat_pop.txt": """ICAR Package of Practices - Groundnut - Gujarat

OVERVIEW: Gujarat is one of India's largest groundnut producers, grown mainly in Kharif (Saurashtra) under rainfed and irrigated conditions.

VARIETIES: GG-20, GJG-31, TG-37A and bold-seeded Spanish bunch types suited to Saurashtra.

SOWING: Sow with monsoon onset. Seed rate 100-125 kg/ha (kernels) at 30 x 10 cm. Treat seed with Trichoderma + Rhizobium. Gypsum improves pod set.

FERTILIZER: Apply 12.5 kg N, 25 kg P2O5 and gypsum at 500 kg/ha at pegging for calcium. Apply FYM and, where deficient, micronutrients (boron, iron).

IRRIGATION: Critical at flowering, pegging and pod development. Avoid stress at pegging; stop irrigation before harvest.

PESTS AND DISEASES: Leaf miner and Spodoptera - spray Quinalphos or Emamectin benzoate. Tikka leaf spot and rust - spray Mancozeb/Chlorothalonil 2.5 g/litre. Stem rot and collar rot - Trichoderma seed treatment, good drainage. Aflatoxin - avoid drought stress and dry pods properly.

HARVEST: Harvest at maturity (dark shell veins); dry to 8-9% moisture. Yield 2-2.5 t/ha (irrigated).
""",

"sugarcane_maharashtra_pop.txt": """ICAR Package of Practices - Sugarcane - Maharashtra

OVERVIEW: Sugarcane is widely grown in the Deccan region of Maharashtra under irrigation; a major crop for sugar and jaggery.

VARIETIES: Co-86032 (dominant), CoM-0265, Co-92005 and CoVSI-9805. Use disease-free three-budded setts.

PLANTING: Plant in suru (Jan-Feb), pre-seasonal (Oct-Nov) or adsali (July). Seed rate about 25,000-30,000 setts/ha. Treat setts with Carbendazim. Wide-row and paired-row planting suit mechanization and drip.

FERTILIZER: Apply 250 kg N, 115 kg P2O5 and 115 kg K2O per hectare. Apply nitrogen in splits at planting, tillering and grand growth. Apply FYM/press mud and micronutrients (Fe, Zn) where deficient.

PESTS AND DISEASES: Early shoot borer - Chlorantraniliprole or Cartap granules and trash mulching. Woolly aphid - release predators (Dipha, Micromus); avoid broad-spectrum sprays. Grassy shoot disease - hot-water treat setts and rogue out affected clumps; red rot - resistant varieties.

IRRIGATION AND HARVEST: Critical stages germination, tillering and grand growth. Adopt drip irrigation to save water in scarcity-prone Maharashtra. Harvest at maturity by brix; yield 80-100 t/ha. Manage ratoon for a second crop.
""",

"soybean_madhyapradesh_pop.txt": """ICAR Package of Practices - Soybean - Madhya Pradesh

OVERVIEW: Madhya Pradesh is the largest soybean producer in India ('Soya state'), grown rainfed in Kharif on black soils of the Central zone.

VARIETIES: JS-9560, JS-2034, JS-2069 and NRC-86. JS-9560 is early-maturing and widely grown.

SOWING: Sow with the onset of monsoon (late June-early July) when 100 mm rain is received. Seed rate 65-75 kg/ha at 45 x 5 cm. Treat seed with Thiram + Carbendazim, then Rhizobium and PSB. Broad-bed-and-furrow planting helps drainage.

FERTILIZER: Apply 20 kg N, 60-80 kg P2O5, 40 kg K2O and 20 kg Sulphur per hectare as basal. Soybean fixes nitrogen, so keep N low. Sulphur improves oil content.

PESTS AND DISEASES: Girdle beetle and stem fly - spray Thiamethoxam or Triazophos. Defoliators (Spodoptera, Bihar hairy caterpillar) - Emamectin benzoate or Indoxacarb. Yellow mosaic virus (whitefly-borne) - manage whitefly and use tolerant varieties. Rhizoctonia aerial blight and rust - spray Hexaconazole.

WEEDS AND HARVEST: Pre-emergence Pendimethalin; one hand weeding at 30 days. Harvest when leaves drop and pods rattle; avoid shattering. Yield 1.5-2.5 t/ha.
""",

# ════════════════════════════════════ HORTICULTURE (multi-state) ════════════════

"tomato_general_pop.txt": """ICAR Package of Practices - Tomato (Vegetable)

OVERVIEW: Tomato is a major vegetable grown across India in all seasons under open field and protected conditions.

VARIETIES AND HYBRIDS: Arka Rakshak (triple disease resistant), Arka Samrat, Pusa Ruby, and many F1 hybrids. Choose disease-resistant hybrids for leaf curl and wilt-prone areas.

NURSERY AND PLANTING: Raise nursery in protrays; transplant 25-30 day old seedlings at 60 x 45 cm. Treat seed with Trichoderma. Stake indeterminate types.

FERTILIZER: Apply 120 kg N, 60 kg P2O5 and 60 kg K2O per hectare with 25 t/ha FYM. Apply N and K in splits via fertigation where drip is used. Calcium prevents blossom-end rot.

PESTS: Fruit borer (Helicoverpa) - pheromone traps and Emamectin benzoate/Chlorantraniliprole. Whitefly (leaf curl vector) - Diafenthiuron/Acetamiprid. Tomato pinworm (Tuta absoluta) - pheromone traps and Spinosad.

DISEASES: Early and late blight - spray Mancozeb, then Metalaxyl+Mancozeb for late blight. Bacterial wilt - use resistant varieties (Arka Rakshak), grafting, and crop rotation. Leaf curl virus - manage whitefly and rogue infected plants.

IRRIGATION AND HARVEST: Drip with mulch is ideal; avoid water stress at flowering and fruiting. Harvest at breaker/red-ripe stage as needed. Yield 40-60 t/ha (hybrids).
""",

"onion_general_pop.txt": """ICAR Package of Practices - Onion (Vegetable)

OVERVIEW: Onion is a major bulb crop grown in Kharif, late-Kharif and Rabi; Maharashtra, Karnataka, Gujarat and MP are leading producers.

VARIETIES: Agrifound Light Red, Bhima Super, Bhima Red (kharif), and N-53. Choose varieties for the season and for storage.

NURSERY AND PLANTING: Transplant 6-7 week old seedlings at 15 x 10 cm. Seed rate 8-10 kg/ha. Avoid deep planting.

FERTILIZER: Apply 100 kg N, 50 kg P2O5, 50 kg K2O and 30 kg Sulphur per hectare. Sulphur improves bulb pungency and storage. Apply N in splits; stop N early to aid curing.

PESTS AND DISEASES: Thrips are the major pest (silvery streaks on leaves) - spray Fipronil 5 SC at 2 ml/litre or Spinosad; add a sticker. Purple blotch and Stemphylium blight - spray Mancozeb/Hexaconazole with a sticker. Basal rot - Trichoderma and good drainage.

IRRIGATION AND HARVEST: Light frequent irrigation; stop 10-15 days before harvest to aid curing. Harvest when 50-70% tops fall over; cure in shade for storage. Yield 25-35 t/ha.
""",

# ════════════════════════════════════ SCHEMES (pan-India) ══════════════════════

"pmfby_scheme_india.txt": """Pradhan Mantri Fasal Bima Yojana (PMFBY) - Crop Insurance Scheme (Government of India)

WHAT IT IS: PMFBY is a pan-India crop insurance scheme that protects farmers against yield loss from natural calamities, pests and diseases, for notified crops in notified areas.

ELIGIBILITY: All farmers - including sharecroppers and tenant farmers - growing notified crops in notified areas are eligible. Enrollment is voluntary for all farmers (including loanee farmers).

FARMER PREMIUM: Farmers pay a maximum of 2% of the sum insured for Kharif food and oilseed crops, 1.5% for Rabi food and oilseed crops, and 5% for annual commercial and horticultural crops. The balance premium is shared by central and state governments.

RISKS COVERED: Prevented sowing, standing crop losses (drought, flood, pests, disease), post-harvest losses for up to 14 days for crops kept to dry in the field, and localized calamities (hailstorm, landslide, inundation).

DOCUMENTS NEEDED: Aadhaar card, bank account details (for Direct Benefit Transfer), land records (khasra/khatauni) or a tenancy/sharecropping agreement, and a sowing declaration/certificate.

HOW AND WHERE TO APPLY: Enroll through the nearest bank, a Common Service Centre (CSC), the insurance company's agent, or the National Crop Insurance Portal (pmfby.gov.in) BEFORE the cut-off date notified for each crop and season. Loanee farmers are enrolled through their financing bank.

CLAIMS: Yield-based claims are settled using Crop Cutting Experiments. Report localized losses within 72 hours through the bank, insurer toll-free number, or the Crop Insurance app.
""",

"pmkisan_scheme_india.txt": """Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) - Income Support Scheme (Government of India)

WHAT IT IS: PM-KISAN is a pan-India central-sector income support scheme that pays eligible landholding farmer families Rs 6000 per year, in three equal installments of Rs 2000 every four months, directly into the bank account (DBT).

ELIGIBILITY: All landholding farmer families with cultivable land are eligible, subject to exclusions. Family means husband, wife and minor children.

EXCLUSIONS: Institutional landholders; constitutional post holders; serving/retired government employees and pensioners drawing pension of Rs 10,000 or more (excluding Group D); income-tax payers in the last assessment year; and professionals like doctors, engineers, lawyers and CAs in practice.

DOCUMENTS NEEDED: Aadhaar card (mandatory), bank account details, and land ownership records. eKYC (Aadhaar-based OTP or biometric) is required to receive installments.

HOW AND WHERE TO APPLY: Register through the PM-KISAN portal (pmkisan.gov.in) self-registration, a Common Service Centre (CSC), or the local revenue officer / village accountant (Patwari). Aadhaar-seed your bank account for DBT.

CHECK STATUS: Use the 'Beneficiary Status' option on the PM-KISAN portal with your Aadhaar or registered mobile/account number to see installment status and correct errors.
""",

"kcc_scheme_india.txt": """Kisan Credit Card (KCC) - Agricultural Credit Scheme (Government of India / RBI / NABARD)

WHAT IT IS: The Kisan Credit Card provides farmers timely and affordable short-term credit for crop cultivation, post-harvest expenses, and allied activities (dairy, fisheries, poultry). Available through commercial banks, cooperative banks and regional rural banks across India.

ELIGIBILITY: All farmers - individual or joint cultivators (owner-cultivators), tenant farmers, oral lessees and sharecroppers, and Self-Help Groups or Joint Liability Groups - are eligible. Allied-activity farmers (animal husbandry, fisheries) are also covered.

CREDIT LIMIT: The limit is based on the scale of finance for the crop, the area cultivated, and a component for post-harvest and consumption needs. The card is valid for 5 years subject to annual review and is renewable.

INTEREST AND SUBVENTION: Short-term crop loans up to Rs 3 lakh carry an interest subvention; with prompt repayment, the effective interest is about 4% per annum (7% base minus 3% prompt-repayment incentive). A collateral-free limit is available up to the RBI-specified amount.

DOCUMENTS NEEDED: Identity proof (Aadhaar), address proof, and land records / proof of cultivation. Passport-size photographs are required.

HOW AND WHERE TO APPLY: Apply at any bank branch with the prescribed form, or through the bank's online KCC facility / a Common Service Centre. KCC can also be linked with the PM-KISAN database for faster processing.
""",
}
