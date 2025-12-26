Name:           homelab-assistant
Version:        1.0.0
Release:        1%{?dist}
Summary:        Self-hosted homelab infrastructure management

License:        MIT
URL:            https://github.com/cbabil/homelab
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-devel
BuildRequires:  nodejs
Requires:       python3 >= 3.11
Requires:       python3-pip

%description
A self-hosted web application for managing homelab infrastructure.
Connect to remote servers via SSH, deploy Docker applications through
an extensible catalog, and monitor your infrastructure.

%prep
%setup -q

%build
# Build frontend
cd frontend
npm install
npm run build
cd ..

%install
# Create directories
mkdir -p %{buildroot}/opt/homelab-assistant
mkdir -p %{buildroot}/etc/homelab-assistant
mkdir -p %{buildroot}/var/lib/homelab-assistant
mkdir -p %{buildroot}/var/log/homelab-assistant
mkdir -p %{buildroot}%{_unitdir}

# Install backend
cp -r backend/src/* %{buildroot}/opt/homelab-assistant/
cp backend/requirements.txt %{buildroot}/opt/homelab-assistant/

# Install frontend build
cp -r frontend/dist %{buildroot}/opt/homelab-assistant/static

# Install config
cp packaging/config.yaml.example %{buildroot}/etc/homelab-assistant/config.yaml

# Install systemd service
cp packaging/homelab-assistant.service %{buildroot}%{_unitdir}/

%post
# Create user if not exists
getent group homelab >/dev/null || groupadd -r homelab
getent passwd homelab >/dev/null || useradd -r -g homelab -d /var/lib/homelab-assistant -s /sbin/nologin homelab

# Set permissions
chown -R homelab:homelab /var/lib/homelab-assistant
chown -R homelab:homelab /var/log/homelab-assistant
chmod 750 /var/lib/homelab-assistant
chmod 750 /var/log/homelab-assistant

# Install Python dependencies
cd /opt/homelab-assistant && pip3 install -r requirements.txt

# Enable service
systemctl daemon-reload
systemctl enable homelab-assistant

%preun
if [ $1 -eq 0 ]; then
    systemctl stop homelab-assistant
    systemctl disable homelab-assistant
fi

%files
%defattr(-,root,root,-)
/opt/homelab-assistant
%config(noreplace) /etc/homelab-assistant/config.yaml
%{_unitdir}/homelab-assistant.service
%dir %attr(750,homelab,homelab) /var/lib/homelab-assistant
%dir %attr(750,homelab,homelab) /var/log/homelab-assistant

%changelog
* Thu Dec 26 2025 Homelab Team <team@example.com> - 1.0.0-1
- Initial release
