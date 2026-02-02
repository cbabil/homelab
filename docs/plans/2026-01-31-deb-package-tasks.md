# DEB Package Implementation - Task List

**Status: P0/P1/P3 COMPLETE - P2 Testing requires Linux environment**
**Plan Document: [2026-01-31-deb-package-implementation.md](2026-01-31-deb-package-implementation.md)**

---

## Priority Legend

| Priority | Meaning |
|----------|---------|
| P0 | **Critical** - Foundation, must complete first |
| P1 | **High** - Core scripts, required for functioning |
| P2 | **Medium** - Testing & validation |
| P3 | **Low** - Polish, documentation, automation |

---

## P0: Critical (Foundation) - 5 tasks

### Directory Structure
- [x] Create `packaging/debian/` directory
- [x] Create `packaging/build-deb.sh` placeholder

### Control Files
- [x] Create `packaging/debian/control` - Package metadata
  - Package name: `tomo`
  - Architecture: `amd64`
  - Dependencies: python3 (>=3.11), python3-venv, nginx, nodejs (>=18)
  - Recommends: sqlite3, certbot

- [x] Create `packaging/debian/conffiles` - Config file list
  ```
  /etc/tomo/environment
  /etc/nginx/conf.d/tomo.conf
  ```

### Service Files
- [x] Create `packaging/debian/tomo.service` - Systemd unit
  - Type: simple
  - User: tomo
  - WorkingDirectory: /opt/tomo
  - ExecStart: venv python main.py
  - Security hardening options

- [x] Create `packaging/debian/tomo.nginx` - Nginx config
  - Upstream to 127.0.0.1:8000
  - Static files from /var/www/tomo
  - Proxy /mcp to backend
  - Security headers

---

## P1: High (Scripts) - 5 tasks

### Installation Scripts
- [x] Create `packaging/debian/preinst` - Pre-installation
  - Create tomo group if not exists
  - Create tomo user if not exists
  - Stop existing service if upgrading

- [x] Create `packaging/debian/postinst` - Post-installation
  - Create /var/lib/tomo
  - Create /var/log/tomo
  - Create /etc/tomo
  - Set directory ownership (tomo:tomo)
  - Create Python venv if not exists
  - Install Python requirements
  - Generate secrets on first install
  - Create environment file
  - Reload nginx
  - Enable systemd service
  - Print post-install instructions

- [x] Create `packaging/debian/prerm` - Pre-removal
  - Stop tomo service
  - Disable tomo service

- [x] Create `packaging/debian/postrm` - Post-removal
  - On purge: remove /var/lib/tomo
  - On purge: remove /var/log/tomo
  - On purge: remove /etc/tomo
  - On purge: remove Python venv
  - On purge: delete tomo user/group
  - Reload nginx
  - Daemon-reload systemd

### Build Script
- [x] Create `packaging/build-deb.sh` - Main build script
  - Accept VERSION and RELEASE as arguments
  - Clean previous build directory
  - Create package directory structure
  - Copy DEBIAN control files
  - Copy backend source and requirements
  - Build frontend (yarn build)
  - Build CLI (npm run build)
  - Copy CLI with node_modules
  - Create CLI symlink
  - Copy config templates
  - Create VERSION file
  - Set file permissions
  - Run dpkg-deb --build
  - Output final .deb file location

---

## P2: Medium (Testing) - 6 tasks

### Build Testing
- [ ] Test build script on development machine
  - Verify all files included
  - Verify permissions correct
  - Verify control file syntax (lintian)

### Installation Testing
- [ ] Test fresh install on Debian 12 (Bookworm)
  - Use clean Docker container or VM
  - Verify user created
  - Verify directories created
  - Verify venv created
  - Verify service starts
  - Verify web UI accessible
  - Verify CLI works
  - Verify admin creation works

- [ ] Test fresh install on Ubuntu 22.04 LTS
  - Same verification steps as Debian 12

