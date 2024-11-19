# Deployment Guide

## Prerequisites
- Ansible Semaphore installed
- Docker and Docker Compose installed
- Access to target servers

## Semaphore Setup
1. Configure environment variables in Semaphore UI:
   - MYSQL_ROOT_PASSWORD
   - MYSQL_PASSWORD
   - PIHOLE_PASSWORD
   - SEMAPHORE_ADMIN_PASSWORD
   - SEMAPHORE_ACCESS_KEY

2. Add SSH keys in Semaphore Key Store

3. Create project and import playbooks

## Deployment Steps
1. Select appropriate inventory
2. Run playbook with required tags
3. Verify services are running 