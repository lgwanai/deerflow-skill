#!/bin/bash
# Package DeerFlow Skill into a distributable zip file
# Excludes all files/directories listed in .gitignore

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"
DATE=$(date +%Y%m%d)
ZIP_NAME="deerflow-skill-$DATE.zip"

cd "$PROJECT_ROOT"

mkdir -p "$DIST_DIR"

zip -r "$DIST_DIR/$ZIP_NAME" . \
    -x ".git/*" \
    -x ".gitignore" \
    -x "config.yaml" \
    -x "*/__pycache__/*" \
    -x "__pycache__/*" \
    -x "*.py[cod]" \
    -x "*.pyo" \
    -x "*\$py.class" \
    -x "*.so" \
    -x ".Python" \
    -x "build/*" \
    -x "develop-eggs/*" \
    -x "dist/*" \
    -x "downloads/*" \
    -x "eggs/*" \
    -x ".eggs/*" \
    -x "lib64/*" \
    -x "parts/*" \
    -x "sdist/*" \
    -x "var/*" \
    -x "wheels/*" \
    -x "*.egg-info/*" \
    -x ".installed.cfg" \
    -x "*.egg" \
    -x ".venv/*" \
    -x "venv/*" \
    -x "ENV/*" \
    -x ".idea/*" \
    -x ".vscode/*" \
    -x "*.swp" \
    -x "*.swo" \
    -x ".pytest_cache/*" \
    -x "*/.pytest_cache/*" \
    -x ".coverage" \
    -x "htmlcov/*" \
    -x ".tox/*" \
    -x ".nox/*" \
    -x "coverage.xml" \
    -x "*.cover" \
    -x ".hypothesis/*" \
    -x ".benchmarks/*" \
    -x "*/.benchmarks/*" \
    -x ".ruff_cache/*" \
    -x "*/.ruff_cache/*" \
    -x ".planning/*" \
    -x "*.log" \
    -x "logs/*" \
    -x ".env" \
    -x ".env.local" \
    -x ".DS_Store" \
    -x "Thumbs.db" \
    -x "checkpoints.db" \
    -x "memory.json" \
    -x "uploads/*" \
    -x ".claude/*"

echo ""
echo "Package created: $DIST_DIR/$ZIP_NAME"
echo "Size: $(du -h "$DIST_DIR/$ZIP_NAME" | cut -f1)"
echo ""
echo "Contents:"
unzip -l "$DIST_DIR/$ZIP_NAME" | tail -n +4 | head -20
echo "..."
echo "Total files: $(unzip -l "$DIST_DIR/$ZIP_NAME" | tail -1 | awk '{print $2}')"
