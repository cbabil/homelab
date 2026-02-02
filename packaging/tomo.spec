Name:           tomo
Version:        0.1.0
Release:        1%{?dist}
Summary:        Self-hosted infrastructure management

License:        MIT
URL:            https://github.com/cbabil/tomo
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-devel >= 3.11
BuildRequires:  python3-pip
BuildRequires:  nodejs >= 18
BuildRequires:  npm

Requires:       python3 >= 3.11
Requires:       nginx

BuildArch:      noarch

%description
A self-hosted web application for managing your infrastructure.
Connect to remote servers via SSH, deploy Docker applications through
an extensible catalog, and monitor your infrastructure.

Features:
- SSH server management with encrypted credentials
- Docker application deployment from extensible catalog
- Real-time monitoring and metrics
- Multi-user support with role-based access
- Encrypted backup and restore

%prep
%setup -q

%build
# Build frontend
cd frontend
npm install --legacy-peer-deps
npm run build
cd ..

%install
rm -rf %{buildroot}

# Create directories
mkdir -p %{buildroot}/opt/tomo
mkdir -p %{buildroot}/opt/tomo/venv
mkdir -p %{buildroot}/opt/tomo/static
mkdir -p %{buildroot}/etc/tomo
mkdir -p %{buildroot}/etc/nginx/conf.d
mkdir -p %{buildroot}/var/lib/tomo/catalog
mkdir -p %{buildroot}/var/log/tomo
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_bindir}

# Install backend source
cp -r backend/src/* %{buildroot}/opt/tomo/
cp backend/requirements.txt %{buildroot}/opt/tomo/

# Install frontend build
cp -r frontend/dist/* %{buildroot}/opt/tomo/static/

# Install default catalog
if [ -d backend/data/catalog ]; then
    cp -r backend/data/catalog/* %{buildroot}/var/lib/tomo/catalog/ 2>/dev/null || true
fi

# Install config files
install -m 640 packaging/config.yaml.example %{buildroot}/etc/tomo/config.yaml
install -m 644 packaging/nginx-tomo.conf %{buildroot}/etc/nginx/conf.d/tomo.conf

# Install systemd service
install -m 644 packaging/tomo.service %{buildroot}%{_unitdir}/

# Install CLI wrapper
install -m 755 packaging/tomo-cli %{buildroot}%{_bindir}/tomo

%pre
# Create user/group before installation
getent group tomo >/dev/null || groupadd -r tomo
getent passwd tomo >/dev/null || \
    useradd -r -g tomo -d /var/lib/tomo \
    -s /sbin/nologin -c "Tomo" tomo
exit 0

%post
# Create Python virtual environment and install dependencies
python3 -m venv /opt/tomo/venv
/opt/tomo/venv/bin/pip install --upgrade pip
/opt/tomo/venv/bin/pip install -r /opt/tomo/requirements.txt

# Set ownership
chown -R tomo:tomo /var/lib/tomo
chown -R tomo:tomo /var/log/tomo
chown tomo:tomo /etc/tomo/config.yaml

# Set permissions
chmod 750 /var/lib/tomo
chmod 750 /var/log/tomo
chmod 640 /etc/tomo/config.yaml

# Initialize database if not exists
if [ ! -f /var/lib/tomo/tomo.db ]; then
    sudo -u tomo /opt/tomo/venv/bin/python \
        /opt/tomo/cli.py init-db 2>/dev/null || true
fi

# Reload systemd and nginx
systemctl daemon-reload
systemctl reload nginx 2>/dev/null || true

echo ""
echo "Tomo installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Create admin user: tomo create-admin"
echo "  2. Start service: systemctl start tomo"
echo "  3. Enable on boot: systemctl enable tomo"
echo "  4. Access at: http://localhost (via nginx)"
echo ""

%preun
if [ $1 -eq 0 ]; then
    # Stop and disable on uninstall (not upgrade)
    systemctl stop tomo 2>/dev/null || true
    systemctl disable tomo 2>/dev/null || true
fi

%postun
if [ $1 -eq 0 ]; then
    # Reload nginx after uninstall
    systemctl reload nginx 2>/dev/null || true
fi

%files
%defattr(-,root,root,-)
%doc README.md
%license LICENSE

# Application files
%dir /opt/tomo
/opt/tomo/*

# Configuration
%dir %attr(750,root,tomo) /etc/tomo
%config(noreplace) %attr(640,tomo,tomo) /etc/tomo/config.yaml
%config(noreplace) /etc/nginx/conf.d/tomo.conf

# Systemd service
%{_unitdir}/tomo.service

# CLI wrapper
%{_bindir}/tomo

# Data directories
%dir %attr(750,tomo,tomo) /var/lib/tomo
%dir %attr(750,tomo,tomo) /var/lib/tomo/catalog
%dir %attr(750,tomo,tomo) /var/log/tomo

%changelog
* Thu Dec 26 2024 Tomo Team <team@tomo.dev> - 0.1.0-1
- Initial release
- Foundation and authentication (Phase 1)
- Server management with SSH (Phase 2)
- Server preparation with Docker (Phase 3)
- Application deployment from catalog (Phase 4)
- Monitoring and logging (Phase 5)
- Production hardening (Phase 6)
