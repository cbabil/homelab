# Usage Guide for Homelab Setup

## Overview

This document provides detailed instructions on using Ansible Semaphore, managing secrets with Semaphore Vault, configuring the `.env` file, utilizing the `group_vars` directory, and understanding the role of `ansible.cfg` in your homelab setup.

## Ansible Semaphore

Ansible Semaphore is a web-based UI for managing Ansible playbooks. It simplifies the process of running and scheduling playbooks, making it easier to manage your infrastructure.

### Accessing Semaphore

1. **Launch Semaphore UI**: After installation, access the Semaphore UI by navigating to `http://localhost:3000` in your web browser.
2. **Login Credentials**: Use the default credentials specified in your `.env` file to log in. It's crucial to change these credentials immediately after the first login for security purposes.

### Managing Projects and Playbooks

1. **Create a Project**: In Semaphore, create a new project to organize your playbooks and inventories.
2. **Add Playbooks**: Upload your Ansible playbooks to the project. Semaphore allows you to run these playbooks directly from the UI.
3. **Schedule Tasks**: Use Semaphore's scheduling feature to automate the execution of playbooks at specified times.

## Semaphore Vault

Semaphore Vault is a feature that allows you to securely store and manage sensitive information such as passwords, API keys, and other secrets.

### Using Semaphore Vault

1. **Access Vault**: Navigate to the Vault section in the Semaphore UI.
2. **Add Secrets**: Add your secrets to the vault. You can categorize them based on projects or environments.
3. **Use Secrets in Playbooks**: Reference these secrets in your playbooks using Semaphore's templating syntax. This ensures that sensitive information is not hardcoded in your playbooks.

## Configuring the `.env` File

The `.env` file is used to configure environment variables for your homelab setup. It contains sensitive information such as database credentials and admin passwords.

### Example `.env` File

```plaintext
# Additional Environment Variables
DOCKER_NETWORK=homelab
DOCKER_VOLUME_PATH=/opt/docker/volumes
LOG_LEVEL=info
```

### Important Considerations

- **Security**: Ensure that the `.env` file is not included in version control. Use `.gitignore` to exclude it.
- **Environment Variables**: Update the variables in the `.env` file to match your environment's configuration. This includes setting secure passwords and access keys.
- **Access Key Encryption**: Use a secure method to generate the `SEMAPHORE_ACCESS_KEY_ENCRYPTION`. This key is used to encrypt sensitive data within Semaphore.
- **Custom Variables**: Add any additional environment-specific variables that your setup requires, such as network configurations or logging levels.

## Utilizing the `group_vars` Directory

The `group_vars` directory is used to define variables that are applied to groups of hosts in your Ansible inventory. This allows for centralized management of configuration settings.

### Example `group_vars` Files

#### `group_vars/all.yml`

```yaml
# Common variables that don't fit into specific categories
# or are used across multiple roles
docker_dir: "/opt/docker"
data_dir: "/data"
network_interface: "eth0"
```

#### `group_vars/vault.yml`

```yaml
---
# Pi-hole Secrets
vault_pihole_web_password: "your_secure_password"

# MySQL Database Secrets
vault_mysql_root_password: "your_secure_root_password"
vault_mysql_user: "semaphore"
vault_mysql_password: "your_secure_db_password"
vault_mysql_database: "semaphore"

# Semaphore Secrets
vault_semaphore_admin: "admin"
vault_semaphore_admin_password: "your_secure_admin_password"
vault_semaphore_admin_name: "Administrator"
vault_semaphore_admin_email: "admin@yourdomain.com"
vault_semaphore_access_key: "your_secure_access_key"
```

### Best Practices for `group_vars`

- **Centralized Configuration**: Use `group_vars` to centralize configuration settings that apply to multiple hosts or roles.
- **Secure Secrets**: Store sensitive information in `vault.yml` and encrypt it using Ansible Vault for added security.
- **Environment-Specific Variables**: Create separate files for different environments (e.g., `production.yml`, `staging.yml`) to manage environment-specific configurations.

## Ansible Configuration (`ansible.cfg`)

The `ansible.cfg` file is used to define default configurations for Ansible operations. It is important for both local development and when using Ansible Semaphore.

### Key Configurations

- **Vault Password File**: Specifies the file used to decrypt Ansible Vault secrets.
  ```ini
  vault_password_file = .vault_pass
  ```

- **Inventory Path**: Defines the default path for inventory files.
  ```ini
  inventory = inventory/
  ```

- **Roles Path**: Specifies where Ansible should look for roles.
  ```ini
  roles_path = roles/
  ```

- **Host Key Checking**: Disables SSH host key checking, useful in testing environments.
  ```ini
  host_key_checking = False
  ```

- **Retry Files**: Disables the creation of retry files.
  ```ini
  retry_files_enabled = False
  ```

### Usage with Semaphore

- **Integration**: When Semaphore executes playbooks, it respects the settings in `ansible.cfg` unless overridden in the Semaphore UI or project settings.
- **Local Development**: The `ansible.cfg` is also useful when testing playbooks locally before uploading them to Semaphore.

## Cleanup Script

The `cleanup.sh` script is designed to remove installed components and restore the system to its previous state. This is useful for testing environments or when you need to reset the setup.

### Using the Cleanup Script

1. **Run the Script**: Execute the `cleanup.sh` script to begin the cleanup process.
   ```bash
   sudo bash setup/cleanup.sh
   ```

2. **Components Removed**: The script will remove Docker containers, volumes, and any other installed components specified in the script.

3. **Restore System State**: After running the script, the system should be restored to its pre-installation state, allowing for a fresh setup if needed.

## Best Practices

- **Change Default Credentials**: Always change default credentials immediately after installation.
- **Regularly Update Secrets**: Regularly update and rotate secrets stored in Semaphore Vault to maintain security.
- **Backup Configuration**: Regularly back up your Semaphore configuration, `.env` file, and `group_vars` directory to prevent data loss.

By following this guide, you can effectively manage your homelab environment using Ansible Semaphore and ensure that your sensitive information is securely managed. 