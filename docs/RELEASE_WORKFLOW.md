# GitHub Releases and Docker Hub Publishing

This document describes the automated release and Docker publishing workflows for the GradeSchoolMathSolver-RAG project.

## Overview

The project uses GitHub Actions to automate:
1. **GitHub Releases** - Automatically created when tags are pushed
2. **Docker Hub Publishing** - Multi-platform Docker images built and published on releases

## Workflows

### 1. Release Workflow (`.github/workflows/release.yml`)

**Trigger**: Pushing semantic version tags (e.g., `v1.0.0`, `v2.1.3`)

**What it does**:
- Creates a GitHub release with auto-generated release notes
- Extracts version information from the tag
- Generates release description with installation instructions
- Links to the Docker image on Docker Hub

**Example release notes include**:
- What's Changed section with changelog link
- Docker image pull command
- pip installation command
- Link to README for the specific version

### 2. Docker Hub Publish Workflow (`.github/workflows/docker-publish.yml`)

**Trigger**: Pushing semantic version tags (e.g., `v1.0.0`, `v2.1.3`)

**What it does**:
- Builds multi-platform Docker images (linux/amd64, linux/arm64)
- Pushes multiple tags to Docker Hub:
  - `1.0.0` - Full version
  - `1.0` - Minor version
  - `1` - Major version
  - `latest` - Latest release
- Updates Docker Hub repository description from README.md
- Uses GitHub Actions cache for faster builds

**Docker image metadata**:
- OCI-compliant labels for better discoverability
- Version, source, revision, and license information
- Proper title and description

## Setup Instructions

### Prerequisites

1. **Docker Hub Account**: You need a Docker Hub account to publish images
2. **Repository Access**: Admin access to the GitHub repository to set up secrets

