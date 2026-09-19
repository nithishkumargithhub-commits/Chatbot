"""
scripts/chunk_schemes.py — JeevanPath AI
Phase 2: High-Precision Scheme Chunker

Leverages the official 41-scheme Table of Contents and OCR section boundaries
to extract complete, structured, and noise-free scheme records.

Input : backend/data/raw_ocr.json
Output: backend/data/chunks.json
"""

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR    = BACKEND_DIR / "data"
IN_PATH     = DATA_DIR / "raw_ocr.json"
OUT_PATH    = DATA_DIR / "chunks.json"

SCHEMES_SPEC = [
    # Category A: Skill Development Schemes (Pages 8-52)
    {
        "id": 1, "sec": "1.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Skill Development and Entrepreneurship (MSDE)",
        "name": "Pradhan Mantri Kaushal Vikas Yojana (PMKVY)",
        "heading_pattern": r"1\.1\.\s*PRADHAN\s+MANTRI\s+KAUSHAL\s+VIKAS\s+YOJANA"
    },
    {
        "id": 2, "sec": "1.2", "category": "Skill Development Schemes",
        "ministry": "Ministry of Skill Development and Entrepreneurship (MSDE)",
        "name": "Apprenticeship Training Scheme (ATS)",
        "heading_pattern": r"1\.2\.\s*APPRENTICESHIP\s+TRAINING\s+SCHEME"
    },
    {
        "id": 3, "sec": "1.3", "category": "Skill Development Schemes",
        "ministry": "Ministry of Skill Development and Entrepreneurship (MSDE)",
        "name": "Craftsmen Training Scheme (CTS)",
        "heading_pattern": r"1\.3\.\s*CRAFTSMEN\s+TRAINING\s+SCHEME"
    },
    {
        "id": 4, "sec": "1.4", "category": "Skill Development Schemes",
        "ministry": "Ministry of Skill Development and Entrepreneurship (MSDE)",
        "name": "Skill Development Initiative Scheme (SDIS)",
        "heading_pattern": r"1\.4\.\s*SKILL[I\s]+DEVELOPMENT\s+INITIATIVE"
    },
    {
        "id": 5, "sec": "2.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Rural Development",
        "name": "Deen Dayal Upadhyaya Grameen Kaushalya Yojana (DDU-GKY)",
        "heading_pattern": r"2\.1\.\s*DEEN\s+DAYAL\s+UPADHYAYA\s+GRAMEEN\s+KAUSHALYA"
    },
    {
        "id": 6, "sec": "2.2", "category": "Skill Development Schemes",
        "ministry": "Ministry of Rural Development",
        "name": "Rural Self-Employment Training Institutes (RSETIS)",
        "heading_pattern": r"2\.2\.\s*RURAL\s+SELF[- ]EMPLOYMENT\s+TRAINING"
    },
    {
        "id": 7, "sec": "3.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Housing and Urban Poverty Alleviation",
        "name": "National Urban Livelihoods Mission (NULM)",
        "heading_pattern": r"3\.1\.\s*NATIONAL\s+URBAN\s+LIVELIHOODS\s+MISSION"
    },
    {
        "id": 8, "sec": "4.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Textiles",
        "name": "Integrated Skill Development Scheme (ISDS)",
        "heading_pattern": r"4\.1\.\s*INTEGRATED\s+SKILL\s+DEVELOPMENT"
    },
    {
        "id": 9, "sec": "5.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Agriculture",
        "name": "National Food Security Mission - Farmers Field School",
        "heading_pattern": r"5\.1\.\s*NATIONAL\s+FOOD\s+SECURITY\s+MISSION"
    },
    {
        "id": 10, "sec": "5.2", "category": "Skill Development Schemes",
        "ministry": "Ministry of Agriculture",
        "name": "Agri-Clinic and Agri-Business Centres Scheme (ACABC)",
        "heading_pattern": r"5\.2\.\s*AGRI[- ]CLINIC"
    },
    {
        "id": 11, "sec": "5.3", "category": "Skill Development Schemes",
        "ministry": "Ministry of Agriculture",
        "name": "Extension Reforms Farm School",
        "heading_pattern": r"5\.3\.\s*EXTENSION\s+REFORMS"
    },
    {
        "id": 12, "sec": "6.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Micro, Small and Medium Enterprises (MSME)",
        "name": "Entrepreneurship Development Programmes (EDP)",
        "heading_pattern": r"6\.1\.\s*ENTREPRENEURSHIP\s+DEVELOPMENT\s+PROGRAMMES"
    },
    {
        "id": 13, "sec": "6.2", "category": "Skill Development Schemes",
        "ministry": "Ministry of Micro, Small and Medium Enterprises (MSME)",
        "name": "Entrepreneurship Skill Development Programmes (ESDP)",
        "heading_pattern": r"6\.2\.\s*ENTREPRENEURSHIP\s+SKILL\s+DEVELOPMENT\s+PROGRAMMES"
    },
    {
        "id": 14, "sec": "6.3", "category": "Skill Development Schemes",
        "ministry": "Ministry of Micro, Small and Medium Enterprises (MSME)",
        "name": "Management Development Programmes (MDP)",
        "heading_pattern": r"6\.3\.\s*MANAGEMENT\s+DEVELOPMENT\s+PROGRAMMES"
    },
    {
        "id": 15, "sec": "6.4", "category": "Skill Development Schemes",
        "ministry": "Ministry of Micro, Small and Medium Enterprises (MSME)",
        "name": "Assistance to Training Institutions Scheme (ATI Scheme)",
        "heading_pattern": r"6\.4\.\s*ASSISTANCE\s+TO\s+TRAINING\s+INSTITUTIONS"
    },
    {
        "id": 16, "sec": "6.5", "category": "Skill Development Schemes",
        "ministry": "Ministry of Micro, Small and Medium Enterprises (MSME)",
        "name": "Skill Upgradation & Quality Improvement and Mahila Coir Yojana (MCY)",
        "heading_pattern": r"6\.5\.\s*SKILL\s+UPGRADATION"
    },
    {
        "id": 17, "sec": "7.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Tourism",
        "name": "Scheme of Capacity Building for Service Providers",
        "heading_pattern": r"7\.1\.\s*SCHEME\s+OF\s+CAPACITY\s+BUILDING"
    },
    {
        "id": 18, "sec": "7.2", "category": "Skill Development Schemes",
        "ministry": "Ministry of Tourism",
        "name": "Hunar Se Rozgar Tak Initiative",
        "heading_pattern": r"7\.2\.\s*HUNAR\s+SE\s+ROZGAR"
    },
    {
        "id": 19, "sec": "8.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Human Resource Development (MHRD)",
        "name": "Apprenticeship Scheme (MHRD)",
        "heading_pattern": r"8\.1\.\s*APPRENTICESHIP\s+SCHEME"
    },
    {
        "id": 20, "sec": "8.2", "category": "Skill Development Schemes",
        "ministry": "Ministry of Human Resource Development (MHRD)",
        "name": "Vocationalization of School Education",
        "heading_pattern": r"8\.2\.\s*VOCATIONALIZATION\s+OF\s+SCHOOL"
    },
    {
        "id": 21, "sec": "8.3", "category": "Skill Development Schemes",
        "ministry": "Ministry of Human Resource Development (MHRD)",
        "name": "Scheme of Community Development Through Polytechnics",
        "heading_pattern": r"8\.3\.\s*SCHEME\s+OF\s+COMMUNITY\s+DEVELOPMENT"
    },
    {
        "id": 22, "sec": "9.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of IT and Communication",
        "name": "Scheme for Financial Assistance to States for Skill Development in ESDM Sector",
        "heading_pattern": r"9\.1\.\s*SCHEME\s+FOR\s+FINANCIAL\s+ASSISTANCE\s+TO\s+STATES"
    },
    {
        "id": 23, "sec": "9.2", "category": "Skill Development Schemes",
        "ministry": "Ministry of IT and Communication",
        "name": "Skill Development in ESDM for Digital India",
        "heading_pattern": r"9\.2\.\s*SKILL\s+DEVELOPMENT\s+IN\s+ESDM"
    },
    {
        "id": 24, "sec": "10.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Tribal Affairs",
        "name": "Vocational Training for Tribal Youth",
        "heading_pattern": r"10\.1\s*[\.\-]?\s*VOCATIONAL\s+TRAINING\s+FOR\s+TRIBAL"
    },
    {
        "id": 25, "sec": "11.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Women and Child Development",
        "name": "Support to Training and Employment Programme for Women (STEP)",
        "heading_pattern": r"11\.1\s*[\.\-]?\s*SUPPORT\s*TO\s+TRAINING\s+AND\s+EMPLOYMENT"
    },
    {
        "id": 26, "sec": "12.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Commerce and Industry",
        "name": "Indian Leather Development Programme (ILDP)",
        "heading_pattern": r"12\.1\s*[\.\-]?\s*INDIAN\s+LEATHER\s+DEVELOPMENT"
    },
    {
        "id": 27, "sec": "13.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Development of North Eastern Region (DoNER)",
        "name": "Capacity Building & Technical Assistance",
        "heading_pattern": r"13\.1\s*[\.\-]?\s*CAPACITY\s+BUILDING\s+&\s+TECHNICAL"
    },
    {
        "id": 28, "sec": "14.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Home Affairs",
        "name": "UDAAN Special Industry Initiative for J&K",
        "heading_pattern": r"14\.1\s*[\.\-]?\s*UDAAN"
    },
    {
        "id": 29, "sec": "15.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Minority Affairs",
        "name": "Seekho Aur Kamao (Learn and Earn)",
        "heading_pattern": r"15\.1\s*[\.\-]?\s*SEEKHO\s*AURI?\s*KAMAO"
    },
    {
        "id": 30, "sec": "15.2", "category": "Skill Development Schemes",
        "ministry": "Ministry of Minority Affairs",
        "name": "Nai Roshni (Leadership Development of Minority Women)",
        "heading_pattern": r"15\.2\s*[\.\-]?\s*NAI\s+ROSHINI"
    },
    {
        "id": 31, "sec": "16.1", "category": "Skill Development Schemes",
        "ministry": "Ministry of Social Justice and Empowerment",
        "name": "Financial Assistance for Skill Training of Persons with Disabilities",
        "heading_pattern": r"16\.1\s*[\.\-]?\s*FINANCIAL\s*ASSISTANCE\s+FOR\s+SKILL\s+TRAINING"
    },

    # Category B: Skill Development Training Through Institutes (Pages 53-61)
    {
        "id": 32, "sec": "B-1.1", "category": "Training Through Institutes",
        "ministry": "Ministry of Food Processing",
        "name": "Skill Development Programs Under NIFTEM and IICPT",
        "heading_pattern": r"(?:P53|1\.1\.)\s*SKILL\s+DEVELOPMENT\s+PROGRAMS\s+UNDER\s+NIFT[E|M]"
    },
    {
        "id": 33, "sec": "B-2.1", "category": "Training Through Institutes",
        "ministry": "Ministry of Chemicals and Fertilizers",
        "name": "Central Institute of Plastics Engineering and Technology (CIPET)",
        "heading_pattern": r"(?:P55|2\.1\.)\s*CENTRAL\s+INSTITUTE\s+OF\s+PLASTICS"
    },
    {
        "id": 34, "sec": "B-3.1", "category": "Training Through Institutes",
        "ministry": "Ministry of Agriculture",
        "name": "Krishi Vigyan Kendras (KVKs)",
        "heading_pattern": r"(?:P57|3\.1\.)\s*KRISHI\s+VIGYAN\s+KENDRAS"
    },
    {
        "id": 35, "sec": "B-4.1", "category": "Training Through Institutes",
        "ministry": "Ministry of Human Resource Development (MHRD)",
        "name": "National Institute of Open Schooling (NIOS) Distance Vocational Education",
        "heading_pattern": r"(?:P59|4\.1\.)\s*NATIONAL\s+INSTITUTE\s+OF\s+OPEN\s+SCHOOLING"
    },
    {
        "id": 36, "sec": "B-4.2", "category": "Training Through Institutes",
        "ministry": "Ministry of Human Resource Development (MHRD)",
        "name": "Jan Shikshan Sansthan (JSS)",
        "heading_pattern": r"4\.2\.\s*JAN:?\s*SHIKSHAN\s+SANSTHAN"
    },

    # Category C: Other Initiatives (Pages 62-67)
    {
        "id": 37, "sec": "C-1.1", "category": "Other Initiatives",
        "ministry": "Ministry of Social Justice and Empowerment",
        "name": "Special Central Assistance (SCA) to Scheduled Castes Sub Plan (SCSP)",
        "heading_pattern": r"(?:P62|1\.1\.)\s*SPECIAL\s+CENTRAL\s*ASSISTANCE\s*\(SCA\)"
    },
    {
        "id": 38, "sec": "C-1.2", "category": "Other Initiatives",
        "ministry": "Ministry of Social Justice and Empowerment",
        "name": "National Scheduled Castes Finance & Development Corporation (NSFDC)",
        "heading_pattern": r"1\.2\.\s*NATIONAL\s*SCHEDULED\s+CASTES"
    },
    {
        "id": 39, "sec": "C-1.3", "category": "Other Initiatives",
        "ministry": "Ministry of Social Justice and Empowerment",
        "name": "National Safai Karamcharis Finance & Development Corporation (NSKFDC)",
        "heading_pattern": r"1\.3\.\s*NATIONAL\s+SAFAIKARAMCHARIS"
    },
    {
        "id": 40, "sec": "C-1.4", "category": "Other Initiatives",
        "ministry": "Ministry of Social Justice and Empowerment",
        "name": "National Backward Classes Finance & Development Corporation (NBCFDC)",
        "heading_pattern": r"1\.4\.\s*NATIONAL\s+BACKWARD\s+CLASS"
    },
    {
        "id": 41, "sec": "C-1.5", "category": "Other Initiatives",
        "ministry": "Ministry of Social Justice and Empowerment",
        "name": "National Handicapped Finance and Development Corporation (NHFDC)",
        "heading_pattern": r"1\.5\.\s*FINANCIAL\s*ASSISTANCE\s+FOR\s+SKILL\s+TRAINING\s+OF\s+PERSONS\s+WITH\s+DISAB"
    },
]

