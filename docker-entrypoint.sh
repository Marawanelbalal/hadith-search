#!/bin/sh
set -e

DATA_DIR="/app/backend/data"

echo "=== Hadith Search Container ==="
echo "APP_MODE=${APP_MODE:-annotation}"
echo "PYTHONPATH=${PYTHONPATH:-/app/backend}"
echo ""

# Check for required data files
MISSING=""
if [ ! -f "$DATA_DIR/hadiths.db" ]; then
    MISSING="$MISSING  - hadiths.db"
fi
if [ ! -f "$DATA_DIR/queries.json" ]; then
    MISSING="$MISSING  - queries.json"
fi
if [ ! -f "$DATA_DIR/qrels_ungraded.json" ]; then
    MISSING="$MISSING  - qrels_ungraded.json"
fi

if [ -n "$MISSING" ]; then
    echo "WARNING: Missing data files in $DATA_DIR:"
    echo "$MISSING"
    echo ""
    echo "Mount the data volume and upload these files."
    if [ "$APP_MODE" = "annotation" ]; then
        echo "These files are required for the annotation platform."
    fi
    echo ""
fi

# For search/research modes, check for additional files
if [ "$APP_MODE" != "annotation" ]; then
    SEARCH_MISSING=""
    for f in english_embeddings.npy arabic_embeddings.npy \
             english_inverted_index.pkl arabic_inverted_index.pkl \
             document_lengths.pkl hadith_ids.npy; do
        if [ ! -f "$DATA_DIR/$f" ]; then
            SEARCH_MISSING="$SEARCH_MISSING  - $f"
        fi
    done
    if [ -n "$SEARCH_MISSING" ]; then
        echo "WARNING: Missing search data files (needed for APP_MODE=$APP_MODE):"
        echo "$SEARCH_MISSING"
        echo ""
    fi
fi

echo "Starting uvicorn..."
exec "$@"
