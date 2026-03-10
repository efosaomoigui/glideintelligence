-- Migrate 'technology' to 'tech' in category_configs
UPDATE category_configs SET category = 'tech' WHERE category = 'technology';

-- Migrate 'technology' to 'tech' in topics
UPDATE topics SET category = 'tech' WHERE category = 'technology';

-- Enable Gemini, disable Ollama
UPDATE ai_providers SET enabled = true, priority = 100 WHERE name = 'Gemini';
UPDATE ai_providers SET enabled = false WHERE name = 'Ollama';
UPDATE ai_providers SET enabled = true, priority = 80 WHERE name = 'Claude';

-- Reset failed topics for a clean run
UPDATE topics SET status = 'developing', overall_sentiment = NULL WHERE status = 'analysis_failed';
