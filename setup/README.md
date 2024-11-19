# Setup Scripts

This directory contains scripts for setting up and managing the homelab environment.

## Overview

These scripts automate the installation and cleanup of various components needed for the homelab:
- Git
- Python3 & Pip3
- Docker & Docker Compose
- Ansible Semaphore
- HomeLab MOTD

## Prerequisites

- Debian/Ubuntu-based system
- Root access or sudo privileges
- Internet connection

## Scripts Description

### Installation Scripts

- `init.sh`: Main initialization script that orchestrates the entire setup
- `install-git.sh`: Installs Git version control
- `install-python3.sh`: Installs Python3 runtime
- `install-pip3.sh`: Installs Python package manager
- `install-docker.sh`: Installs Docker engine
- `install-docker-compose.sh`: Installs Docker Compose
- `install-semaphore.sh`: Sets up Ansible Semaphore UI

### Cleanup Scripts

- `cleanup.sh`: Removes installed components and restores system state

## Usage

### Installation

Run the initialization script as root: