# DEB Package Implementation Plan

**Status: PLANNING**
**Created: 2026-01-31**
**Target: Debian 12+ / Ubuntu 22.04+**

---

## Overview

Create a `.deb` package for installing Tomo on Debian-based Linux distributions (Debian, Ubuntu, Linux Mint, Pop!_OS, etc.).

### Package Naming Convention

Following Debian naming standards:
- **Package Name**: `tomo`
- **Version Format**: `X.Y.Z-debian1` (e.g., `1.0.0-debian1`)
- **Architecture**: `amd64` (x86_64), future: `arm64`

---

## Architecture Decision

### Option A: Single Monolithic Package (Recommended)
```
tomo_1.0.0-debian1_amd64.deb
├── Backend (Python)
├── Frontend (Static)
├── CLI (Node.js)
└── Configuration
```

**Pros:**
- Simple installation: `apt install ./tomo.deb`
- Single version tracking
- Atomic upgrades
- Easier dependency resolution

**Cons:**
- Larger package size (~25 MB)
- Updates require full package replacement

### Option B: Split Packages
```
tomo-backend_1.0.0-debian1_amd64.deb
tomo-frontend_1.0.0-debian1_all.deb
tomo-cli_1.0.0-debian1_amd64.deb
tomo (meta-package)
```

**Pros:**
- Granular updates
- Smaller individual downloads
- Optional CLI installation

**Cons:**
- Complex dependency management
- Multiple packages to track
- More maintainer overhead

### Decision: **Option A (Monolithic)**
For v1, use a single package for simplicity. Can split later if needed.

---

## Package Structure

```
tomo_1.0.0-debian1_amd64.deb
│
├── DEBIAN/                          # Package metadata
│   ├── control                      # Package info, dependencies
│   ├── conffiles                    # List of config files
│   ├── preinst                      # Pre-installation script
│   ├── postinst                     # Post-installation script
│   ├── prerm                        # Pre-removal script
│   └── postrm                       # Post-removal script
│
├── opt/tomo/           # Application files
│   ├── backend/
│   │   ├── src/                     # Python source
│   │   ├── sql/                     # SQL migrations
│   │   ├── requirements.txt
│   │   └── main.py                  # Entry point
│   ├── cli/
│   │   ├── dist/                    # Compiled CLI
│   │   └── node_modules/            # CLI dependencies
│   └── VERSION                      # Version file
│
├── var/www/tomo/       # Frontend static files
│   ├── index.html
│   └── assets/
│
├── etc/tomo/           # Configuration
│   ├── environment.example          # Example env file
│   └── config.yaml.example          # Example config
│
├── etc/nginx/conf.d/
│   └── tomo.conf       # Nginx config
│
├── etc/systemd/system/
│   └── tomo.service    # Systemd service
│
└── usr/local/bin/
    └── tomo                      # CLI symlink
```

---

## Dependencies

### Runtime Dependencies (Depends)
```
python3 (>= 3.11)
python3-venv
nginx
nodejs (>= 18)
```

### Build Dependencies (Build-Depends)
```
debhelper (>= 13)
dh-virtualenv (>= 1.2)
python3-dev
python3-pip
python3-setuptools
nodejs (>= 18)
npm
```

### Recommended (Recommends)
```
sqlite3              # For database inspection
certbot              # For HTTPS certificates
python3-certbot-nginx
```

---

## File Locations

| Purpose | Path | Owner | Mode |
|---------|------|-------|------|
| Application | `/opt/tomo/` | root:root | 755 |
| Python venv | `/opt/tomo/venv/` | root:root | 755 |
| Backend source | `/opt/tomo/backend/` | root:root | 755 |
| CLI | `/opt/tomo/cli/` | root:root | 755 |
| Frontend | `/var/www/tomo/` | root:root | 755 |
| Data directory | `/var/lib/tomo/` | tomo:tomo | 750 |
| Database | `/var/lib/tomo/tomo.db` | tomo:tomo | 640 |
| Logs | `/var/log/tomo/` | tomo:tomo | 750 |
| Config | `/etc/tomo/` | root:tomo | 750 |
| Environment | `/etc/tomo/environment` | root:tomo | 640 |
| Systemd service | `/etc/systemd/system/tomo.service` | root:root | 644 |
| Nginx config | `/etc/nginx/conf.d/tomo.conf` | root:root | 644 |
| CLI symlink | `/usr/local/bin/tomo` | root:root | 755 |

---

## Installation Scripts

### preinst (Pre-Installation)

