#!/bin/bash
# Build RPM package for Tomo
# Run this script on a RHEL/Rocky/Fedora system with rpmbuild installed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION=$(grep '"version"' "$PROJECT_DIR/frontend/package.json" | head -1 | sed 's/.*: "\(.*\)".*/\1/')

echo "Building Tomo RPM v${VERSION}"
echo "=========================================="

# Check for required tools
for cmd in rpmbuild npm python3; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is required but not installed"
        exit 1
    fi
done

# Setup rpmbuild directories
RPMBUILD_DIR="$HOME/rpmbuild"
mkdir -p "$RPMBUILD_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create tarball
echo "Creating source tarball..."
TARBALL_NAME="tomo-${VERSION}"
TARBALL_DIR=$(mktemp -d)

mkdir -p "$TARBALL_DIR/$TARBALL_NAME"

# Copy source files
cp -r "$PROJECT_DIR/backend" "$TARBALL_DIR/$TARBALL_NAME/"
cp -r "$PROJECT_DIR/frontend" "$TARBALL_DIR/$TARBALL_NAME/"
cp -r "$PROJECT_DIR/packaging" "$TARBALL_DIR/$TARBALL_NAME/"
cp "$PROJECT_DIR/README.md" "$TARBALL_DIR/$TARBALL_NAME/" 2>/dev/null || true

# Create LICENSE file if not exists
if [ ! -f "$PROJECT_DIR/LICENSE" ]; then
    echo "MIT License" > "$TARBALL_DIR/$TARBALL_NAME/LICENSE"
fi
cp "$PROJECT_DIR/LICENSE" "$TARBALL_DIR/$TARBALL_NAME/" 2>/dev/null || true

# Create tarball
cd "$TARBALL_DIR"
tar czf "$RPMBUILD_DIR/SOURCES/${TARBALL_NAME}.tar.gz" "$TARBALL_NAME"
rm -rf "$TARBALL_DIR"

echo "Tarball created: $RPMBUILD_DIR/SOURCES/${TARBALL_NAME}.tar.gz"

# Copy and update spec file
echo "Preparing spec file..."
SPEC_FILE="$RPMBUILD_DIR/SPECS/tomo.spec"
cp "$SCRIPT_DIR/tomo.spec" "$SPEC_FILE"

# Update version in spec file
sed -i "s/^Version:.*/Version:        ${VERSION}/" "$SPEC_FILE"

# Build RPM
echo "Building RPM..."
rpmbuild -ba "$SPEC_FILE"

# Show results
echo ""
echo "Build complete!"
echo ""
echo "RPM packages created:"
find "$RPMBUILD_DIR/RPMS" -name "tomo*.rpm" -type f
echo ""
echo "Source RPM created:"
find "$RPMBUILD_DIR/SRPMS" -name "tomo*.rpm" -type f
echo ""
echo "To install:"
echo "  sudo dnf install $RPMBUILD_DIR/RPMS/noarch/tomo-${VERSION}-*.rpm"
