#!/bin/bash
# simulate-ci.sh - Validate local development environment
#
# This script validates that your local development environment is properly set up
# and runs the same quality checks that CI will run, helping catch issues early.

set -euo pipefail

echo "🔍 Validating Local Development Environment..."
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    print_error "Must be run from the project root directory (where pyproject.toml is located)"
    exit 1
fi

# Step 1: Environment Validation
print_step "Validating Environment..."

# Check Python version (should match CI)
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
EXPECTED_PYTHON="3.13"
if [[ ! "$PYTHON_VERSION" =~ ^3\.13\. ]]; then
    print_error "Python version mismatch! Expected: $EXPECTED_PYTHON.x, Found: $PYTHON_VERSION"
    print_warning "Install Python 3.13.x to match CI environment"
    exit 1
fi
print_success "Python version: $PYTHON_VERSION (matches CI)"

# Check uv installation
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed! Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
UV_VERSION=$(uv --version | cut -d' ' -f2)
print_success "uv version: $UV_VERSION"

# Step 2: Validate Current Environment
print_step "Validating current development environment..."

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    print_error "Virtual environment not found! Run 'make setup' first."
    exit 1
fi

# Check if dependencies are installed
if ! uv run python -c "import pytest, pyright" 2>/dev/null; then
    print_error "Dependencies not installed! Run 'uv sync --dev' first."
    exit 1
fi

print_success "Development environment is properly set up"

print_success "Development environment setup complete"

# Step 4: Validate Dependencies
print_step "Validating dependencies..."

# Check that we're using the expected Python in venv
VENV_PYTHON_VERSION=$(uv run python --version 2>&1 | cut -d' ' -f2)
if [[ "$VENV_PYTHON_VERSION" != "$PYTHON_VERSION" ]]; then
    print_error "Virtual environment Python version mismatch! System: $PYTHON_VERSION, venv: $VENV_PYTHON_VERSION"
    exit 1
fi
print_success "Virtual environment Python: $VENV_PYTHON_VERSION"

# Check pyright version
PYRIGHT_VERSION=$(uv run pyright --version 2>&1 | cut -d' ' -f2)
print_success "Pyright version: $PYRIGHT_VERSION"

# Step 5: Run Quality Checks (same as CI)
print_step "Running quality checks..."

echo ""
echo "🧪 Running tests..."
if ! make test; then
    print_error "Tests failed! This will fail in CI."
    exit 1
fi
print_success "Tests passed"

echo ""
echo "🔍 Running type checking..."
if ! make type-check; then
    print_error "Type checking failed! This will fail in CI."
    exit 1
fi
print_success "Type checking passed"

echo ""
echo "🎨 Running linting..."
if ! make lint; then
    print_error "Linting failed! This will fail in CI."
    exit 1
fi
print_success "Linting passed"

# Step 6: Final Summary
echo ""
echo "================================================="
print_success "🎉 Environment Validation Complete!"
echo ""
echo -e "${GREEN}✅ All checks passed - your code will pass in GitHub Actions!${NC}"
echo ""
echo "Environment Details:"
echo "  - Python: $VENV_PYTHON_VERSION"
echo "  - Pyright: $PYRIGHT_VERSION"
echo "  - UV: $UV_VERSION"
echo ""
echo "To validate your environment regularly:"
echo "  ./scripts/simulate-ci.sh"
echo ""
echo "Or use the Makefile target:"
echo "  make simulate-ci"
