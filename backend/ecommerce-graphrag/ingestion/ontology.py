# Enforced Ontology Configuration for Enterprise GraphRAG Extraction

# We restrict the LLM to these categories to prevent graph explosion (hallucinated schemas).
ALLOWED_NODES = [
    "Product",
    "Brand",
    "Category",
    "Feature",
    "Material",
    "Benefit",
    "TargetAudience"
]

ALLOWED_RELATIONSHIPS = [
    "PRODUCED_BY",
    "BELONGS_TO",
    "HAS_FEATURE",
    "MADE_OF",
    "PROVIDES_BENEFIT",
    "DESIGNED_FOR"
]
