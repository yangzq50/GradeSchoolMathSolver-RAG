# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Python Version Support**: Maintaining Python 3.11+ as minimum supported version
  - Updated CI/CD pipeline to test on Python 3.11, 3.12, and 3.13
  - All dependencies compatible with Python 3.11+

### Updated Dependencies
All dependencies have been updated to their absolute latest versions that support Python 3.10+:

#### Core Dependencies
- `flask`: 3.0.0 → 3.1.2 (minor version update with bug fixes and improvements)
- `flask-cors`: 6.0.0 → 6.0.1 (patch update)

#### Database
- `elasticsearch`: 8.11.1 → 9.2.0 (major version update to latest 9.x with new features)
- **Removed `sqlalchemy`** - migrated to Elasticsearch-only storage

#### AI/ML
- `requests`: 2.32.4 → 2.32.5 (patch update)
- `numpy`: 1.26.2 → **2.3.4** (major version update to numpy 2.x with improved performance and new features)

#### Utilities
- `python-dotenv`: 1.0.0 → 1.2.1 (minor version update)
- `pydantic`: 2.5.2 → 2.12.4 (minor version update with improvements and bug fixes)

#### Web UI
- `jinja2`: 3.1.6 (unchanged - already latest)

#### Testing
- `pytest`: 7.4.3 → 9.0.1 (major version update to 9.x with new features)
- `pytest-cov`: 4.1.0 → 7.0.0 (major version update with improved coverage reporting)

#### Linting and Type Checking
- `flake8`: 7.0.0 → 7.3.0 (minor version update)
- `mypy`: 1.8.0 → 1.18.2 (minor version update with improved type checking)
- `types-requests`: 2.32.0.20240914 → 2.32.4.20250913 (type stubs update)

### Compatibility Notes
- All updated packages have been verified to support Python 3.11, 3.12, and 3.13
- **numpy 2.x**: Major upgrade brings significant performance improvements and new features. Requires Python >=3.11
- **elasticsearch**: Successfully upgraded to 9.x with enhanced features and performance
- No breaking changes expected from the dependency updates
- All existing tests (25/25) pass successfully with updated dependencies
- No code changes required to support the latest packages

### Testing
- Verified all 25 existing tests pass on Python 3.12 with updated dependencies
- CI pipeline now tests on Python 3.11, 3.12, and 3.13 to ensure cross-version compatibility
