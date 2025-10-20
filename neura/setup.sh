#!/bin/bash
# Setup script for Neura development environment

set -e

echo "🧠 Setting up Neura Development Environment"
echo "==========================================="

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Check Poetry
echo -e "\n${BLUE}Checking Poetry installation...${NC}"
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Poetry not found. Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    echo -e "${GREEN}✓ Poetry installed${NC}"
    echo -e "${YELLOW}⚠ Please add Poetry to your PATH and restart your shell${NC}"
    echo -e "  Add this to your ~/.zshrc or ~/.bashrc:"
    echo -e "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    exit 0
else
    echo -e "${GREEN}✓ Poetry found${NC}"
fi

# Install dependencies
echo -e "\n${BLUE}Installing dependencies...${NC}"
poetry install --no-root

# Create necessary directories
echo -e "\n${BLUE}Creating directories...${NC}"
mkdir -p data logs neura_vault
echo -e "${GREEN}✓ Directories created${NC}"

# Copy environment file
echo -e "\n${BLUE}Setting up environment...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env with your configuration${NC}"
else
    echo -e "${YELLOW}⚠ .env already exists, skipping${NC}"
fi

# Setup pre-commit hooks (if available)
if command -v poetry &> /dev/null; then
    echo -e "\n${BLUE}Setting up pre-commit hooks...${NC}"
    poetry run pre-commit install || echo -e "${YELLOW}⚠ pre-commit setup skipped${NC}"
fi

echo -e "\n${GREEN}========================================="
echo -e "✓ Neura setup complete!${NC}"
echo -e "\nNext steps:"
echo -e "  1. Edit .env if needed"
echo -e "  2. Run ${BLUE}make test${NC} to verify installation"
echo -e "  3. Run ${BLUE}make run${NC} to start the API"
echo -e "  4. Visit http://localhost:8000"
echo -e "\nFor all commands, run: ${BLUE}make help${NC}"
