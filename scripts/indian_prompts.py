"""
Indian Photo Labeling: LLaVA Prompt + Label Mapping
=====================================================
Used by GitHub Actions decrypt_and_label.py
"""

LLAVA_PROMPT = """Analyze this photo of a woman carefully.
Answer ONLY using the format below. Use ONLY the listed options. No explanations.

AGE_YEARS: [a number, e.g. 26]
AGE_GROUP: [teen | college | young_adult | prime | mature | older]
  (teen=under21, college=21-26, young_adult=26-30, prime=30-36, mature=36-45, older=45+)
BODY_BUILD: [very_slim | slim | athletic_toned | average | thick_heavy | curvy_hourglass | plus_size]
SKIN_COLOR: [very_fair | fair | light_brown | medium_brown | olive_brown | dark_brown | dark]
HAIR_LENGTH: [short | shoulder | long | very_long]
CLOTHING: [bare_minimal | bikini_swimwear | lingerie_intimate | crop_top_midriff | gym_sportswear | western_casual | western_party | traditional_indian | saree | salwar_kameez | indo_western_fusion | fully_covered]
POSE: [lying_horizontal | sitting | standing | close_up_selfie]
MOOD: [happy_cheerful | neutral_calm | shy_coy | confident_bold | seductive_suggestive | serious | playful]
ETHNICITY: [south_asian_indian | east_asian | middle_eastern | african | caucasian_white | latina | mixed_unclear]
SOUTH_ASIAN_REGION: [north_indian | south_indian | east_indian | general_desi | not_applicable]
BODY_DETAIL: [petite_lean | athletic_fit | average_proportional | pear_hips | hourglass_defined | uniformly_full | very_heavy]
"""


def parse_llava_response(text: str) -> dict:
    """Extract KEY: value pairs from LLaVA output."""
    result = {}
    for line in text.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().upper().replace(" ", "_")
            val_parts = val.strip().lower().split()
            if val_parts:
                val = val_parts[0].strip("[]().,")
            else:
                val = ""
            result[key] = val
    return result


