# PyPI Publishing Guide

This document explains how to configure and use the automated PyPI publishing workflow for the GradeSchoolMathSolver-RAG project.

## Overview

The project uses GitHub Actions to automatically build and publish Python packages to PyPI when semantic version tags are pushed. The workflow is defined in `.github/workflows/pypi-publish.yml`.

## Package Configuration

### pyproject.toml

The project uses `pyproject.toml` for all package configuration, following modern Python packaging standards (PEP 517/518). This replaces the older `setup.py` approach.

Key sections in `pyproject.toml`:

#### Build System
```toml
[build-system]
requires = ["setuptools>=69.0", "wheel"]
build-backend = "setuptools.build_meta"
```

This specifies that the package uses setuptools as the build backend.

#### Project Metadata
```toml
[project]
name = "gradeschoolmathsolver"
version = "1.0.0"
description = "An AI-powered Grade School Math Solver with RAG"
readme = "README.md"
authors = [{name = "yangzq50"}]
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "flask==3.1.2",
    # ... other dependencies
]
```

**Important**: The version in `pyproject.toml` is automatically updated to match the git tag during the release workflow.

#### Package Discovery
```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["gradeschoolmathsolver*"]
exclude = ["tests*"]
```

This tells setuptools to automatically find all packages under `gradeschoolmathsolver/`.

#### Console Scripts
```toml
[project.scripts]
gradeschoolmathsolver = "gradeschoolmathsolver.web_ui.app:main"
```

This creates the `gradeschoolmathsolver` command-line tool.

### MANIFEST.in

The `MANIFEST.in` file specifies additional files to include in the distribution:

```
include README.md
include LICENSE
include requirements.txt
include .env.example
recursive-include gradeschoolmathsolver/web_ui/templates *.html
recursive-include docs *.md
```

## Setting Up PyPI Publishing

### Prerequisites

