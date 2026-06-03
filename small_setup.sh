#!/bin/bash

set -e

echo "==================================="
echo "Setting up project..."
echo "==================================="

# ------------------------------------------------------------
# Detect project/package name
# ------------------------------------------------------------

PROJECT_NAME=$(basename "$PWD")
PACKAGE_NAME=$(echo "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | tr '-' '_')

echo ""
echo "Project name detected: $PROJECT_NAME"
echo "Package name: $PACKAGE_NAME"

# ------------------------------------------------------------
# Create pyproject.toml
# ------------------------------------------------------------

if [ ! -f pyproject.toml ]; then

cat > pyproject.toml <<EOF
[project]
name = "$PACKAGE_NAME"
version = "0.1.0"
requires-python = ">=3.10"
EOF

echo ""
echo "Created pyproject.toml"

else
    echo ""
    echo "pyproject.toml already exists"
fi

# ------------------------------------------------------------
# Create requirements.txt
# ------------------------------------------------------------

if [ ! -f requirements.txt ]; then

cat > requirements.txt <<EOF
requests
python-dotenv
pytest
SQLAlchemy
EOF

echo ""
echo "Created requirements.txt"

else
    echo ""
    echo "requirements.txt already exists"
fi

# ------------------------------------------------------------
# Create virtual environment
# ------------------------------------------------------------

echo ""
echo "Creating virtual environment..."

python3 -m venv .venv

# ------------------------------------------------------------
# Upgrade pip
# ------------------------------------------------------------

echo ""
echo "Upgrading pip..."

.venv/bin/pip install --upgrade pip

# ------------------------------------------------------------
# Install dependencies
# ------------------------------------------------------------

echo ""
echo "Installing dependencies..."

.venv/bin/pip install -r requirements.txt

# ------------------------------------------------------------
# Install project in editable mode
# ------------------------------------------------------------

echo ""
echo "Installing project in editable mode..."

.venv/bin/pip install -e .

# ------------------------------------------------------------
# Finished
# ------------------------------------------------------------

echo ""
echo "==================================="
echo "Setup completed successfully."
echo "==================================="

echo ""
echo "Activate the virtual environment with:"
echo "source .venv/bin/activate"