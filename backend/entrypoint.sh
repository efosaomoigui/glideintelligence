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

# Run migrations and initialization only if RUN_INITIALIZATION is true
if [ "$RUN_INITIALIZATION" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head

    echo "Initializing essential data..."
    python init_all.py
else
    echo "Skipping initialization (RUN_INITIALIZATION not set to true)"
fi

# Hand off to the original container command
exec "$@"
