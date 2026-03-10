#!/bin/bash
set -e

# Ensure spaCy model is available on every startup
# This is fast if already cached — only downloads if missing
echo "Checking spaCy model 'en_core_web_sm'..."
python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || {
    echo "Model not found, downloading en_core_web_sm..."
    python -m spacy download en_core_web_sm --quiet
    echo "✓ spaCy model downloaded."
}
echo "✓ spaCy model ready."

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Run data initialization
echo "Initializing essential data..."
python init_all.py

# Hand off to the original container command
exec "$@"
