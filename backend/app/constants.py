"""
app/constants.py
================
Single source of truth for category names used throughout the system.

IMPORTANT: These are the ONLY valid category values anywhere in the codebase:
  - topics.category  (DB column)
  - raw_articles.category  (DB column)
  - category_configs.category  (DB column — must match exactly)
  - normalize_articles_job  (keyword assignment)
  - generate_topic_analysis_job  (config lookup)

If you need to rename a category, change it HERE first, then re-run:
  python seed_category_configs.py
"""

# Canonical category list — used everywhere
CATEGORIES = {
    "politics":      "Politics",
    "business":      "Business",
    "economy":       "Economy",
    "technology":    "Technology",
    "security":      "Security",
    "sport":         "Sport",
    "regional":      "Regional",
    "global-impact": "Global Impact",
    "social":        "Social",
    "environment":   "Environment",
    "general":       "General",
}

# Slugs only (used for validation and DB values)
VALID_CATEGORIES = set(CATEGORIES.keys())

# Default category when no keyword matches
DEFAULT_CATEGORY = "general"
