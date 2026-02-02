# Frequently Asked Questions

Common questions about Tomo.

---

## General

### What is Tomo?

Tomo is a self-hosted platform for managing tomo infrastructure. It lets you:
- Connect to remote servers via SSH
- Deploy Docker applications from a marketplace
- Monitor system health and metrics
- Manage everything from a single dashboard

---

### Is Tomo free?

Tomo is proprietary software. See the [LICENSE](https://github.com/cbabil/tomo/blob/main/LICENSE) for terms. For licensing inquiries, contact christophe@babilotte.com.

---

### What are the system requirements?

**For the server running Tomo:**
- Debian 12+ or Ubuntu 22.04+
- 1 GB RAM (2 GB recommended)
- 5 GB disk space
- Internet access

**For managed servers:**
- Any Linux with SSH
- Docker (can be auto-installed)

---

### Can I run this on a Raspberry Pi?

Yes, with caveats:
- Use a Pi 4 with 4GB+ RAM
- Use a fast SD card or SSD
- Performance may be limited with many servers

---

## Installation

### Which installation method should I use?

| Use Case | Recommended Method |
|----------|-------------------|
| Production server | DEB Package |
| Testing/evaluation | Docker |
| Development | From Source |

---

### Can I install on Windows?

Not natively. Options:
- Use WSL2 (Windows Subsystem for Linux)
- Run in a Docker container
- Use a Linux VM

---

### Do I need Docker on the main server?

No. Docker is only needed on managed remote servers where you deploy applications. The main Tomo server runs natively.

---

### How do I update to a new version?

**DEB Package:**
```bash
wget https://github.com/cbabil/tomo/releases/latest/download/tomo_X.Y.Z-1_amd64.deb
sudo apt install ./tomo_X.Y.Z-1_amd64.deb
```

**Docker:**
```bash
docker compose down
docker compose pull
docker compose up -d
```

---

## Servers

### How many servers can I manage?

There's no hard limit. Practical considerations:
- 10-20 servers: Works well on minimal hardware
- 50+ servers: Increase resources, tune metrics intervals
- 100+ servers: Consider distributed monitoring

---

### Can I use non-Linux servers?

Currently only Linux servers with SSH are supported. Future versions may add:
- Windows (via WinRM)
- macOS (via SSH)
- ESXi/Proxmox

---

### Is root access required?

No, but recommended for full functionality:
- Docker management requires docker group membership
- Some system metrics need elevated permissions
- Agent installation needs sudo

---

### Can I use SSH key with passphrase?

Yes. When adding a server:
1. Upload your private key
2. Enter the passphrase when prompted
3. The passphrase is encrypted at rest

---

## Security

### How are credentials stored?

SSH passwords and private keys are encrypted using:
- AES-256-GCM encryption
- PBKDF2 key derivation (100,000 iterations)
- Unique salt per installation

---

### Is my data sent to external services?

By default, no. The only optional external service is Have I Been Pwned for password checking, which uses k-Anonymity (only sends first 5 characters of password hash).

---

### How do I secure my installation?

1. Use HTTPS (see [[Security-Settings]])
2. Set strong passwords
3. Enable session timeout
4. Review audit logs regularly
5. Keep software updated

---

### What ports need to be open?

| Port | Purpose | Required |
|------|---------|----------|
| 80/443 | Web UI | Yes (one) |
| 8000 | Backend API | Internal only |
| 8765 | Agent WebSocket | If using agents |
| 22 | SSH to servers | To managed servers |

---

## Applications

### What applications are available?

The marketplace includes popular self-hosted apps:
- Media servers (Jellyfin, Plex)
- File sharing (Nextcloud)
- Monitoring (Uptime Kuma, Grafana)
- Development (Gitea, Code Server)
- And many more

---

### Can I deploy custom applications?

Yes, two ways:
1. **Custom image**: Deploy any Docker image directly
2. **Custom catalog**: Add your own app catalog

---

### Where is application data stored?

Application data is stored on the remote servers in Docker volumes. This data is NOT backed up by Tomo - use Docker volume backups or application-specific backup tools.

---

### Can I migrate applications between servers?

Currently manual:
1. Export data from source server
2. Deploy fresh on target server
3. Import data

Application migration is on the roadmap.

---

## Agent

### Do I need to install the agent?

The agent is optional. Without it:
- Basic server status still works (via SSH)
- Some metrics may be limited
- Commands executed via SSH instead of agent

With agent:
- Real-time metrics
- Faster command execution
- Docker integration
- Automatic reconnection

---

### What does the agent collect?

- CPU, memory, disk usage
- Network statistics
- Docker container status
- System uptime

The agent does NOT collect:
- File contents
- Passwords
- Personal data

---

### How is agent communication secured?

- TLS-encrypted WebSocket
- Token-based authentication
- Automatic token rotation (every 24 hours)
- Command allowlist (only approved operations)

---

## Troubleshooting

### I forgot my admin password

Reset via CLI:
```bash
tomo admin reset-password
```

This requires server access but not web login.

---

### My server shows as offline

Check:
1. Server is powered on and connected
2. SSH service is running
3. Firewall allows connections
4. Credentials are correct

See [[Troubleshooting]] for detailed steps.

---

### Deployment is stuck

Common causes:
1. Docker image is large (wait for download)
2. Network issue on remote server
3. Docker service problem

Check logs:
```bash
tomo app logs <app-id>
```

---

### Where are the logs?

| Installation | Location |
|--------------|----------|
| DEB Package | `/var/log/tomo/` |
| Docker | `docker compose logs` |
| Development | Console output |

---

## Backup & Recovery

### What does backup include?

- Server configurations
- User accounts
- Application metadata
- System settings
- Audit logs

NOT included:
- Application data on remote servers
- Docker volumes
- Container images

---

### How often should I backup?

Recommendations:
- **Daily**: Active installations with changes
- **Weekly**: Stable installations
- **Before changes**: Before updates or major modifications

---

### Can I restore to a different server?

Yes:
1. Install Tomo on new server
2. Create admin account
3. Restore from backup
4. Update server IPs if changed

---

## Contributing

### Can I contribute to the project?

See [[Contributing]] for contribution guidelines. We welcome:
- Bug reports
- Feature requests
- Documentation improvements

---

### Where can I report bugs?

[GitHub Issues](https://github.com/cbabil/tomo/issues) - please use the bug report template.

---

## Still Have Questions?

- [[Troubleshooting]] - Common problems and solutions
- [[Error-Messages]] - Error reference
- [GitHub Issues](https://github.com/cbabil/tomo/issues) - Report issues or ask questions