FIELD_PATTERNS = {
    "description": re.compile(r"Brief\s*Description\s*[:\-]?\s*(.*?)(?=Nature\s+of\s+Assistance|Who\s+can\s+apply|How\s+to\s+apply|Source\s+of|Target\s+Segment|$)", re.DOTALL | re.IGNORECASE),
    "assistance" : re.compile(r"Nature\s+of\s+Assistance\s*[:\-]?\s*(.*?)(?=Who\s+can\s+apply|How\s+to\s+apply|Source\s+of|$)", re.DOTALL | re.IGNORECASE),
    "eligibility": re.compile(r"Who\s+can\s+apply\s*\??\s*[:\-]?\s*(.*?)(?=How\s+to\s+apply|Source\s+of|$)", re.DOTALL | re.IGNORECASE),
    "how_to_apply": re.compile(r"How\s+to\s+apply\s*\??\s*[:\-]?\s*(.*?)(?=Source\s+of|$)", re.DOTALL | re.IGNORECASE),
    "source_url": re.compile(r"Source\s+of\s+(?:Information|information)\s*[:\-]?\s*([^\n]+)", re.IGNORECASE),
}

def clean_text(text: str) -> str:
    text = text.replace("0f", "of").replace("1akh", "lakh").replace("tot thet", "to the")
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^\s*\d{1,3}\s*$", "", text, flags=re.MULTILINE)
    return text.strip()