- [ ] Test fresh install on Ubuntu 24.04 LTS
  - Same verification steps as Debian 12

### Upgrade Testing
- [ ] Test upgrade from previous version
  - Install v1.0.0
  - Add data (create users, servers)
  - Upgrade to v1.0.1
  - Verify data preserved
  - Verify service restarts
  - Verify no errors

### Removal Testing
- [ ] Test removal and purge
  - `apt remove tomo` - verify data preserved
  - `apt purge tomo` - verify data removed
  - Verify no orphaned files
  - Verify user removed on purge

---

## P3: Low (Polish) - 6 tasks

### Additional Files
- [x] Create `packaging/debian/copyright` - License file
  - MIT license
  - Copyright holder
  - Upstream source URL

- [x] Create `packaging/debian/changelog` - Debian changelog
  - Follow debian changelog format
  - Include version and date
  - Urgency: medium

- [x] Create `packaging/README.md` - Build instructions
  - Prerequisites
  - Build commands
  - Installation commands
  - Troubleshooting

### Documentation Updates
- [x] Update `docs/INSTALLATION.md` - Add DEB section
  - Download instructions
  - Installation command
  - Post-install steps
  - Upgrade instructions
  - Removal instructions

- [x] Update `TODO.md` - Mark task complete

### CI/CD
- [x] Add GitHub Actions workflow for DEB building
  - Trigger on release tags (in .github/workflows/release.yml)
  - Build on ubuntu-latest
  - Upload .deb as release artifact

---

## Execution Order

```
P0: Foundation (5 tasks)
│
├─► Directory structure
│   └─► Control files
│       └─► Service files
│
P1: Scripts (5 tasks)
│
├─► preinst
│   └─► postinst
│       └─► prerm
│           └─► postrm
│               └─► build-deb.sh
│
P2: Testing (6 tasks)
│
├─► Build test
│   └─► Debian 12 test
│       └─► Ubuntu 22.04 test
│           └─► Ubuntu 24.04 test
│               └─► Upgrade test
│                   └─► Removal test
│
P3: Polish (6 tasks)
│
├─► copyright
│   └─► changelog
│       └─► README.md
│           └─► INSTALLATION.md
│               └─► TODO.md
│                   └─► GitHub Actions
```

---

## Progress Tracker

| Priority | Tasks | Completed | Status |
|----------|-------|-----------|--------|
| P0: Critical | 5 | 5 | ✅ Complete |
| P1: High | 5 | 5 | ✅ Complete |
| P2: Medium | 6 | 0 | ⏸️ Requires Linux |
| P3: Low | 6 | 6 | ✅ Complete |
| **Total** | **22** | **16** | **73%** |

---

## Dependencies

### Build Machine Requirements
- Debian 12+ or Ubuntu 22.04+
- dpkg-deb (from dpkg package)
- Python 3.11+
- Node.js 18+
- Yarn (for frontend)
- npm (for CLI)

### Test Environment Requirements
- Docker (for isolated testing)
- Or: VMs/cloud instances for each target distro
- Clean systems (no previous tomo installation)

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Python version mismatch | Specify minimum version in Depends |
| Node.js not available | Add nodejs repo in docs, or bundle |
| Large package size | Consider dh-virtualenv or split packages |
| Nginx conflicts | Use conf.d drop-in, not sites-available |
| Permission issues | Careful ownership in postinst |
| Upgrade data loss | Test upgrade path thoroughly |
| Service startup failure | Add systemd health checks |

---

## Success Criteria

1. **Build**: `./build-deb.sh` produces valid .deb file
2. **Lint**: `lintian tomo_*.deb` passes with no errors
3. **Install**: `apt install ./tomo_*.deb` works on clean system
4. **Run**: Service starts and web UI is accessible
5. **CLI**: `tomo admin create` works
6. **Upgrade**: Data preserved during version upgrade
7. **Remove**: Clean removal with `apt remove`
8. **Purge**: Complete cleanup with `apt purge`