1. A PyPI account (create at https://pypi.org/)
2. Access to the GitHub repository settings
3. Permission to configure the "prod" environment in GitHub

### Step 1: Generate PyPI API Token

1. Log in to [PyPI](https://pypi.org/)
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Configure the token:
   - **Token name**: "GradeSchoolMathSolver GitHub Actions" (or similar)
   - **Scope**: 
     - For first release: "Entire account" (project doesn't exist yet)
     - After first release: Scope to "Project: gradeschoolmathsolver"
5. Click "Create token"
6. **IMPORTANT**: Copy the token immediately (it starts with `pypi-`)
   - You won't be able to see it again!

### Step 2: Add Token to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Configure the secret:
   - **Name**: `PYPI_TOKEN`
   - **Value**: Paste the PyPI token you copied
5. Click "Add secret"

### Step 3: Configure Production Environment

The workflow uses the "prod" environment for additional security:

1. Go to Settings → Environments
2. Create a new environment named "prod" (if it doesn't exist)
3. Optionally configure protection rules:
   - **Required reviewers**: Add team members who must approve releases
   - **Wait timer**: Add a delay before deployment
   - **Deployment branches**: Limit to specific branches (e.g., main)

## Publishing a Release

### Creating a Release

To publish a new version to PyPI:

1. **Update the version** (optional - the workflow does this automatically):
   ```bash
   # Edit pyproject.toml manually or let the workflow handle it
   ```

2. **Commit all changes** to the main branch:
   ```bash
   git add .
   git commit -m "Prepare for release v1.2.3"
   git push origin main
   ```

3. **Create and push a semantic version tag**:
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

4. **Monitor the workflow**:
   - Go to Actions tab in GitHub
   - Find the "PyPI Publish" workflow run
   - Check the logs for any errors

### What Happens Automatically

When you push a tag matching `v*.*.*`, the workflow:

1. **Verification Job**:
   - Checks out the code
   - Verifies the tag is on the default branch
   - Extracts the version from the tag

2. **Build Package Job**:
   - Updates the version in `pyproject.toml` to match the tag
   - Uses `python -m build` to build both:
     - Source distribution (`.tar.gz`)
     - Universal wheel (`.whl`) - works on all platforms and Python versions (3.11+)
   - Uploads distribution artifacts

3. **Publish Job**:
   - Downloads all build artifacts
   - Publishes to PyPI using `pypa/gh-action-pypi-publish` with the `PYPI_TOKEN` secret

**Note**: This package is pure Python with no compiled extensions, so a single universal wheel works across all platforms and Python versions. This simplifies the build process and reduces build time significantly.

### Workflow Environment

The publish job runs in the "prod" environment, which means:
- It requires the "prod" environment to be configured
- Any protection rules apply (e.g., required approvals)
- Environment-specific secrets are available

## Local Testing

### Building Locally

Test the build process before pushing a tag:

```bash
# Install build tools
pip install build

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the package (source distribution and universal wheel)
python -m build

# Check the output
ls -lh dist/
```

You should see:
- `gradeschoolmathsolver-X.Y.Z.tar.gz` (source distribution)
- `gradeschoolmathsolver-X.Y.Z-py3-none-any.whl` (universal wheel for pure Python packages)

### Validating the Package

Check the package for issues:

```bash
# Install check tools
pip install twine

# Check distributions
twine check dist/*

# List package contents
tar -tzf dist/gradeschoolmathsolver-*.tar.gz | head -20
unzip -l dist/gradeschoolmathsolver-*.whl | head -20
```

### Testing Installation

Install the package locally:

```bash
# Install from wheel
pip install dist/gradeschoolmathsolver-*.whl

# Or install in development mode
pip install -e .

# Test the command
gradeschoolmathsolver --help
```

### Publishing to TestPyPI (Optional)

Test the entire publishing process with TestPyPI:

1. Create a TestPyPI account at https://test.pypi.org/
2. Generate an API token
3. Upload to TestPyPI:
   ```bash
   twine upload --repository testpypi dist/*
   ```
4. Test installation:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ gradeschoolmathsolver
   ```

## Updating Package Configuration

### Adding Dependencies

Edit `pyproject.toml`:

```toml
dependencies = [
    "flask==3.1.2",
    "new-package>=1.0.0",  # Add new dependency
    ...
]
```

### Updating Metadata

Edit the `[project]` section in `pyproject.toml`:

```toml
[project]
name = "gradeschoolmathsolver"
version = "1.0.0"
description = "Updated description"
authors = [
    {name = "yangzq50"},
    {name = "New Contributor", email = "contributor@example.com"}
]
```

### Adding Optional Dependencies

For development or optional features:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=9.0.1",
    "flake8>=7.3.0",
]
docs = [
    "sphinx>=7.0.0",
    "sphinx-rtd-theme>=1.0.0",
]
```

Users can install with: `pip install gradeschoolmathsolver[dev]`

### Adding Console Scripts

To add new command-line tools:

```toml
[project.scripts]
gradeschoolmathsolver = "gradeschoolmathsolver.web_ui.app:main"
gsm-cli = "gradeschoolmathsolver.cli:main"  # New command
```

## Troubleshooting

### Package Not Found on PyPI

After publishing, it may take a few minutes for the package to appear on PyPI:
- Check the workflow logs for errors
- Visit https://pypi.org/project/gradeschoolmathsolver/
- Verify the `PYPI_TOKEN` secret is correct

### Permission Denied

If the workflow fails with a permission error:
1. Check the `PYPI_TOKEN` secret is set correctly
2. Verify the token has the correct scope
3. For first release, use "Entire account" scope
4. After first release, scope token to the specific project

### Version Conflict

If you see "File already exists" error:
- PyPI doesn't allow re-uploading the same version
- You must increment the version number
- Delete the tag locally and remotely, fix the version, and re-tag

```bash
# Delete tag locally
git tag -d v1.0.0

# Delete tag remotely
git push --delete origin v1.0.0

# Create new tag with incremented version
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin v1.0.1
```

### Build Failures

If the build fails:
1. Test locally first: `python -m build`
2. Check `pyproject.toml` syntax
3. Ensure all required files are present
4. Verify package structure is correct
5. Check the GitHub Actions logs for specific error messages

### pypa/gh-action-pypi-publish Issues

If publishing fails:
1. Verify the `PYPI_TOKEN` secret is correctly set
2. Ensure artifacts were uploaded successfully in previous jobs
3. Check that the "prod" environment is configured
4. Review the publish job logs for specific errors

## Best Practices

1. **Always test locally** before pushing tags
2. **Use semantic versioning**: MAJOR.MINOR.PATCH
3. **Document changes** in release notes
4. **Scope PyPI tokens** to specific projects after first release
5. **Keep pyproject.toml updated** with accurate metadata
6. **Test in TestPyPI first** for major changes
7. **Never commit** PyPI tokens to the repository
8. **Use environment protection** rules for production releases

## References

- [Python Packaging User Guide](https://packaging.python.org/)
- [PEP 517 - Build System](https://peps.python.org/pep-0517/)
- [PEP 518 - pyproject.toml](https://peps.python.org/pep-0518/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [PyPI Help](https://pypi.org/help/)
