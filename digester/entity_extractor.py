# digester/entity_extractor.py
import spacy
from spacy.pipeline import EntityRuler
import os
import json

# Load model (transformer → better NER; fallback to small if missing)
try:
    nlp = spacy.load("en_core_web_trf")
except OSError:
    nlp = spacy.load("en_core_web_sm")

# Optional: load domain patterns for guaranteed matches
ruler = nlp.add_pipe("entity_ruler", before="ner")
patterns = [
    {"label": "ORG", "pattern": "Lawrence Livermore National Laboratory"},
    {"label": "ORG", "pattern": "Los Alamos National Laboratory"},
    {"label": "ORG", "pattern": "NIST"},
    {"label": "ORG", "pattern": "Macquarie University"},
    {"label": "ORG", "pattern": "Trinity College Dublin"},
    {"label": "ORG", "pattern": "Zeiss"},
    {"label": "ORG", "pattern": "RP Photonics"},
    {"label": "ORG", "pattern": "Optics.org"},
    {"label": "ORG", "pattern": "Photonics Media"},
    # add more, or load from config/entity_ruler_patterns.json if present
]

# Load external patterns if available
custom_patterns_path = os.path.join("config", "entity_ruler_patterns.json")
if os.path.exists(custom_patterns_path):
    try:
        with open(custom_patterns_path, "r") as f:
            ext_patterns = json.load(f)
            if isinstance(ext_patterns, list):
                patterns.extend(ext_patterns)
    except Exception:
        pass

ruler.add_patterns(patterns)

TRACKED = {"ORG", "PERSON", "GPE", "NORP", "FAC"}

def extract_entities(text: str):
    doc = nlp(text or "")
    out = []
    for ent in doc.ents:
        if ent.label_ in TRACKED:
            out.append({"text": ent.text.strip(), "raw_label": ent.label_})
    return out
