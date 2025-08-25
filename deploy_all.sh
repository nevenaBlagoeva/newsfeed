#!/usr/bin/env bash
set -euo pipefail

# --------------------------
# Configuration
# --------------------------
ARTIFACT_BUCKET="newsfeed-lambda-artifacts"
LAMBDAS=("fetcher" "filter" "ingest" "ingest_api" "retrieve")
BUILD_DIR=".build"
REQUIRED_PACKAGES=("praw" "pydantic" "feedparser")  # removed openai

# Export dependencies from Poetry
REQ_FILE="requirements.txt"
poetry export -f requirements.txt --output "$REQ_FILE" --without-hashes

# Ensure S3 bucket exists
aws s3api head-bucket --bucket "$ARTIFACT_BUCKET" 2>/dev/null || \
  aws s3 mb "s3://$ARTIFACT_BUCKET"

# Clean build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# --------------------------
# Package each Lambda
# --------------------------
for LAMBDA in "${LAMBDAS[@]}"; do
  echo "======================================"
  echo "📦 Packaging Lambda: $LAMBDA"

  ZIP_DIR="$BUILD_DIR/$LAMBDA"
  PKG_DIR="$ZIP_DIR/pkg"
  ZIPFILE="$ZIP_DIR/newsfeed-${LAMBDA}.zip"

  rm -rf "$PKG_DIR" "$ZIP_DIR"
  mkdir -p "$PKG_DIR"
  mkdir -p "$ZIP_DIR"

  # --------------------------
  # Install dependencies locally into package folder
  # --------------------------
  pip install --upgrade pip
  pip install --target "$PKG_DIR" -r "$REQ_FILE"

  # Copy source code
  cp -r src/newsfeed "$PKG_DIR"

  # Ensure zip folder exists
  mkdir -p "$ZIP_DIR"

  # --------------------------
  # Create zip from PKG_DIR to ZIP_DIR
  # --------------------------
  (cd "$PKG_DIR" && zip -r "../newsfeed-${LAMBDA}.zip" . -x '__pycache__/*' '*.pyc')

  # Move zip to final location
  mv "$ZIP_DIR/newsfeed-${LAMBDA}.zip" "$ZIPFILE"

  # --------------------------
  # Verify required packages exist
  # --------------------------
  MISSING_PACKAGES=()
  for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if [ ! -d "$PKG_DIR/$pkg" ]; then
      MISSING_PACKAGES+=("$pkg")
    fi
  done

  if [ "${#MISSING_PACKAGES[@]}" -ne 0 ]; then
    echo "❌ Missing dependencies in $LAMBDA zip: ${MISSING_PACKAGES[*]}"
    exit 1
  fi

  # --------------------------
  # Upload zip to S3
  # --------------------------
  echo "☁️ Uploading $ZIPFILE to S3..."
  aws s3 cp "$ZIPFILE" "s3://$ARTIFACT_BUCKET/"
done

# --------------------------
# Run Terraform
# --------------------------
echo "======================================"
echo "🚀 Running Terraform to deploy Lambdas"
cd terraform
terraform init
terraform apply -auto-approve
cd -

echo "🎉 All Lambdas packaged, verified, uploaded, and deployed successfully!"