```bash
#!/bin/bash
set -e

# Create system user if not exists
if ! getent group tomo >/dev/null; then
    groupadd --system tomo
fi

if ! getent passwd tomo >/dev/null; then
    useradd --system \
        --gid tomo \
        --home-dir /var/lib/tomo \
        --shell /sbin/nologin \
        --comment "Tomo Service" \
        tomo
fi

# Stop service if upgrading
if systemctl is-active --quiet tomo 2>/dev/null; then
    systemctl stop tomo
fi

exit 0
```

### postinst (Post-Installation)

```bash
#!/bin/bash
set -e

case "$1" in
    configure)
        # Create directories
        mkdir -p /var/lib/tomo
        mkdir -p /var/log/tomo
        mkdir -p /etc/tomo

        # Set ownership
        chown -R tomo:tomo /var/lib/tomo
        chown -R tomo:tomo /var/log/tomo
        chown root:tomo /etc/tomo
        chmod 750 /etc/tomo

        # Create Python virtual environment if not exists
        if [ ! -d /opt/tomo/venv ]; then
            python3 -m venv /opt/tomo/venv
            /opt/tomo/venv/bin/pip install --upgrade pip wheel
            /opt/tomo/venv/bin/pip install \
                -r /opt/tomo/backend/requirements.txt
        fi

        # Generate secrets if first install
        if [ ! -f /etc/tomo/environment ]; then
            MASTER_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
            SALT=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
            JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")

            cat > /etc/tomo/environment <<EOF
TOMO_MASTER_PASSWORD=${MASTER_PASSWORD}
TOMO_SALT=${SALT}
JWT_SECRET_KEY=${JWT_SECRET}
DATA_DIRECTORY=/var/lib/tomo
PYTHON_ENV=production
ALLOWED_ORIGINS=http://localhost
EOF
            chown root:tomo /etc/tomo/environment
            chmod 640 /etc/tomo/environment
        fi

        # Enable nginx config
        if [ -f /etc/nginx/conf.d/tomo.conf ]; then
            nginx -t 2>/dev/null && systemctl reload nginx || true
        fi

        # Reload systemd and enable service
        systemctl daemon-reload
        systemctl enable tomo

        echo ""
        echo "==================================================="
        echo "  Tomo installed successfully!"
        echo "==================================================="
        echo ""
        echo "Next steps:"
        echo "  1. Edit /etc/tomo/environment"
        echo "     (update ALLOWED_ORIGINS for your domain)"
        echo ""
        echo "  2. Start the service:"
        echo "     sudo systemctl start tomo"
        echo ""
        echo "  3. Create an admin account:"
        echo "     tomo admin create"
        echo ""
        echo "  4. Access the web interface:"
        echo "     http://localhost (or your domain)"
        echo ""
        ;;
    abort-upgrade|abort-remove|abort-deconfigure)
        ;;
    *)
        echo "postinst called with unknown argument: $1" >&2
        exit 1
        ;;
esac

exit 0
```

### prerm (Pre-Removal)

```bash
#!/bin/bash
set -e

case "$1" in
    remove|upgrade|deconfigure)
        # Stop service
        if systemctl is-active --quiet tomo 2>/dev/null; then
            systemctl stop tomo
        fi
        systemctl disable tomo 2>/dev/null || true
        ;;
    failed-upgrade)
        ;;
    *)
        echo "prerm called with unknown argument: $1" >&2
        exit 1
        ;;
esac

exit 0
```

### postrm (Post-Removal)

```bash
#!/bin/bash
set -e

case "$1" in
    purge)
        # Remove data and config on purge
        rm -rf /var/lib/tomo
        rm -rf /var/log/tomo
        rm -rf /etc/tomo
        rm -rf /opt/tomo/venv

        # Remove user
        if getent passwd tomo >/dev/null; then
            userdel tomo 2>/dev/null || true
        fi
        if getent group tomo >/dev/null; then
            groupdel tomo 2>/dev/null || true
        fi

        # Reload nginx
        nginx -t 2>/dev/null && systemctl reload nginx || true
        ;;
    remove|upgrade|failed-upgrade|abort-install|abort-upgrade|disappear)
        ;;
    *)
        echo "postrm called with unknown argument: $1" >&2
        exit 1
        ;;
esac

systemctl daemon-reload

exit 0
```

---

## Control File

