#!/bin/bash
# Validation script for GitHub Release and Docker Hub publishing workflows
# This script helps verify that workflows are properly configured

set -e

echo "🔍 Validating GitHub Release and Docker Hub Publishing Setup"
echo "============================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Git repository found${NC}"

# Check if workflows exist
echo ""
echo "📋 Checking workflow files..."
WORKFLOWS_OK=true

if [ -f ".github/workflows/release.yml" ]; then
    echo -e "${GREEN}✅ release.yml found${NC}"
else
    echo -e "${RED}❌ release.yml not found${NC}"
    WORKFLOWS_OK=false
fi

if [ -f ".github/workflows/docker-publish.yml" ]; then
    echo -e "${GREEN}✅ docker-publish.yml found${NC}"
else
    echo -e "${RED}❌ docker-publish.yml not found${NC}"
    WORKFLOWS_OK=false
fi

if [ "$WORKFLOWS_OK" = false ]; then
    echo -e "${RED}❌ One or more workflow files are missing${NC}"
    exit 1
fi

# Validate YAML syntax
echo ""
echo "🔍 Validating YAML syntax..."
if command -v python3 &> /dev/null; then
    if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))" 2>/dev/null; then
        echo -e "${GREEN}✅ release.yml is valid YAML${NC}"
    else
        echo -e "${RED}❌ release.yml has YAML syntax errors${NC}"
        exit 1
    fi
    
    if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/docker-publish.yml'))" 2>/dev/null; then
        echo -e "${GREEN}✅ docker-publish.yml is valid YAML${NC}"
    else
        echo -e "${RED}❌ docker-publish.yml has YAML syntax errors${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Python3 not found - skipping YAML validation${NC}"
fi

# Check Dockerfile
echo ""
echo "🐳 Checking Dockerfile..."
if [ -f "Dockerfile" ]; then
    echo -e "${GREEN}✅ Dockerfile found${NC}"
    
    # Check for multi-stage build
    if grep -q "^FROM.*AS" Dockerfile; then
        echo -e "${GREEN}✅ Multi-stage build detected${NC}"
    else
        echo -e "${YELLOW}⚠️  No multi-stage build found (recommended for optimization)${NC}"
    fi
    
    # Check for EXPOSE
    if grep -q "^EXPOSE" Dockerfile; then
        echo -e "${GREEN}✅ EXPOSE instruction found${NC}"
    else
        echo -e "${YELLOW}⚠️  No EXPOSE instruction found${NC}"
    fi
    
    # Check for CMD or ENTRYPOINT
    if grep -q "^CMD\|^ENTRYPOINT" Dockerfile; then
        echo -e "${GREEN}✅ CMD/ENTRYPOINT found${NC}"
    else
        echo -e "${RED}❌ No CMD or ENTRYPOINT found${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Dockerfile not found${NC}"
    exit 1
fi

# Check for documentation
echo ""
echo "📚 Checking documentation..."
if [ -f "docs/RELEASE_WORKFLOW.md" ]; then
    echo -e "${GREEN}✅ RELEASE_WORKFLOW.md found${NC}"
else
    echo -e "${YELLOW}⚠️  RELEASE_WORKFLOW.md not found${NC}"
fi

# Check README for Docker Hub and release information
if [ -f "README.md" ]; then
    echo -e "${GREEN}✅ README.md found${NC}"
    
    if grep -q "Docker Hub" README.md || grep -q "docker pull" README.md; then
        echo -e "${GREEN}✅ Docker Hub information in README${NC}"
    else
        echo -e "${YELLOW}⚠️  No Docker Hub information in README${NC}"
    fi
    
    if grep -q "Release" README.md || grep -q "release" README.md; then
        echo -e "${GREEN}✅ Release information in README${NC}"
    else
        echo -e "${YELLOW}⚠️  No release information in README${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  README.md not found${NC}"
fi

# Check git tags
echo ""
echo "🏷️  Checking existing tags..."
TAGS=$(git tag -l 'v*.*.*' 2>/dev/null | wc -l)
if [ "$TAGS" -gt 0 ]; then
    echo -e "${GREEN}✅ Found $TAGS semantic version tags${NC}"
    echo "   Latest tags:"
    git tag -l 'v*.*.*' | tail -5 | sed 's/^/   - /'
else
    echo -e "${YELLOW}⚠️  No semantic version tags found (this is normal for new repositories)${NC}"
fi

# Summary and next steps
echo ""
echo "============================================================="
echo -e "${GREEN}✨ Validation complete!${NC}"
echo ""
echo "📝 Next Steps:"
echo "   1. Ensure GitHub Secrets are configured:"
echo "      - DOCKERHUB_USERNAME"
echo "      - DOCKERHUB_TOKEN"
echo "   2. Create a release by pushing a tag:"
echo "      git tag -a v1.0.0 -m 'Release version 1.0.0'"
echo "      git push origin v1.0.0"
echo "   3. Monitor the workflow runs in the Actions tab"
echo "   4. Check Docker Hub for the published image"
echo ""
echo "📖 For detailed instructions, see docs/RELEASE_WORKFLOW.md"
echo "============================================================="
