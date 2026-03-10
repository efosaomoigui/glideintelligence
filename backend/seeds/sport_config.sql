-- Sport Category Configuration
INSERT INTO category_configs (category, dimension_mappings, impact_categories, created_at, updated_at)
VALUES (
    'sport',
    '{
        "primary_dimensions": ["competition_type", "audience_engagement", "geographical_scope"],
        "competition_type_options": ["International", "National", "Club/Local", "Youth/Development"],
        "audience_engagement_options": ["High Interest", "Moderate", "Niche/Specialist"],
        "geographical_scope_options": ["Global", "Regional (Africa)", "Local (Nigeria)"]
    }',
    '[
        {"key": "fan_engagement", "label": "Fan Engagement", "icon": "🏟️"},
        {"key": "economic_revenue", "label": "Revenue Impact", "icon": "💰"},
        {"key": "talent_development", "label": "Talent Pipeline", "icon": "🎓"},
        {"key": "infrastructure", "label": "Infrastructure", "icon": "🏗️"}
    ]',
    NOW(),
    NOW()
) ON CONFLICT (category) DO UPDATE SET 
    dimension_mappings = EXCLUDED.dimension_mappings,
    impact_categories = EXCLUDED.impact_categories,
    updated_at = NOW();

-- General Fallback Configuration
INSERT INTO category_configs (category, dimension_mappings, impact_categories, created_at, updated_at)
VALUES (
    'general',
    '{
        "primary_dimensions": ["significance", "urgency", "audience"],
        "significance_options": ["Major", "Moderate", "Minor"],
        "urgency_options": ["High", "Medium", "Low"],
        "audience_options": ["General Public", "Business Leaders", "Policymakers"]
    }',
    '[
        {"key": "public_interest", "label": "Public Interest", "icon": "👥"},
        {"key": "economic_flow", "label": "Economic Flow", "icon": "📈"},
        {"key": "policy_relevance", "label": "Policy Impact", "icon": "⚖️"}
    ]',
    NOW(),
    NOW()
) ON CONFLICT (category) DO UPDATE SET 
    dimension_mappings = EXCLUDED.dimension_mappings,
    impact_categories = EXCLUDED.impact_categories,
    updated_at = NOW();
