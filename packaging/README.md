# Tomo - Packaging

This directory contains packaging files for building distribution packages.

## DEB Package (Debian/Ubuntu)

### Prerequisites

- Debian 12+ or Ubuntu 22.04+
- dpkg-deb (from `dpkg` package)
- Python 3.11+
- Node.js 18+
- Yarn (for frontend)
- npm (for CLI)

### Build

```bash
# Build with default version
./build-deb.sh

# Build with specific version
./build-deb.sh 1.0.0

# Build with version and release number
./build-deb.sh 1.0.0 2
```

Output: `build/tomo_VERSION_amd64.deb`

### Install

```bash
sudo apt install ./build/tomo_1.0.0-1_amd64.deb
```

### Post-Install Steps

1. Edit `/etc/tomo/environment` to set `ALLOWED_ORIGINS`
2. Start the service: `sudo systemctl start tomo`
3. Create admin account: `tomo admin create`
4. Access web UI: `http://localhost`

### Uninstall

```bash
# Remove (keeps data and config)
sudo apt remove tomo

# Purge (removes everything)
sudo apt purge tomo
```

## RPM Package (RHEL/CentOS/Fedora)

See `tomo.spec` for RPM build instructions.

```bash
./build-rpm.sh
```

## File Locations

| Purpose | Path |
|---------|------|
| Application | `/opt/tomo/` |
| Frontend | `/var/www/tomo/` |
| Data | `/var/lib/tomo/` |
| Logs | `/var/log/tomo/` |
| Config | `/etc/tomo/` |
| Systemd | `/etc/systemd/system/tomo.service` |
| Nginx | `/etc/nginx/conf.d/tomo.conf` |
| CLI | `/usr/local/bin/tomo` |

## Service Management

```bash
# Start/stop/restart
sudo systemctl start tomo
sudo systemctl stop tomo
sudo systemctl restart tomo

# Check status
sudo systemctl status tomo

# View logs
journalctl -u tomo -f
```
