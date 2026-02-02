#!/bin/bash
#
# Tomo - DEB Package Builder
#
# Usage:
#   ./build-deb.sh [VERSION] [RELEASE]
#
# Examples:
#   ./build-deb.sh                    # Uses version from VERSION file, release 1
#   ./build-deb.sh 1.0.0              # Version 1.0.0, release 1
#   ./build-deb.sh 1.0.0 2            # Version 1.0.0, release 2
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGE_NAME="tomo"
ARCH="amd64"

# Get version
if [ -n "$1" ]; then
    VERSION="$1"
elif [ -f "$PROJECT_ROOT/VERSION" ]; then
    VERSION=$(cat "$PROJECT_ROOT/VERSION")
else
    VERSION="1.0.0"
fi

RELEASE="${2:-1}"
FULL_VERSION="${VERSION}-${RELEASE}"
BUILD_DIR="$SCRIPT_DIR/build/${PACKAGE_NAME}_${FULL_VERSION}_${ARCH}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "=============================================="
echo "  Tomo DEB Package Builder"
echo "=============================================="
echo ""
echo "  Package: ${PACKAGE_NAME}"
echo "  Version: ${FULL_VERSION}"
echo "  Arch:    ${ARCH}"
echo ""

# Check dependencies
log_info "Checking build dependencies..."
command -v dpkg-deb >/dev/null 2>&1 || log_error "dpkg-deb not found. Install dpkg package."
command -v python3 >/dev/null 2>&1 || log_error "python3 not found."
command -v node >/dev/null 2>&1 || log_error "node not found."
command -v yarn >/dev/null 2>&1 || log_error "yarn not found."
command -v npm >/dev/null 2>&1 || log_error "npm not found."
command -v uv >/dev/null 2>&1 || log_error "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
log_success "Dependencies OK"

# Clean previous build
log_info "Cleaning previous build..."
rm -rf "$SCRIPT_DIR/build"
mkdir -p "$BUILD_DIR"

# Create directory structure
log_info "Creating package directory structure..."
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/tomo/backend"
mkdir -p "$BUILD_DIR/opt/tomo/cli"
mkdir -p "$BUILD_DIR/var/www/tomo"
mkdir -p "$BUILD_DIR/etc/tomo"
mkdir -p "$BUILD_DIR/etc/nginx/conf.d"
mkdir -p "$BUILD_DIR/etc/systemd/system"
mkdir -p "$BUILD_DIR/usr/local/bin"

# Copy DEBIAN control files
log_info "Copying control files..."
cp "$SCRIPT_DIR/debian/control" "$BUILD_DIR/DEBIAN/"
cp "$SCRIPT_DIR/debian/conffiles" "$BUILD_DIR/DEBIAN/"
cp "$SCRIPT_DIR/debian/preinst" "$BUILD_DIR/DEBIAN/"
cp "$SCRIPT_DIR/debian/postinst" "$BUILD_DIR/DEBIAN/"
cp "$SCRIPT_DIR/debian/prerm" "$BUILD_DIR/DEBIAN/"
cp "$SCRIPT_DIR/debian/postrm" "$BUILD_DIR/DEBIAN/"

# Make scripts executable
chmod 755 "$BUILD_DIR/DEBIAN/preinst"
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/prerm"
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# Update version in control file
sed -i.bak "s/^Version:.*/Version: ${FULL_VERSION}/" "$BUILD_DIR/DEBIAN/control"
rm -f "$BUILD_DIR/DEBIAN/control.bak"

# Copy backend
log_info "Copying backend..."
cp -r "$PROJECT_ROOT/backend/src"/* "$BUILD_DIR/opt/tomo/backend/"
cp -r "$PROJECT_ROOT/backend/sql" "$BUILD_DIR/opt/tomo/backend/"

# Export requirements.txt from uv.lock (for pip install on target systems)
log_info "Exporting requirements from uv.lock..."
cd "$PROJECT_ROOT/backend"
uv export --no-dev --no-hashes > "$BUILD_DIR/opt/tomo/backend/requirements.txt"
cd "$PROJECT_ROOT"
log_success "Requirements exported"

# Build frontend
log_info "Building frontend (this may take a while)..."
cd "$PROJECT_ROOT/frontend"
yarn install --frozen-lockfile --silent 2>/dev/null || yarn install --frozen-lockfile
yarn build
cp -r dist/* "$BUILD_DIR/var/www/tomo/"
cd "$PROJECT_ROOT"
log_success "Frontend built"

# Build CLI
log_info "Building CLI..."
cd "$PROJECT_ROOT/cli"
npm ci --silent 2>/dev/null || npm ci
npm run build
cp -r dist "$BUILD_DIR/opt/tomo/cli/"
cp -r node_modules "$BUILD_DIR/opt/tomo/cli/"
cp package.json "$BUILD_DIR/opt/tomo/cli/"
cd "$PROJECT_ROOT"
log_success "CLI built"

# Create CLI symlink
ln -sf /opt/tomo/cli/dist/src/bin/tomo.js \
    "$BUILD_DIR/usr/local/bin/tomo"

# Copy configuration files
log_info "Copying configuration files..."
cp "$SCRIPT_DIR/debian/tomo.service" \
    "$BUILD_DIR/etc/systemd/system/"
cp "$SCRIPT_DIR/debian/tomo.nginx" \
    "$BUILD_DIR/etc/nginx/conf.d/tomo.conf"

# Copy example config if exists
if [ -f "$PROJECT_ROOT/backend/.env-default" ]; then
    cp "$PROJECT_ROOT/backend/.env-default" \
        "$BUILD_DIR/etc/tomo/environment.example"
fi

# Create VERSION file
echo "$VERSION" > "$BUILD_DIR/opt/tomo/VERSION"

# Set permissions
log_info "Setting file permissions..."
find "$BUILD_DIR" -type d -exec chmod 755 {} \;
find "$BUILD_DIR" -type f -exec chmod 644 {} \;
chmod 755 "$BUILD_DIR/DEBIAN/preinst"
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/prerm"
chmod 755 "$BUILD_DIR/DEBIAN/postrm"
chmod 755 "$BUILD_DIR/usr/local/bin/tomo"

# Build the package
log_info "Building DEB package..."
dpkg-deb --build --root-owner-group "$BUILD_DIR"

# Move to final location
FINAL_DEB="$SCRIPT_DIR/build/${PACKAGE_NAME}_${FULL_VERSION}_${ARCH}.deb"
mv "${BUILD_DIR}.deb" "$FINAL_DEB"

# Get package size
SIZE=$(du -h "$FINAL_DEB" | cut -f1)

echo ""
echo "=============================================="
echo -e "${GREEN}  Package built successfully!${NC}"
echo "=============================================="
echo ""
echo "  Output: $FINAL_DEB"
echo "  Size:   $SIZE"
echo ""
echo "  To install:"
echo "    sudo apt install ./$FINAL_DEB"
echo ""
echo "  To verify:"
echo "    dpkg-deb --info $FINAL_DEB"
echo "    dpkg-deb --contents $FINAL_DEB"
echo ""

# Optional: Run lintian if available
if command -v lintian >/dev/null 2>&1; then
    log_info "Running lintian checks..."
    lintian "$FINAL_DEB" || true
fi

exit 0