```
Package: tomo
Version: 1.0.0-debian1
Section: admin
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.11), python3-venv, nginx, nodejs (>= 18)
Recommends: sqlite3, certbot, python3-certbot-nginx
Maintainer: Your Name <your.email@example.com>
Homepage: https://github.com/your-org/tomo
Description: Self-hosted tomo management platform
 Tomo is a web-based platform for managing
 self-hosted infrastructure including:
  - Server management and monitoring
  - Docker container orchestration
  - Application marketplace
  - Automated agent deployment
  - Backup and restore functionality
```

---

## Build Process

### Directory Structure for Building

```
packaging/
├── debian/
│   ├── control                  # Package metadata
│   ├── rules                    # Build rules (makefile)
│   ├── conffiles                # Config file list
│   ├── preinst                  # Pre-install script
│   ├── postinst                 # Post-install script
│   ├── prerm                    # Pre-remove script
│   ├── postrm                   # Post-remove script
│   ├── tomo.service  # Systemd service
│   ├── tomo.nginx    # Nginx config
│   └── copyright                # License information
├── build-deb.sh                 # Build script
└── README.md                    # Build instructions
```

### Build Script (`build-deb.sh`)

```bash
#!/bin/bash
set -e

VERSION="${1:-1.0.0}"
RELEASE="${2:-debian1}"
ARCH="amd64"
PACKAGE_NAME="tomo"
BUILD_DIR="build/${PACKAGE_NAME}_${VERSION}-${RELEASE}_${ARCH}"

echo "Building ${PACKAGE_NAME} ${VERSION}-${RELEASE} for ${ARCH}"

# Clean previous build
rm -rf build/

# Create directory structure
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/opt/tomo/backend"
mkdir -p "${BUILD_DIR}/opt/tomo/cli"
mkdir -p "${BUILD_DIR}/var/www/tomo"
mkdir -p "${BUILD_DIR}/etc/tomo"
mkdir -p "${BUILD_DIR}/etc/nginx/conf.d"
mkdir -p "${BUILD_DIR}/etc/systemd/system"
mkdir -p "${BUILD_DIR}/usr/local/bin"

# Copy DEBIAN control files
cp packaging/debian/control "${BUILD_DIR}/DEBIAN/"
cp packaging/debian/conffiles "${BUILD_DIR}/DEBIAN/"
cp packaging/debian/preinst "${BUILD_DIR}/DEBIAN/"
cp packaging/debian/postinst "${BUILD_DIR}/DEBIAN/"
cp packaging/debian/prerm "${BUILD_DIR}/DEBIAN/"
cp packaging/debian/postrm "${BUILD_DIR}/DEBIAN/"
chmod 755 "${BUILD_DIR}/DEBIAN/"{preinst,postinst,prerm,postrm}

# Update version in control file
sed -i "s/^Version:.*/Version: ${VERSION}-${RELEASE}/" "${BUILD_DIR}/DEBIAN/control"

# Copy backend
cp -r backend/src "${BUILD_DIR}/opt/tomo/backend/"
cp -r backend/sql "${BUILD_DIR}/opt/tomo/backend/"
cp backend/requirements.txt "${BUILD_DIR}/opt/tomo/backend/"
cp backend/src/main.py "${BUILD_DIR}/opt/tomo/backend/"

# Build frontend
echo "Building frontend..."
cd frontend
yarn install --frozen-lockfile
yarn build
cd ..
cp -r frontend/dist/* "${BUILD_DIR}/var/www/tomo/"

# Build CLI
echo "Building CLI..."
cd cli
npm ci
npm run build
cd ..
cp -r cli/dist "${BUILD_DIR}/opt/tomo/cli/"
cp -r cli/node_modules "${BUILD_DIR}/opt/tomo/cli/"
cp cli/package.json "${BUILD_DIR}/opt/tomo/cli/"

# Create CLI symlink placeholder
ln -sf /opt/tomo/cli/dist/src/bin/tomo.js \
    "${BUILD_DIR}/usr/local/bin/tomo"

# Copy configuration files
cp packaging/debian/tomo.service \
    "${BUILD_DIR}/etc/systemd/system/"
cp packaging/debian/tomo.nginx \
    "${BUILD_DIR}/etc/nginx/conf.d/tomo.conf"
cp backend/.env-default \
    "${BUILD_DIR}/etc/tomo/environment.example"

# Create version file
echo "${VERSION}" > "${BUILD_DIR}/opt/tomo/VERSION"

# Set permissions
find "${BUILD_DIR}" -type d -exec chmod 755 {} \;
find "${BUILD_DIR}" -type f -exec chmod 644 {} \;
chmod 755 "${BUILD_DIR}/DEBIAN/"{preinst,postinst,prerm,postrm}
chmod 755 "${BUILD_DIR}/usr/local/bin/tomo"

# Build package
dpkg-deb --build --root-owner-group "${BUILD_DIR}"

# Move to output
mv "${BUILD_DIR}.deb" "build/${PACKAGE_NAME}_${VERSION}-${RELEASE}_${ARCH}.deb"

echo ""
echo "Package built: build/${PACKAGE_NAME}_${VERSION}-${RELEASE}_${ARCH}.deb"
echo ""
echo "To install:"
echo "  sudo apt install ./build/${PACKAGE_NAME}_${VERSION}-${RELEASE}_${ARCH}.deb"
```

