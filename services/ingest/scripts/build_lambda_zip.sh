#!/usr/bin/env bash
set -euo pipefail

# Resolve the services/ingest directory no matter where the script is run from
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BUILD_DIR="$ROOT/.build/lambda"
DIST_DIR="$ROOT/dist"
ZIP_PATH="$DIST_DIR/ingest_lambda.zip"

rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

echo "Building Lambda deployment package..."
echo "Project root: $ROOT"
echo "Build dir:    $BUILD_DIR"
echo "Zip output:   $ZIP_PATH"

#install dependencies 
python -m pip install --upgrade pip
python -m pip install -r "$ROOT/requirements.txt" -t "$BUILD_DIR"

#copy source package
cp -R "$ROOT/src" "$BUILD_DIR/src"

#create the zip 
cd "$BUILD_DIR"
zip -r "$ZIP_PATH" .

echo "Done."
ls -lh "$ZIP_PATH"