def extract_field(text: str, pattern: re.Pattern) -> str:
    m = pattern.search(text)
    return clean_text(m.group(1)) if m else ""

def run_chunking():
    print("=" * 60)
    print("JeevanPath AI — Phase 2: High-Precision Scheme Chunker")
    print("=" * 60)

    if not IN_PATH.exists():
        print(f"ERROR: {IN_PATH} not found.")
        sys.exit(1)

    with open(IN_PATH, "r", encoding="utf-8") as f:
        pages = json.load(f)

    # We build a continuous text starting from page 8 (skip cover, preface, TOC)
    scheme_pages = [p for p in pages if p["page"] >= 8]
    full_doc = "\n\n".join(p["text"] for p in scheme_pages)

    # Locate each scheme heading position in the document
    matches = []
    for spec in SCHEMES_SPEC:
        regex = re.compile(spec["heading_pattern"], re.IGNORECASE)
        m = regex.search(full_doc)
        if m:
            matches.append({"spec": spec, "pos": m.start()})
        else:
            # Fallback: search for section number and scheme keyword
            kw = spec["name"].split()[0]
            fallback_pattern = re.compile(rf"{re.escape(spec['sec'])}\.?\s*.*?{kw}", re.IGNORECASE)
            m2 = fallback_pattern.search(full_doc)
            if m2:
                matches.append({"spec": spec, "pos": m2.start()})
            else:
                print(f"  [WARN] Heading not matched directly: {spec['sec']} {spec['name']}")

    # Sort matches by position in text
    matches.sort(key=lambda x: x["pos"])

    chunks = []
    for i, item in enumerate(matches):
        spec = item["spec"]
        start = item["pos"]
        end = matches[i + 1]["pos"] if i + 1 < len(matches) else len(full_doc)
        raw_scheme_text = clean_text(full_doc[start:end])

        desc = extract_field(raw_scheme_text, FIELD_PATTERNS["description"])
        asst = extract_field(raw_scheme_text, FIELD_PATTERNS["assistance"])
        elig = extract_field(raw_scheme_text, FIELD_PATTERNS["eligibility"])
        apply = extract_field(raw_scheme_text, FIELD_PATTERNS["how_to_apply"])
        url_match = extract_field(raw_scheme_text, FIELD_PATTERNS["source_url"])

        # Rich chunk text for vector embedding
        rich_chunk = (
            f"Government Scheme: {spec['name']}\n"
            f"Ministry: {spec['ministry']}\n"
            f"Category: {spec['category']}\n"
            f"Section: {spec['sec']}\n\n"
            f"Description:\n{desc if desc else raw_scheme_text[:400]}\n\n"
            f"Nature of Assistance / Benefits:\n{asst}\n\n"
            f"Eligibility / Who Can Apply:\n{elig}\n\n"
            f"How to Apply:\n{apply}\n\n"
            f"Full Details:\n{raw_scheme_text}"
        )
        rich_chunk = clean_text(rich_chunk)

        chunks.append({
            "id": spec["id"],
            "section_num": spec["sec"],
            "scheme_name": spec["name"],
            "ministry": spec["ministry"],
            "category": spec["category"],
            "chunk_text": rich_chunk,
            "description": desc,
            "assistance": asst,
            "eligibility": elig,
            "how_to_apply": apply,
            "source_url": url_match,
            "word_count": len(rich_chunk.split()),
            "char_length": len(rich_chunk),
        })

    print(f"\nExtracted {len(chunks)} of {len(SCHEMES_SPEC)} complete schemes:\n")
    for c in chunks:
        print(f"  [{c['section_num']:<6}] {c['scheme_name'][:50]:<50} | {c['word_count']:4d} words")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(chunks)} chunks -> {OUT_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    run_chunking()
