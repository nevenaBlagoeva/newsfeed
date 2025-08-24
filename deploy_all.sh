#!/usr/bin/env bash
set -euo pipefail

ARTIFACT_BUCKET="newsfeed-lambda-artifacts"
PYTHON_VERSION="python3.11"
LAMBDAS=("fetcher" "filter" "ingest" "ingest_api" "retrieve")
BUILD_DIR=".build"

echo "📦 Ensuring artifact bucket exists: $ARTIFACT_BUCKET"
aws s3api head-bucket --bucket "$ARTIFACT_BUCKET" 2>/dev/null || \
  aws s3 mb "s3://$ARTIFACT_BUCKET"

# Start fresh build dir
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

for LAMBDA in "${LAMBDAS[@]}"; do
  echo "======================================"
  echo "📦 Packaging Lambda: $LAMBDA"

  SRC_DIR="src/lambdas/$LAMBDA"
  ZIPFILE="newsfeed-${LAMBDA}.zip"
  PKG_DIR="${BUILD_DIR}/${LAMBDA}"

  if [ ! -d "$SRC_DIR" ]; then
    echo "❌ Skipping $LAMBDA (no folder $SRC_DIR)"
    continue
  fi

  # Fresh package dir
  rm -rf "$PKG_DIR"
  mkdir -p "$PKG_DIR"

  # Copy lambda source
  cp -r "$SRC_DIR"/* "$PKG_DIR"/

  # Copy shared
  mkdir -p "$PKG_DIR/shared"
  cp -r src/shared/* "$PKG_DIR/shared"/
  touch "$PKG_DIR/shared/__init__.py"

  # Install dependencies
  if [ -f "$SRC_DIR/requirements.txt" ]; then
    pip install -r "$SRC_DIR/requirements.txt" -t "$PKG_DIR"
  fi

  # Create zip from pkg dir
  (cd "$PKG_DIR" && zip -r "$ZIPFILE" . -x "__pycache__/*" "*.pyc")

  echo "✅ Built $ZIPFILE"

  echo "☁️ Uploading to S3"
  aws s3 cp "$BUILD_DIR/$LAMBDA/$ZIPFILE" "s3://$ARTIFACT_BUCKET/$ZIPFILE"
done

echo "======================================"
echo "🚀 Running Terraform"
cd terraform
terraform init
terraform apply -auto-approve
cd -

echo "🎉 All Lambdas deployed successfully!"
