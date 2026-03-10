"""
Seed script for category configurations.
Populates the category_configs table using the canonical categories from app/constants.py.

Categories: politics, business, economy, technology, security,
            sports, social, regional, environment, general
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.database import AsyncSessionLocal
from app.models.intelligence import CategoryConfig
from app.constants import VALID_CATEGORIES
from sqlalchemy import select

CATEGORY_CONFIGS = {
    "politics": {
        "dimension_mappings": {
            "primary_dimensions": ["stakeholder", "region", "impact_area"],
            "stakeholder_options": [
                "Opposition Parties", "Ruling Party", "Civil Society",
                "International Community", "Citizens", "State Governors",
                "National Assembly", "Judiciary", "Military", "Traditional Rulers",
                "Youth Groups", "Women Groups"
            ],
            "region_options": [
                "North", "South", "East", "West", "FCT", "Niger Delta",
                "Middle Belt", "North East", "North West", "North Central",
                "South East", "South South", "South West"
            ],
            "impact_area_options": [
                "Governance", "Democracy", "Regional Balance", "Power Dynamics",
                "Policy Direction", "Constitutional Matters", "Electoral Process",
                "Federalism", "State Autonomy", "National Unity"
            ]
        },
        "impact_categories": [
            {"key": "legal_risk", "icon": "⚖️", "label": "Legal Risk"},
            {"key": "regional_tension", "icon": "🗺️", "label": "Regional Tension"},
            {"key": "stakes", "icon": "💸", "label": "At Stake"},
            {"key": "power_shift", "icon": "🔄", "label": "Power Dynamics"}
        ]
    },
    "business": {
        "dimension_mappings": {
            "primary_dimensions": ["sector", "stakeholder", "impact_area"],
            "sector_options": [
                "Fintech", "E-commerce", "Manufacturing", "Services",
                "Hospitality", "Entertainment", "Healthcare", "Education",
                "Logistics", "Agriculture", "Real Estate", "Energy"
            ],
            "stakeholder_options": [
                "Entrepreneurs", "Investors", "Employees", "Customers",
                "Suppliers", "Regulators", "Competitors", "Partners",
                "Shareholders", "Creditors"
            ],
            "impact_area_options": [
                "Revenue", "Profitability", "Market Share", "Competition",
                "Innovation", "Regulation", "Consumer Demand", "Supply Chain",
                "Funding", "Expansion", "Sustainability"
            ]
        },
        "impact_categories": [
            {"key": "market_opportunity", "icon": "🎯", "label": "Market Opportunity"},
            {"key": "competitive_landscape", "icon": "⚔️", "label": "Competitive Landscape"},
            {"key": "regulatory_impact", "icon": "📋", "label": "Regulatory Impact"},
            {"key": "growth_potential", "icon": "📈", "label": "Growth Potential"}
        ]
    },
    "economy": {
        "dimension_mappings": {
            "primary_dimensions": ["sector", "stakeholder", "impact_area"],
            "sector_options": [
                "Banking", "Manufacturing", "Agriculture", "Technology",
                "Oil & Gas", "Retail", "Telecommunications", "Real Estate",
                "Construction", "Mining", "Energy", "Transportation"
            ],
            "stakeholder_options": [
                "Investors", "Consumers", "Businesses", "SMEs", "Government",
                "Foreign Partners", "Regulators", "Central Bank", "Workers",
                "Shareholders", "Creditors"
            ],
            "impact_area_options": [
                "Inflation", "Employment", "Growth", "Trade", "Investment",
                "Currency", "Interest Rates", "GDP", "Fiscal Policy",
                "Monetary Policy", "Market Stability"
            ]
        },
        "impact_categories": [
            {"key": "market_impact", "icon": "📊", "label": "Market Impact"},
            {"key": "business_climate", "icon": "🏢", "label": "Business Climate"},
            {"key": "consumer_effect", "icon": "💳", "label": "Consumer Effect"},
            {"key": "fiscal_implications", "icon": "💰", "label": "Fiscal Implications"}
        ]
    },
    "technology": {
        "dimension_mappings": {
            "primary_dimensions": ["sector", "stakeholder", "impact_area"],
            "sector_options": [
                "Artificial Intelligence", "Blockchain", "Cloud Computing",
                "Cybersecurity", "Mobile Technology", "Internet Infrastructure",
                "Software Development", "Hardware", "Telecommunications",
                "Digital Payments", "EdTech", "HealthTech"
            ],
            "stakeholder_options": [
                "Tech Companies", "Users", "Developers", "Investors",
                "Regulators", "Startups", "Enterprises", "Government",
                "Consumers", "Innovators"
            ],
            "impact_area_options": [
                "Innovation", "Adoption", "Regulation", "Privacy",
                "Security", "Access", "Digital Divide", "Infrastructure",
                "Investment", "Competition", "Standards"
            ]
        },
        "impact_categories": [
            {"key": "innovation_impact", "icon": "💡", "label": "Innovation Impact"},
            {"key": "adoption_rate", "icon": "📱", "label": "Adoption Rate"},
            {"key": "regulatory_framework", "icon": "⚙️", "label": "Regulatory Framework"},
            {"key": "digital_inclusion", "icon": "🌐", "label": "Digital Inclusion"}
        ]
    },
    "security": {
        "dimension_mappings": {
            "primary_dimensions": ["threat_type", "region", "stakeholder"],
            "threat_type_options": [
                "Terrorism", "Banditry", "Kidnapping", "Communal Conflict",
                "Border Security", "Piracy", "Insurgency", "Armed Robbery",
                "Cattle Rustling", "Cultism", "Cybercrime"
            ],
            "region_options": [
                "North East", "North West", "North Central", "South East",
                "South South", "South West", "FCT", "Border Regions",
                "Coastal Areas", "Rural Areas", "Urban Centers"
            ],
            "stakeholder_options": [
                "Military", "Civilians", "Businesses", "Farmers", "Travelers",
                "Investors", "IDPs", "Police", "Vigilantes", "Local Communities",
                "Security Agencies", "Humanitarian Organizations"
            ]
        },
        "impact_categories": [
            {"key": "threat_level", "icon": "🚨", "label": "Threat Level"},
            {"key": "affected_areas", "icon": "📍", "label": "Affected Areas"},
            {"key": "response_status", "icon": "🛡️", "label": "Response Status"},
            {"key": "humanitarian", "icon": "🏥", "label": "Humanitarian Impact"}
        ]
    },
    "sport": {
        "dimension_mappings": {
            "primary_dimensions": ["team", "tournament", "stakeholder"],
            "team_options": [
                "Super Eagles", "National Team", "Local Clubs", "Foreign Clubs",
                "NPFL Teams", "Grassroots Teams"
            ],
            "tournament_options": [
                "AFCON", "World Cup", "Olympics", "NPFL", "CAF Champions League",
                "Local Leagues", "Friendly Matches"
            ],
            "stakeholder_options": [
                "Players", "Coaches", "NFF", "Fans", "Sponsors", "Media",
                "Ministry of Sports", "Club Owners"
            ]
        },
        "impact_categories": [
            {"key": "fan_sentiment", "icon": "🎉", "label": "Fan Sentiment"},
            {"key": "match_outcome", "icon": "⚽", "label": "Match Outcome"},
            {"key": "player_performance", "icon": "🏃", "label": "Player Performance"},
            {"key": "tournament_impact", "icon": "🏆", "label": "Tournament Impact"}
        ]
    },
    "global-impact": {
        "dimension_mappings": {
            "primary_dimensions": ["region", "stakeholder", "impact_area"],
            "region_options": [
                "Global South", "West Africa", "European Union", "China",
                "United States", "Middle East", "Oil Markets", "Commodity Markets"
            ],
            "stakeholder_options": [
                "Foreign Investors", "Exporters", "Importers", "Multinational Corporations",
                "Diplomats", "Diaspora", "IFIs (IMF/World Bank)", "Regulators"
            ],
            "impact_area_options": [
                "Trade Flow", "Investment Policy", "Exchange Rates", "Supply Chain",
                "Strategic Partnerships", "Climate Commitment", "Economic Sovereignty"
            ]
        },
        "impact_categories": [
            {"key": "geopolitics", "icon": "🗺️", "label": "Geopolitical Shifts"},
            {"key": "macro_economy", "icon": "📈", "label": "Macro Economy"},
            {"key": "trade_dynamics", "icon": "🚢", "label": "Trade Dynamics"},
            {"key": "strategy", "icon": "♟️", "label": "Strategic Alignment"}
        ]
    },
    "social": {
        "dimension_mappings": {
            "primary_dimensions": ["stakeholder", "impact_area", "region"],
            "stakeholder_options": [
                "Youth", "Women", "Children", "Elderly", "Disabled",
                "Religious Groups", "Ethnic Groups", "Urban Dwellers",
                "Rural Communities", "Students", "Workers", "Families"
            ],
            "impact_area_options": [
                "Education", "Healthcare", "Housing", "Employment",
                "Social Welfare", "Cultural Identity", "Community Cohesion",
                "Human Rights", "Gender Equality", "Youth Empowerment"
            ],
            "region_options": [
                "Urban Areas", "Rural Areas", "North", "South", "East",
                "West", "Slums", "Suburbs", "City Centers"
            ]
        },
        "impact_categories": [
            {"key": "social_welfare", "icon": "🤝", "label": "Social Welfare"},
            {"key": "community_impact", "icon": "👥", "label": "Community Impact"},
            {"key": "cultural_significance", "icon": "🎭", "label": "Cultural Significance"},
            {"key": "human_development", "icon": "📚", "label": "Human Development"}
        ]
    },
    "regional": {
        "dimension_mappings": {
            "primary_dimensions": ["region", "stakeholder", "impact_area"],
            "region_options": [
                "ECOWAS", "West Africa", "Nigeria", "Ghana", "Senegal",
                "Ivory Coast", "Benin", "Togo", "Niger", "Burkina Faso",
                "Mali", "Guinea", "Liberia", "Sierra Leone", "Gambia"
            ],
            "stakeholder_options": [
                "Regional Bodies", "Member States", "Citizens", "Businesses",
                "International Partners", "Civil Society", "Diaspora",
                "Regional Institutions"
            ],
            "impact_area_options": [
                "Trade", "Security", "Integration", "Migration",
                "Economic Cooperation", "Political Stability", "Infrastructure",
                "Cultural Exchange", "Diplomacy", "Development"
            ]
        },
        "impact_categories": [
            {"key": "regional_stability", "icon": "🌍", "label": "Regional Stability"},
            {"key": "cross_border_impact", "icon": "🔗", "label": "Cross-Border Impact"},
            {"key": "integration_progress", "icon": "🤲", "label": "Integration Progress"},
            {"key": "diplomatic_relations", "icon": "🏛️", "label": "Diplomatic Relations"}
        ]
    },
    "environment": {
        "dimension_mappings": {
            "primary_dimensions": ["impact_area", "stakeholder", "region"],
            "impact_area_options": [
                "Climate Change", "Pollution", "Deforestation", "Water Resources",
                "Biodiversity", "Waste Management", "Renewable Energy",
                "Conservation", "Sustainability", "Natural Disasters"
            ],
            "stakeholder_options": [
                "Communities", "Government", "Businesses", "NGOs",
                "Farmers", "Fishermen", "Indigenous People", "Environmentalists",
                "Industries", "Regulators"
            ],
            "region_options": [
                "Niger Delta", "Coastal Areas", "Forest Regions", "Sahel",
                "Urban Centers", "Rural Areas", "Protected Areas",
                "Industrial Zones", "Agricultural Zones"
            ]
        },
        "impact_categories": [
            {"key": "environmental_risk", "icon": "🌱", "label": "Environmental Risk"},
            {"key": "climate_impact", "icon": "🌡️", "label": "Climate Impact"},
            {"key": "resource_sustainability", "icon": "♻️", "label": "Resource Sustainability"},
            {"key": "health_hazard", "icon": "⚠️", "label": "Health Hazard"}
        ]
    },
    "general": {
        "dimension_mappings": {
            "primary_dimensions": ["stakeholder", "impact_area", "region"],
            "stakeholder_options": [
                "Government", "Citizens", "Businesses", "Civil Society",
                "International Community", "Investors", "Workers", "Youth",
                "Women", "Media", "Regulators", "Experts"
            ],
            "impact_area_options": [
                "Policy", "Economy", "Security", "Social Welfare",
                "Development", "Governance", "Public Interest",
                "Investment", "Reform", "Innovation", "Trade"
            ],
            "region_options": [
                "Nigeria", "West Africa", "Africa", "North", "South",
                "East", "West", "FCT", "Urban Areas", "Rural Areas",
                "National", "International"
            ]
        },
        "impact_categories": [
            {"key": "public_impact", "icon": "👥", "label": "Public Impact"},
            {"key": "policy_implications", "icon": "📋", "label": "Policy Implications"},
            {"key": "economic_effect", "icon": "📊", "label": "Economic Effect"},
            {"key": "future_outlook", "icon": "🔭", "label": "Future Outlook"}
        ]
    },
}

# Enforce at seed time: every key must be in VALID_CATEGORIES
assert set(CATEGORY_CONFIGS.keys()) == VALID_CATEGORIES, (
    f"Mismatch between CATEGORY_CONFIGS keys and VALID_CATEGORIES!\n"
    f"  configs:    {sorted(CATEGORY_CONFIGS.keys())}\n"
    f"  constants:  {sorted(VALID_CATEGORIES)}"
)


async def seed_category_configs():
    """Seed category configurations into the database."""
    async with AsyncSessionLocal() as db:
        print("Seeding category configurations...")

        for category, config_data in CATEGORY_CONFIGS.items():
            result = await db.execute(
                select(CategoryConfig).where(CategoryConfig.category == category)
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  [UPDATE] '{category}' — updating dimensions & impacts")
                existing.dimension_mappings = config_data["dimension_mappings"]
                existing.impact_categories = config_data["impact_categories"]
            else:
                print(f"  [CREATE] '{category}' — creating new config")
                new_config = CategoryConfig(
                    category=category,
                    dimension_mappings=config_data["dimension_mappings"],
                    impact_categories=config_data["impact_categories"]
                )
                db.add(new_config)

        await db.commit()
        print("\n[SUCCESS] Category configurations seeded successfully!")

        result = await db.execute(select(CategoryConfig))
        all_configs = result.scalars().all()
        print(f"\nTotal categories in DB: {len(all_configs)}")
        for config in all_configs:
            dims = config.dimension_mappings.get("primary_dimensions", [])
            impacts = len(config.impact_categories)
            print(f"  - {config.category}: {len(dims)} dimensions, {impacts} impact categories")


if __name__ == "__main__":
    asyncio.run(seed_category_configs())
