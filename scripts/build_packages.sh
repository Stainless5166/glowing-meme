#!/bin/bash
# Build Glowing Meme packages for the agent and monitor.
#
# Determines the version from git tags, updates packaging metadata, runs the
# test suite, and produces Arch Linux and Debian packages in dist/.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
DIST_DIR="$REPO_ROOT/dist"

cd "$REPO_ROOT"

# ---------------------------------------------------------------------------
# Version handling
# ---------------------------------------------------------------------------
GIT_DESCRIBE=$(git describe --tags --always --dirty 2>/dev/null || echo "0.0.0")
GIT_DESCRIBE=${GIT_DESCRIBE#v}

if [[ "$GIT_DESCRIBE" =~ ^([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    PEP440_VERSION="${BASH_REMATCH[1]}"
elif [[ "$GIT_DESCRIBE" =~ ^([0-9]+\.[0-9]+\.[0-9]+)-([0-9]+)-g([0-9a-f]+)$ ]]; then
    base="${BASH_REMATCH[1]}"
    count="${BASH_REMATCH[2]}"
    hash="${BASH_REMATCH[3]}"
    PEP440_VERSION="${base}.dev${count}+g${hash}"
else
    PEP440_VERSION="0.0.0+${GIT_DESCRIBE}"
fi

# Arch pkgver cannot contain '-' or '+'.
ARCH_VERSION=$(echo "$PEP440_VERSION" | tr '-' '.' | tr '+' '.')

# Debian version uses '~' for prereleases so they sort before the release.
DEB_VERSION="$PEP440_VERSION"
if [[ "$DEB_VERSION" == *+* ]]; then
    DEB_VERSION=$(echo "$DEB_VERSION" | sed 's/+/~/' )
fi

echo "Building Glowing Meme"
echo "  PEP 440 version: $PEP440_VERSION"
echo "  Arch pkgver:     $ARCH_VERSION"
echo "  Debian version:  $DEB_VERSION"

# ---------------------------------------------------------------------------
# Update source versions
# ---------------------------------------------------------------------------
sed -i "s/^__version__ = .*/__version__ = \"$PEP440_VERSION\"/" \
    src/glowing_meme/__init__.py
sed -i "s/^VERSION = .*/VERSION = \"$PEP440_VERSION\"/" \
    agent/agent.py

# ---------------------------------------------------------------------------
# Update packaging versions
# ---------------------------------------------------------------------------
sed -i "s/^pkgver=.*/pkgver=$ARCH_VERSION/" packaging/agent/PKGBUILD
sed -i "s/^pkgver=.*/pkgver=$ARCH_VERSION/" packaging/monitor/PKGBUILD

update_changelog() {
    local file=$1
    local pkg=$2
    local version=$3
    cat > "$file" <<EOF
$pkg ($version-1) unstable; urgency=medium

  * Build from $PEP440_VERSION.

 -- Glowing Meme Team <team@glowing-meme.invalid>  $(date -R)
EOF
}

update_changelog packaging/agent/debian/changelog glowing-meme-agent "$DEB_VERSION"
update_changelog packaging/monitor/debian/changelog glowing-meme-monitor "$DEB_VERSION"

# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------
echo "Running tests..."
make test

# ---------------------------------------------------------------------------
# Build monitor wheel
# ---------------------------------------------------------------------------
echo "Building monitor wheel..."
rm -rf dist
uv build --wheel

# ---------------------------------------------------------------------------
# Stage packaging sources
# ---------------------------------------------------------------------------
cp agent/agent.py packaging/agent/agent.py
cp agent/glowing-meme-agent.service packaging/agent/glowing-meme-agent.service

rm -f packaging/monitor/*.whl
WHEEL_FILE=$(basename dist/*.whl)
cp "dist/$WHEEL_FILE" "packaging/monitor/$WHEEL_FILE"
# Update PKGBUILD wheel variable to match the actual wheel filename.
sed -i "s|^_wheel=.*|_wheel=\"$WHEEL_FILE\"|" packaging/monitor/PKGBUILD

mkdir -p "$DIST_DIR"
rm -f "$DIST_DIR"/*

# ---------------------------------------------------------------------------
# Build Arch packages
# ---------------------------------------------------------------------------
echo "Building Arch agent package..."
cd packaging/agent
rm -f ./*.pkg.tar.zst
makepkg -sf --noconfirm
cp glowing-meme-agent-*.pkg.tar.zst "$DIST_DIR/"
cd "$REPO_ROOT"

echo "Building Arch monitor package..."
cd packaging/monitor
rm -f ./*.pkg.tar.zst
makepkg -sf --noconfirm
cp glowing-meme-monitor-*.pkg.tar.zst "$DIST_DIR/"
cd "$REPO_ROOT"

# ---------------------------------------------------------------------------
# Build Debian packages
# ---------------------------------------------------------------------------
echo "Building Debian agent package..."
cd packaging/agent
rm -f ../glowing-meme-agent_*.deb ../glowing-meme-agent_*.changes \
      ../glowing-meme-agent_*.buildinfo
dpkg-buildpackage -us -uc -b
cd "$REPO_ROOT"
cp packaging/glowing-meme-agent_*.deb "$DIST_DIR/"

echo "Building Debian monitor package..."
cd packaging/monitor
rm -f ../glowing-meme-monitor_*.deb ../glowing-meme-monitor_*.changes \
      ../glowing-meme-monitor_*.buildinfo
dpkg-buildpackage -us -uc -b
cd "$REPO_ROOT"
cp packaging/glowing-meme-monitor_*.deb "$DIST_DIR/"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "Artifacts in $DIST_DIR:"
ls -la "$DIST_DIR"