### Step 1: Create Docker Hub Access Token

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Go to **Account Settings** → **Security** → **New Access Token**
3. Create a token with **Read, Write, Delete** permissions
4. Save the token securely (you won't be able to see it again)

### Step 2: Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | `yangzq50` |
| `DOCKERHUB_TOKEN` | Docker Hub access token from Step 1 | `dckr_pat_...` |

### Step 3: Verify Dockerfile

Ensure your `Dockerfile` is properly configured:
- ✅ Multi-stage build for smaller images
- ✅ Proper base image selection
- ✅ Correct EXPOSE port
- ✅ Health check configured
- ✅ Entry point defined

The existing `Dockerfile` already meets these requirements.

## Creating a Release

### Method 1: Using Git Tags (Recommended)

```bash
# Ensure you're on the main branch and up-to-date
git checkout main
git pull origin main

# Create and push a semantic version tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Method 2: Using GitHub Web Interface

1. Go to your repository on GitHub
2. Click on **Releases** → **Draft a new release**
3. Click **Choose a tag** → Type your new tag (e.g., `v1.0.0`)
4. Click **Create new tag on publish**
5. Fill in release title and description (optional - workflow will update)
6. Click **Publish release**

### What Happens Next

When you push a tag matching `v*.*.*`:

1. **Release Workflow** triggers:
   - Creates/updates GitHub release
   - Adds release notes and installation instructions
   - Takes ~30 seconds

2. **Docker Publish Workflow** triggers:
   - Builds Docker images for multiple platforms
   - Pushes to Docker Hub with multiple tags
   - Updates Docker Hub description
   - Takes ~5-10 minutes (first build), ~2-3 minutes (subsequent builds with cache)

## Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.x.x): Incompatible API changes
- **MINOR** version (x.1.x): New features (backward compatible)
- **PATCH** version (x.x.1): Bug fixes (backward compatible)

### Version Bumping Guidelines

- **Patch** (v1.0.0 → v1.0.1): Bug fixes, documentation updates
- **Minor** (v1.0.0 → v1.1.0): New features, enhancements
- **Major** (v1.0.0 → v2.0.0): Breaking changes, major refactoring

## Docker Image Tags

For a release `v1.2.3`, the following tags are created:

| Tag | Description | Use Case |
|-----|-------------|----------|
| `1.2.3` | Specific version | Production use, reproducible builds |
| `1.2` | Latest patch of v1.2 | Auto-update to latest patch |
| `1` | Latest minor of v1 | Auto-update to latest minor |
| `latest` | Latest release | Development, testing |

### Pulling Docker Images

```bash
# Specific version (recommended for production)
docker pull yangzq50/gradeschoolmathsolver:1.0.0

# Latest patch version
docker pull yangzq50/gradeschoolmathsolver:1.0

# Latest minor version
docker pull yangzq50/gradeschoolmathsolver:1

# Latest release
docker pull yangzq50/gradeschoolmathsolver:latest
```

## Customization

### Changing Docker Image Name

Edit `.github/workflows/docker-publish.yml`:

```yaml
env:
  DOCKER_IMAGE_NAME: your-custom-name  # Change this
```

### Changing Tag Pattern

Edit both workflow files to change the tag pattern:

```yaml
on:
  push:
    tags:
      - 'v*.*.*'  # Change this pattern
```

### Adding More Platforms

Edit `.github/workflows/docker-publish.yml`:

```yaml
platforms: linux/amd64,linux/arm64,linux/arm/v7  # Add more platforms
```

### Modifying Release Notes Template

Edit `.github/workflows/release.yml` in the "Create GitHub Release" step:

```yaml
body: |
  ## What's Changed
  # Add your custom template here
```

## Troubleshooting

### Build Fails: "denied: requested access to the resource is denied"

**Solution**: Verify Docker Hub credentials in GitHub Secrets
- Check `DOCKERHUB_USERNAME` is correct
- Verify `DOCKERHUB_TOKEN` is valid and has Read/Write/Delete permissions
- Ensure the token hasn't expired

### Build is Slow

**Solution**: The workflow uses GitHub Actions cache
- First build: ~5-10 minutes (no cache)
- Subsequent builds: ~2-3 minutes (with cache)
- Cache is automatically managed

### Release Not Created

**Solution**: Check tag format
- Must start with `v` (e.g., `v1.0.0`, not `1.0.0`)
- Must follow semantic versioning (three numbers)
- Use `git tag -l` to verify tag exists

### Multi-platform Build Fails

**Solution**: 
- QEMU and Buildx are automatically set up
- ARM builds may take longer than AMD builds
- Check GitHub Actions logs for specific platform errors

## Monitoring

### Checking Workflow Status

1. Go to **Actions** tab in your GitHub repository
2. View workflow runs for each release
3. Click on a run to see detailed logs

### Verifying Docker Hub Publication

1. Visit `https://hub.docker.com/r/<username>/gradeschoolmathsolver`
2. Check **Tags** tab for new version tags
3. Verify **Overview** tab description matches README.md

## Best Practices

1. **Test Before Release**: Always test your changes before creating a release tag
2. **Use Pre-releases**: For testing, create pre-release tags (e.g., `v1.0.0-beta.1`)
3. **Semantic Versioning**: Follow semantic versioning strictly
4. **Changelog**: Maintain a CHANGELOG.md file for detailed release notes
5. **Security**: Never commit Docker Hub credentials to the repository
6. **Tag Protection**: Consider protecting release tags in GitHub settings

## Security Considerations

- Docker Hub tokens are stored securely in GitHub Secrets
- Tokens are never exposed in logs or outputs
- Use scoped tokens with minimal necessary permissions
- Rotate tokens periodically (recommended every 6-12 months)
- Enable two-factor authentication on Docker Hub

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [Semantic Versioning Specification](https://semver.org/)
- [Docker Build and Push Action](https://github.com/docker/build-push-action)
- [OCI Image Spec](https://github.com/opencontainers/image-spec/blob/main/annotations.md)
