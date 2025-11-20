# GitHub Releases and Docker Hub Publishing

This document describes the automated release and Docker publishing workflows for the GradeSchoolMathSolver-RAG project.

## Overview

The project uses GitHub Actions to automate:
1. **Milestone-Based Tagging** - Automatically creates tags when milestones are closed
2. **GitHub Releases** - Automatically created when tags are pushed
3. **Docker Hub Publishing** - Multi-platform Docker images built and published on releases

## Workflows

### 1. Milestone Tag Workflow (`.github/workflows/milestone-tag.yml`)

**Trigger**: Closing a milestone with a properly formatted title

**What it does**:
- Automatically creates a git tag when a milestone is closed
- Parses milestone title to extract version information
- Supports three version formats with automatic normalization
- Skips tag creation if tag already exists or milestone doesn't match patterns

**Milestone Title Patterns**:

1. **Full Semantic Version**: `vx.x.x - [description]`
   - Example: `v1.2.3 - Feature Release` → Creates tag `v1.2.3`
   
2. **Minor Version**: `vx.x - [description]`
   - Example: `v1.2 - Minor Release` → Creates tag `v1.2.0`
   
3. **Major Version**: `vx - [description]`
   - Example: `v1 - Major Release` → Creates tag `v1.0.0`

**Non-matching milestones** (ignored):
- `Release 1.2.3` (missing 'v' prefix)
- `v1.2.3` (missing dash and description)
- `1.2.3 - Release` (missing 'v' prefix)
- `Milestone without version` (no version)

Once the tag is created, it automatically triggers the Release and Docker Publish workflows.

### 2. Release Workflow (`.github/workflows/release.yml`)

**What it does**:
- Uses `actions/github-script` to call GitHub's generateReleaseNotes API
- Automatically generates changelog from commit history and pull requests
- Creates a GitHub release using `actions/create-release@v1`
- Extracts version information from the tag
- Generates release description with installation instructions and auto-generated changelog
- Links to the Docker image on Docker Hub

**Trigger**: 
- Pushing semantic version tags (e.g., `v1.0.0`, `v2.1.3`) **on the default branch (main)**
- Automatically triggered by the Milestone Tag Workflow
- Tags not on the default branch will be skipped

**Example release notes include**:
- Auto-generated "What's Changed" section with PRs and commits
- Docker image pull command
- pip installation command
- Link to README for the specific version
- List of new contributors (if any)

### 2. Docker Hub Publish Workflow (`.github/workflows/docker-publish.yml`)

**What it does**:
- Builds multi-platform Docker images (linux/amd64, linux/arm64)
- Pushes multiple tags to Docker Hub:
  - `1.0.0` - Full version
  - `1.0` - Minor version
  - `1` - Major version
  - `latest` - Latest release
- Updates Docker Hub repository description from README.md using Docker Hub API directly
- Uses GitHub Actions cache for faster builds

**Trigger**: 
- Pushing semantic version tags (e.g., `v1.0.0`, `v2.1.3`) **on the default branch (main)**
- Automatically triggered by the Milestone Tag Workflow
- Tags not on the default branch will be skipped
- **Runs in the `prod` environment** (may require approval if environment protection rules are configured)

**Docker image metadata**:
- OCI-compliant labels for better discoverability
- Version, source, revision, and license information
- Proper title and description

**Security**:
- Uses Docker Hub API directly (no third-party actions)
- Credentials handled securely via GitHub Secrets
- JWT token-based authentication

## Setup Instructions

### Quick Validation

Before setting up, you can validate that all workflow files are properly configured:

```bash
./scripts/validate-release-setup.sh
```

This script checks:
- Workflow files exist and have valid YAML syntax
- Dockerfile is properly configured
- Documentation is in place
- Existing version tags

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

### Method 1: Using Milestones (Recommended)

This is the easiest and most organized way to create releases:

```bash
# 1. Create a milestone on GitHub with proper format
#    Title examples:
#    - "v1.0.0 - Initial Release"
#    - "v1.2 - Feature Updates"
#    - "v2 - Major Refactor"

# 2. Add issues to the milestone and complete them

# 3. Close the milestone when ready to release
#    This automatically creates the git tag and triggers the release workflows
```

The milestone title determines the tag:
- `v1.2.3 - Feature Release` → Tag `v1.2.3`
- `v1.2 - Minor Release` → Tag `v1.2.0`
- `v1 - Major Release` → Tag `v1.0.0`

### Method 2: Using Git Tags (Manual)

```bash
# Ensure you're on the main branch and up-to-date
git checkout main
git pull origin main

# Create and push a semantic version tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Method 3: Using GitHub Web Interface

1. Go to your repository on GitHub
2. Click on **Releases** → **Draft a new release**
3. Click **Choose a tag** → Type your new tag (e.g., `v1.0.0`)
4. Click **Create new tag on publish**
5. Fill in release title and description (optional - workflow will update)
6. Click **Publish release**

### What Happens Next

When you close a milestone with a matching pattern or push a tag matching `v*.*.*`:

> **Important**: Both the Release and Docker Publish workflows will only execute if the tag is on the default branch (main). Tags created on other branches will be ignored.

1. **Milestone Tag Workflow** triggers (if using milestone):
   - Parses milestone title
   - Creates appropriate git tag **on the main branch**
   - Takes ~10 seconds

2. **Release Workflow** triggers:
   - Verifies the tag is on the default branch (main)
   - Creates/updates GitHub release
   - Adds release notes and installation instructions
   - Takes ~30 seconds

3. **Docker Publish Workflow** triggers:
   - Verifies the tag is on the default branch (main)
   - Runs in the `prod` environment
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
docker pull yangzq50/gradeschoolmathsolver-rag:1.0.0

# Latest patch version
docker pull yangzq50/gradeschoolmathsolver-rag:1.0

# Latest minor version
docker pull yangzq50/gradeschoolmathsolver-rag:1

# Latest release
docker pull yangzq50/gradeschoolmathsolver-rag:latest
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

**Solution**: Check tag format and branch
- Must start with `v` (e.g., `v1.0.0`, not `1.0.0`)
- Must follow semantic versioning (three numbers)
- **Must be on the default branch (main)** - tags on other branches will be skipped
- Use `git tag -l` to verify tag exists
- Use `git branch -r --contains <tag>` to verify the tag is on main

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

1. Visit `https://hub.docker.com/r/<username>/gradeschoolmathsolver-rag`
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
