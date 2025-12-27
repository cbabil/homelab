Name:           homelab-assistant
Version:        0.1.0
Release:        1%{?dist}
Summary:        Self-hosted homelab infrastructure management

License:        MIT
URL:            https://github.com/cbabil/homelab
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-devel >= 3.11
BuildRequires:  python3-pip
BuildRequires:  nodejs >= 18
BuildRequires:  npm

Requires:       python3 >= 3.11
Requires:       nginx

BuildArch:      noarch

%description
A self-hosted web application for managing homelab infrastructure.
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
mkdir -p %{buildroot}/opt/homelab-assistant
mkdir -p %{buildroot}/opt/homelab-assistant/venv
mkdir -p %{buildroot}/opt/homelab-assistant/static
mkdir -p %{buildroot}/etc/homelab-assistant
mkdir -p %{buildroot}/etc/nginx/conf.d
mkdir -p %{buildroot}/var/lib/homelab-assistant/catalog
mkdir -p %{buildroot}/var/log/homelab-assistant
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_bindir}

# Install backend source
cp -r backend/src/* %{buildroot}/opt/homelab-assistant/
cp backend/requirements.txt %{buildroot}/opt/homelab-assistant/

# Install frontend build
cp -r frontend/dist/* %{buildroot}/opt/homelab-assistant/static/

# Install default catalog
if [ -d backend/data/catalog ]; then
    cp -r backend/data/catalog/* %{buildroot}/var/lib/homelab-assistant/catalog/ 2>/dev/null || true
fi

# Install config files
install -m 640 packaging/config.yaml.example %{buildroot}/etc/homelab-assistant/config.yaml
install -m 644 packaging/nginx-homelab.conf %{buildroot}/etc/nginx/conf.d/homelab-assistant.conf

# Install systemd service
install -m 644 packaging/homelab-assistant.service %{buildroot}%{_unitdir}/

# Install CLI wrapper
install -m 755 packaging/homelab-assistant-cli %{buildroot}%{_bindir}/homelab-assistant

%pre
# Create user/group before installation
getent group homelab >/dev/null || groupadd -r homelab
getent passwd homelab >/dev/null || \
    useradd -r -g homelab -d /var/lib/homelab-assistant \
    -s /sbin/nologin -c "Homelab Assistant" homelab
exit 0

%post
# Create Python virtual environment and install dependencies
python3 -m venv /opt/homelab-assistant/venv
/opt/homelab-assistant/venv/bin/pip install --upgrade pip
/opt/homelab-assistant/venv/bin/pip install -r /opt/homelab-assistant/requirements.txt

# Set ownership
chown -R homelab:homelab /var/lib/homelab-assistant
chown -R homelab:homelab /var/log/homelab-assistant
chown homelab:homelab /etc/homelab-assistant/config.yaml

# Set permissions
chmod 750 /var/lib/homelab-assistant
chmod 750 /var/log/homelab-assistant
chmod 640 /etc/homelab-assistant/config.yaml

# Initialize database if not exists
if [ ! -f /var/lib/homelab-assistant/homelab.db ]; then
    sudo -u homelab /opt/homelab-assistant/venv/bin/python \
        /opt/homelab-assistant/cli.py init-db 2>/dev/null || true
fi

# Reload systemd and nginx
systemctl daemon-reload
systemctl reload nginx 2>/dev/null || true

echo ""
echo "Homelab Assistant installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Create admin user: homelab-assistant create-admin"
echo "  2. Start service: systemctl start homelab-assistant"
echo "  3. Enable on boot: systemctl enable homelab-assistant"
echo "  4. Access at: http://localhost (via nginx)"
echo ""

%preun
if [ $1 -eq 0 ]; then
    # Stop and disable on uninstall (not upgrade)
    systemctl stop homelab-assistant 2>/dev/null || true
    systemctl disable homelab-assistant 2>/dev/null || true
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
%dir /opt/homelab-assistant
/opt/homelab-assistant/*

# Configuration
%dir %attr(750,root,homelab) /etc/homelab-assistant
%config(noreplace) %attr(640,homelab,homelab) /etc/homelab-assistant/config.yaml
%config(noreplace) /etc/nginx/conf.d/homelab-assistant.conf

# Systemd service
%{_unitdir}/homelab-assistant.service

# CLI wrapper
%{_bindir}/homelab-assistant

# Data directories
%dir %attr(750,homelab,homelab) /var/lib/homelab-assistant
%dir %attr(750,homelab,homelab) /var/lib/homelab-assistant/catalog
%dir %attr(750,homelab,homelab) /var/log/homelab-assistant

%changelog
* Thu Dec 26 2024 Homelab Team <team@homelab.local> - 0.1.0-1
- Initial release
- Foundation and authentication (Phase 1)
- Server management with SSH (Phase 2)
- Server preparation with Docker (Phase 3)
- Application deployment from catalog (Phase 4)
- Monitoring and logging (Phase 5)
- Production hardening (Phase 6)
