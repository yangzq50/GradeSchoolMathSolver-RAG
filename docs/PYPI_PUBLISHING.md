# PyPI Publishing Guide

This document explains how to configure and use the automated PyPI publishing workflow for the GradeSchoolMathSolver project.

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
where = ["src"]
include = ["gradeschoolmathsolver*"]
exclude = ["tests*"]
```

This tells setuptools to automatically find all packages under `src/gradeschoolmathsolver/`.

#### Package Data
```toml
[tool.setuptools.package-data]
gradeschoolmathsolver = ["web_ui/templates/*.html", "web_ui/templates/**/*.html"]
```

This ensures HTML templates are included in the package distribution.

#### Console Scripts
```toml
[project.scripts]
gradeschoolmathsolver = "gradeschoolmathsolver.web_ui.app:main"
```

This creates the `gradeschoolmathsolver` command-line tool.

### Legacy Files Removed

The project previously used `MANIFEST.in` for specifying package data. This has been replaced by the `[tool.setuptools.package-data]` section in `pyproject.toml`, which provides better integration with modern Python packaging standards.

All non-Python files (HTML templates, etc.) are now configured directly in `pyproject.toml`.

## Setting Up PyPI Publishing

### Prerequisites

1. A PyPI account (create at https://pypi.org/)
2. Access to the GitHub repository settings
3. Permission to configure the "prod" environment in GitHub

### Step 1: Configure PyPI Trusted Publishing (OIDC)

PyPI now supports **Trusted Publishing** using OpenID Connect (OIDC), which eliminates the need for API tokens and provides enhanced security through short-lived tokens.

1. Log in to [PyPI](https://pypi.org/)
2. Go to your **project page** (or Account Settings → Publishing for new projects)
3. Navigate to the **"Publishing"** section
4. Click **"Add a new publisher"**
5. Select **"GitHub Actions"** as the publisher type
6. Configure the publisher:
   - **Owner**: `yangzq50`
   - **Repository name**: `GradeSchoolMathSolver`
   - **Workflow name**: `pypi-publish.yml`
   - **Environment name**: `prod`
7. Click **"Add"**

**For first-time publishing**: If the project doesn't exist on PyPI yet, you can configure "Pending Publishers" under Account Settings → Publishing before the first release.

### Step 2: Configure Production Environment

The workflow uses the "prod" environment for additional security:

1. Go to Settings → Environments
2. Create a new environment named "prod" (if it doesn't exist)
3. Optionally configure protection rules:
   - **Required reviewers**: Add team members who must approve releases
   - **Wait timer**: Add a delay before deployment
   - **Deployment branches**: Limit to specific branches (e.g., main)

**Note**: No API tokens or secrets are needed with OIDC! GitHub automatically generates short-lived tokens during workflow execution.

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
   - Publishes to PyPI using `pypa/gh-action-pypi-publish` with **OIDC authentication**
   - No API tokens needed - GitHub automatically provides short-lived tokens

**Note**: This package is pure Python with no compiled extensions, so a single universal wheel works across all platforms and Python versions. This simplifies the build process and reduces build time significantly.

### Workflow Environment

The publish job runs in the "prod" environment, which means:
- It requires the "prod" environment to be configured
- Any protection rules apply (e.g., required approvals)
- OIDC authentication is used (no API tokens needed)

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
- Verify the Trusted Publisher is configured correctly on PyPI

### Permission Denied

If the workflow fails with a permission error:
1. Verify the Trusted Publisher is configured on PyPI with the correct repository details
2. Ensure the "prod" environment is configured in GitHub
3. Check that `id-token: write` permission is set in the workflow
4. For first release, configure "Pending Publishers" on PyPI before pushing the tag

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
1. Verify Trusted Publisher is configured correctly on PyPI
2. Ensure artifacts were uploaded successfully in previous jobs
3. Check that the "prod" environment is configured
4. Verify `id-token: write` permission is granted
5. Review the publish job logs for specific errors

## Best Practices

1. **Always test locally** before pushing tags
2. **Use semantic versioning**: MAJOR.MINOR.PATCH
3. **Document changes** in release notes
4. **Use OIDC Trusted Publishing** for enhanced security (no API tokens!)
5. **Keep pyproject.toml updated** with accurate metadata
6. **Test in TestPyPI first** for major changes
7. **Use environment protection** rules for production releases
8. **Configure protection rules** on the "prod" environment for additional security

## References

- [Python Packaging User Guide](https://packaging.python.org/)
- [PEP 517 - Build System](https://peps.python.org/pep-0517/)
- [PEP 518 - pyproject.toml](https://peps.python.org/pep-0518/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [PyPI Help](https://pypi.org/help/)