---

## Task List

### P0: Critical (Foundation)

| # | Task | Description |
|---|------|-------------|
| 1 | Create `packaging/debian/` directory structure | Set up all required directories |
| 2 | Create `DEBIAN/control` file | Package metadata with dependencies |
| 3 | Create `DEBIAN/conffiles` | List of configuration files |
| 4 | Create systemd service file | `tomo.service` |
| 5 | Create nginx config file | `tomo.conf` |

### P1: High (Scripts)

| # | Task | Description |
|---|------|-------------|
| 6 | Create `preinst` script | User creation, stop existing service |
| 7 | Create `postinst` script | Directory setup, venv, secrets, enable service |
| 8 | Create `prerm` script | Stop and disable service |
| 9 | Create `postrm` script | Cleanup on purge |
| 10 | Create `build-deb.sh` script | Main build script |

### P2: Medium (Build & Test)

| # | Task | Description |
|---|------|-------------|
| 11 | Test build on clean Debian 12 | Verify build process works |
| 12 | Test install on clean Debian 12 | Fresh installation test |
| 13 | Test upgrade scenario | Version upgrade test |
| 14 | Test removal and purge | Clean uninstallation test |
| 15 | Test on Ubuntu 22.04 | Cross-distro compatibility |
| 16 | Test on Ubuntu 24.04 | Latest LTS compatibility |

### P3: Low (Polish & Docs)

| # | Task | Description |
|---|------|-------------|
| 17 | Add copyright file | License information |
| 18 | Add changelog file | Debian changelog format |
| 19 | Create README for packaging | Build instructions |
| 20 | Add to GitHub Actions | Automated package building |
| 21 | Update TODO.md | Mark task complete |
| 22 | Update INSTALLATION.md | Add DEB installation docs |

---

## Verification Checklist

### Fresh Install
- [ ] Package installs without errors
- [ ] User `tomo` created
- [ ] Directories created with correct permissions
- [ ] Python venv created and deps installed
- [ ] Secrets generated in `/etc/tomo/environment`
- [ ] Systemd service enabled
- [ ] Nginx config loaded
- [ ] Service starts successfully
- [ ] Web UI accessible
- [ ] CLI `tomo` command works
- [ ] Can create admin account

### Upgrade
- [ ] Service stopped before upgrade
- [ ] Database preserved
- [ ] Config preserved
- [ ] Secrets preserved
- [ ] Service restarted after upgrade
- [ ] No data loss

### Removal
- [ ] Service stopped
- [ ] Service disabled
- [ ] Application files removed
- [ ] Config files preserved (remove) or removed (purge)
- [ ] Data files preserved (remove) or removed (purge)
- [ ] User removed on purge
- [ ] No orphaned files

---

## Estimated Package Sizes

| Component | Uncompressed | Compressed |
|-----------|-------------|------------|
| Backend (source only) | ~2 MB | ~0.5 MB |
| Backend (with venv) | ~45 MB | ~15 MB |
| Frontend (build) | ~3 MB | ~1 MB |
| CLI (with node_modules) | ~12 MB | ~4 MB |
| Config/Scripts | < 1 MB | < 0.5 MB |
| **Total** | **~63 MB** | **~21 MB** |

Note: Python venv is created during `postinst`, not included in package, reducing package size to ~18 MB.

---

## Alternative: Using dh-virtualenv

For more robust Python packaging, consider using `dh-virtualenv`:

```
Build-Depends: debhelper (>= 13), dh-virtualenv, python3-dev
```

This creates an isolated Python environment during build, bundling all dependencies in the package. Trade-off is larger package size but simpler installation (no pip install during postinst).

---

## References

- [Debian Policy Manual](https://www.debian.org/doc/debian-policy/)
- [Debian New Maintainers' Guide](https://www.debian.org/doc/manuals/maint-guide/)
- [dh-virtualenv Documentation](https://dh-virtualenv.readthedocs.io/)
- [Systemd Service Files](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- Existing `install.sh` for reference patterns
