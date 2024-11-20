# Homelab Setup

## Overview

This repository contains scripts and configurations to set up a homelab environment with various services and applications. The setup is automated using shell scripts and Ansible roles.

## Prerequisites

- A Debian/Ubuntu-based system
- Root access or sudo privileges
- Internet connection

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Run the Initialization Script**
   Execute the main initialization script to set up all components:
   ```bash
   sudo bash setup/init.sh
   ```

3. **Verify Installations**
   - Check Docker installation: `docker --version`
   - Check Docker Compose installation: `docker-compose --version`
   - Access Ansible Semaphore UI at `http://localhost:3000`

## Installed Applications

| Application       | Description                        | Role/Task File                                         |
|-------------------|------------------------------------|--------------------------------------------------------|
| Git               | Version control system             | `install-git.sh`                                       |
| Python3           | Python runtime                     | `install-python3.sh`                                   |
| Pip3              | Python package manager             | `install-pip3.sh`                                      |
| Docker            | Containerization platform          | `install-docker.sh`                                    |
| Docker Compose    | Multi-container orchestration tool | `install-docker-compose.sh`                            |
| Ansible Semaphore | Ansible UI for playbook management | `install-semaphore.sh`                                 |
| Pi-hole           | Network-wide ad blocker            | `roles/services/tasks/applications/pihole/install.yml` |
| Portainer         | Docker management UI               | `roles/services/tasks/containers/portainer.yml`        |
| Watchtower        | Automatic container updates        | `roles/services/tasks/containers/watchtower.yml`       |
| Homarr            | Dashboard for managing services    | `roles/services/tasks/containers/homarr.yml`           |
| MySQL             | Database server                    | `roles/services/tasks/containers/mysql.yml`            |

## Security Considerations

- Ensure all default passwords are changed in production environments.
- Follow security best practices as outlined in `SECURITY.md`.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.