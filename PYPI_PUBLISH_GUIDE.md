# 🚀 Publishing GitLeague Client to PyPI

This guide walks you through publishing the `gitleague-client` package to PyPI (Python Package Index) so users can install it with a simple `pip install gitleague-client`.

## Overview

The package is already built and ready. You just need to:
1. Create a PyPI account and API token
2. Configure your credentials
3. Upload the package to PyPI
4. Verify the publication

**Total time:** ~10 minutes

---

## Step 1: Create a PyPI Account

1. Go to [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. Fill in the registration form:
   - **Username**: Choose a unique username (e.g., `boblebol`)
   - **Email**: Your email address
   - **Password**: Strong password
3. Verify your email
4. Enable 2FA (highly recommended):
   - Log in to [pypi.org](https://pypi.org)
   - Go to **Account settings** → **2-Factor Authentication**
   - Choose "Trusted Publishing" or "WebAuthn" (WebAuthn recommended for security)

---

## Step 2: Create an API Token

1. Log in to [https://pypi.org/account/](https://pypi.org/account/)
2. Go to **API tokens**
3. Click **"Add API token"**
4. Configure the token:
   - **Token name**: `gitleague-client-release` (or any descriptive name)
   - **Scope**: "Entire account" (or "Only this project" if you already have the project)
   - Click **"Create token"**
5. **Copy the token immediately** — PyPI only shows it once!
   - Format: `pypi-AgEIcHlwaS5vcmc...` (long string)
   - Save it securely

**⚠️ Important:** Treat this token like a password. Don't commit it to Git or share it.

---

## Step 3: Configure Credentials

### Option A: Using .pypirc (Recommended for Manual Publishing)

Create `~/.pypirc` (in your home directory):

```ini
[distutils]
index-servers =
    pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc... (paste your token here)
```

**Security note:** This file contains your token. Make sure it's readable only by you:
```bash
chmod 600 ~/.pypirc
```

### Option B: Using Environment Variable

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...
```

Then run `twine upload` commands.

### Option C: Using GitHub Actions (For CI/CD)

If you want to automate releases via GitHub:
1. Go to your GitHub repository settings
2. **Secrets and variables** → **Actions**
3. Create two secrets:
   - `PYPI_USERNAME` = `__token__`
   - `PYPI_PASSWORD` = `pypi-AgEIcHlwaS5vcmc...`
4. Add a workflow file (see CI/CD section below)

---

## Step 4: Upload to PyPI

### Prerequisites

Make sure you have the necessary tools:

```bash
pip install twine build
```

### Build the Package

```bash
cd /Users/alexandre/Projects/TheGitLeague/gitleague-client
python -m build
```

This creates:
- `dist/gitleague_client-0.1.0-py3-none-any.whl` (wheel)
- `dist/gitleague_client-0.1.0.tar.gz` (source distribution)

### Upload with Twine

Using `.pypirc` configuration:

```bash
twine upload dist/*
```

Or using environment variables:

```bash
twine upload dist/* \
  -u __token__ \
  -p "pypi-AgEIcHlwaS5vcmc..."
```

### What You'll See

```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading gitleague_client-0.1.0-py3-none-any.whl
[████████████████████] 100%
Uploading gitleague_client-0.1.0.tar.gz
[████████████████████] 100%

View at:
https://pypi.org/project/gitleague-client/0.1.0/
```

---

## Step 5: Verify the Publication

### Check PyPI

1. Visit: https://pypi.org/project/gitleague-client/
2. Verify that version `0.1.0` is listed
3. Check that the README and metadata display correctly

### Test Installation

In a **new virtual environment**:

```bash
# Create a temporary directory
mkdir /tmp/test-gitleague
cd /tmp/test-gitleague

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install the package from PyPI
pip install gitleague-client

# Test the CLI
gitleague-client --version
gitleague-client init --help
```

If everything works, you're done! 🎉

---

## Troubleshooting

### "Invalid authentication"

- Check that your token is correct (no extra spaces or quotes)
- Verify `.pypirc` has correct format
- Ensure `username = __token__` (literally `__token__`, not your username)

### "File already exists"

PyPI doesn't allow re-uploading the same version. To publish a new version:

1. Update the version in `pyproject.toml`:
   ```toml
   version = "0.2.0"  # Bump the version
   ```

2. Commit and tag:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 0.2.0"
   git tag v0.2.0
   git push origin main --tags
   ```

3. Rebuild and upload:
   ```bash
   rm -rf build/ dist/
   python -m build
   twine upload dist/*
   ```

### "404: Not Found"

- Make sure you're uploading to the correct index (https://upload.pypi.org/legacy/)
- Check the project name in `pyproject.toml` (`name = "gitleague-client"`)

---

## Future Releases

For subsequent releases, use semantic versioning:

- **Patch release** (0.1.1): Bug fixes
- **Minor release** (0.2.0): New features (backward compatible)
- **Major release** (1.0.0): Breaking changes

Workflow:
```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
# Commit and tag
git commit -am "Release: v0.2.0"
git tag v0.2.0
git push origin main --tags

# Build and publish
rm -rf dist/
python -m build
twine upload dist/*
```

---

## Automated Releases (Optional CI/CD Setup)

To automatically publish to PyPI when you create a GitHub release:

### 1. Create `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'  # Trigger on version tags like v0.1.0

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_PASSWORD }}
        run: twine upload dist/*
```

### 2. Add GitHub Secret

1. Go to repository Settings
2. **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. **Name**: `PYPI_PASSWORD`
5. **Value**: Your PyPI token (paste from Step 2)
6. Click **Add secret**

### 3. Create a Release

```bash
git tag v0.1.0
git push origin v0.1.0
```

Then create the release on GitHub — it will automatically publish to PyPI!

---

## PyPI Project Page Elements

After publication, users will see:

### PyPI Project Page
- https://pypi.org/project/gitleague-client/
- Shows version history, downloads, dependencies, etc.

### Package Download Stats
- Available in PyPI stats page
- Shows adoption and popularity

### Installation Command
```bash
pip install gitleague-client
```

---

## Next Steps

1. ✅ **Publish to PyPI** — Follow steps above
2. 📖 **Update Installation Guide** — Add PyPI installation method
3. 🗺️ **Update ROADMAP.md** — Mark publication as complete
4. 📣 **Announce** — Post on GitHub, Twitter, etc.

---

## Resources

- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)
- [PEP 427 - Wheel Format](https://peps.python.org/pep-0427/)

---

**Questions?** Check the [Main README](./README.md) or create an issue on GitHub.