def map_to_indian_labels(raw: dict) -> dict:
    """Maps LLaVA visual answers to Indian-context labels."""
    def _int(v, d):
        try: return int(str(v).strip())
        except: return d

    age_years   = _int(raw.get("AGE_YEARS", "25"), 25)
    age_group   = raw.get("AGE_GROUP", "young_adult")
    body_build  = raw.get("BODY_BUILD", "average")
    skin_color  = raw.get("SKIN_COLOR", "medium_brown")
    hair_length = raw.get("HAIR_LENGTH", "long")
    clothing    = raw.get("CLOTHING", "western_casual")
    pose        = raw.get("POSE", "standing")
    mood        = raw.get("MOOD", "neutral_calm")
    ethnicity   = raw.get("ETHNICITY", "south_asian_indian")
    region      = raw.get("SOUTH_ASIAN_REGION", "general_desi")

    is_desi = (ethnicity == "south_asian_indian")

    age_tag_map = {
        "teen": "teen", "college": "young", "young_adult": "young",
        "prime": "prime", "mature": "mature", "older": "aunty",
    }
    age_tag = age_tag_map.get(age_group, "prime")

    # ── Archetype logic ──────────────────────────────────────────────
    archetype = "desi" if is_desi else "model"
    if is_desi:
        is_trad = clothing in ("traditional_indian","saree","salwar_kameez","indo_western_fusion")
        is_west = clothing in ("western_casual","western_party","crop_top_midriff","gym_sportswear")
        is_bold_cloth = clothing in ("bikini_swimwear","lingerie_intimate","bare_minimal","crop_top_midriff")
        bold_mood = mood in ("seductive_suggestive","confident_bold")

        if age_group in ("teen","college") and is_west:
            archetype = "college_girl"
        elif is_bold_cloth and bold_mood:
            archetype = "desi_glam"
        elif region == "south_indian":
            archetype = "south_indian_beauty"
        elif region == "north_indian" and skin_color in ("very_fair","fair") and (is_west or is_bold_cloth):
            archetype = "punjabi_kudi"
        elif age_group == "young_adult" and is_trad:
            archetype = "young_bhabhi"
        elif age_group in ("prime","mature","older") and (is_trad or body_build in ("curvy_hourglass","plus_size","thick_heavy")):
            archetype = "bhabhi"
        elif age_group == "older":
            archetype = "aunty"
        elif clothing == "fully_covered" and mood in ("shy_coy","neutral_calm"):
            archetype = "village_girl"
        elif region == "general_desi" and is_west and skin_color in ("very_fair","fair","light_brown"):
            archetype = "nri_girl"

    # ── Skin tone (Indian spectrum) ──────────────────────────────────
    skin_map = {
        "very_fair":    "fair",
        "fair":         "fair",
        "light_brown":  "wheatish_fair",
        "medium_brown": "wheatish",
        "olive_brown":  "wheatish_dusky",
        "dark_brown":   "dusky",
        "dark":         "dark",
    }
    skin_tag = skin_map.get(skin_color, "wheatish")

    # ── Body tags ────────────────────────────────────────────────────
    body_tag_map = {
        "very_slim":       ["slim","petite","thin"],
        "slim":            ["slim","lean"],
        "athletic_toned":  ["toned","athletic","fit"],
        "average":         ["average","medium_build"],
        "thick_heavy":     ["thick","healthy","chubby"],
        "curvy_hourglass": ["curvy","hourglass","full_figure"],
        "plus_size":       ["plus_size","bbw","full_figure"],
    }
    body_tags = body_tag_map.get(body_build, ["average"])

    # ── Boldness ─────────────────────────────────────────────────────
    boldness_map = {
        "bare_minimal":       "explicit",
        "bikini_swimwear":    "bikini",
        "lingerie_intimate":  "lingerie",
        "crop_top_midriff":   "bold",
        "gym_sportswear":     "moderate",
        "western_party":      "bold",
        "western_casual":     "moderate",
        "traditional_indian": "covered",
        "saree":              "covered",
        "salwar_kameez":      "covered",
        "indo_western_fusion":"moderate",
        "fully_covered":      "covered",
    }
    boldness = boldness_map.get(clothing, "moderate")

    # ── Mood tags ────────────────────────────────────────────────────
    mood_tags = {
        "happy_cheerful":       ["happy","cheerful"],
        "neutral_calm":         ["calm"],
        "shy_coy":              ["shy","innocent","shy_desi"],
        "confident_bold":       ["confident","bold_vibe"],
        "seductive_suggestive": ["seductive","hot","sexy"],
        "serious":              ["serious"],
        "playful":              ["playful","fun"],
    }.get(mood, [])

    # ── Regional tags ────────────────────────────────────────────────
    regional_tags = {
        "north_indian": ["north_indian"],
        "south_indian": ["south_indian"],
        "east_indian":  ["east_indian","bengali_vibes"],
        "general_desi": [],
    }.get(region, [])

    # ── Clothing tags ────────────────────────────────────────────────
    clothing_tags = {
        "traditional_indian": ["traditional","ethnic"],
        "saree":              ["saree","traditional"],
        "salwar_kameez":      ["salwar","ethnic"],
        "indo_western_fusion":["indo_western","fusion"],
        "gym_sportswear":     ["gym","sporty"],
        "bikini_swimwear":    ["bikini","swimwear"],
        "lingerie_intimate":  ["lingerie","intimate"],
        "crop_top_midriff":   ["crop_top","midriff"],
        "western_party":      ["western","party"],
        "western_casual":     ["western","casual"],
    }.get(clothing, [])

    pose_tag = {"lying_horizontal":"lying","sitting":"sitting","standing":"standing","close_up_selfie":"selfie"}.get(pose,"standing")
    ethnicity_short = "desi" if is_desi else "western"
    compound_title  = f"{age_tag}_{ethnicity_short}_{body_tags[0]}"
    compound_persona = f"{compound_title} ({archetype})"

    all_tags = set()
    if is_desi: all_tags.update(["desi","indian"])
    else: all_tags.add(ethnicity.replace("_",""))
    all_tags.update(body_tags)
    all_tags.add(skin_tag)
    all_tags.add(age_tag)
    if age_group in ("prime","mature","older") and is_desi: all_tags.add("bhabhi")
    if age_group in ("teen","college") and is_desi: all_tags.add("college")
    all_tags.add(archetype)
    all_tags.update(mood_tags)
    all_tags.update(clothing_tags)
    all_tags.update(regional_tags)
    all_tags.add(boldness)
    all_tags.add(pose_tag)
    all_tags.add(hair_length)
    all_tags.discard("")

    combo_tags = sorted(all_tags)
    folder = f"{archetype}/{body_tags[0]}"

    # ── Query simulation ─────────────────────────────────────────────
    queries = [
        ["desi","bhabhi"], ["desi","young","slim"], ["desi","mature","curvy"],
        ["desi","college"], ["south_indian","dusky"], ["bold","desi"],
        ["bikini","desi"], ["punjabi_kudi","fair"],
    ]
    query_matches = []
    for q in queries:
        matched = [t for t in q if t in combo_tags]
        query_matches.append({
            "query": " + ".join(q), "match_pct": round(len(matched)/len(q)*100),
            "matched": matched, "is_exact": len(matched)==len(q),
        })

    return {
        "compound_persona": compound_persona, "compound_title": compound_title,
        "archetype": archetype, "combo_tags": combo_tags, "folder": folder,
        "is_desi": is_desi, "age_years": age_years, "age_group": age_group,
        "age_tag": age_tag, "body_type": body_tags[0], "skin_tone": skin_tag,
        "boldness": boldness, "regional_type": region, "mood": mood,
        "clothing_type": clothing, "pose": pose_tag, "hair_length": hair_length,
        "query_matches": query_matches, "llava_raw": raw,
    }
