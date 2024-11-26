#!/bin/bash

set -o errexit  # Abort on nonzero exit code.
set -o nounset  # Abort on unbound variable.
set -o pipefail # Don't hide errors within pipes.

# Colors
readonly RED=$'\033[0;31m'
readonly GREEN=$'\033[0;32m'
readonly YELLOW=$'\033[0;33m'
readonly BLUE=$'\033[0;34m'

# Reset color
readonly NC=$'\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

error() {
    printf '%s' "${RED}Error: ${1}${NC}" >&2
    printf '\n'
    exit 1
}
export -f error

info() {
    printf '%s' "${BLUE}Info: ${1}${NC}"
    printf '\n'
}
export -f info

success() {
    printf '%s' "${GREEN}Success: ${1}${NC}"
    printf '\n'
}
export -f success

warning() {
    printf '%s' "${YELLOW}Warning: ${1}${NC}"
    printf '\n'
}
export -f warning

# Print section header
print_header() {
    echo
    info "================================================================"
    info " ${1}"
    info "================================================================"
    echo
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking prerequisites"
    info "Checking if prerequisites are installed"
    bash "${SCRIPT_DIR}/check-prerequisites.sh" || error "Prerequisites check failed"
    success "All prerequisites are installed"
}

# Git installation
install_git() {
    print_header "Installing Git"
    info "Git is required for version control and pulling repositories"
    bash "${SCRIPT_DIR}/install-git.sh" || error "Git installation failed"
    success "Git has been installed"
}

# Python3 installation
install_python3() {
    print_header "Installing Python3"
    info "Python3 is required for running Ansible and other automation scripts"
    bash "${SCRIPT_DIR}/install-python3.sh" || error "Python3 installation failed"
    success "Python3 has been installed"
}

# Pip3 installation
install_pip3() {
    print_header "Installing Pip3"
    info "Pip3 is required for installing Python packages"
    bash "${SCRIPT_DIR}/install-pip3.sh" || error "Pip3 installation failed"
    success "Pip3 has been installed"
}

# Docker installation
install_docker() {
    print_header "Installing Docker"
    info "Docker is required for running containerized applications"
    info "This will also add your user to the docker group"
    bash "${SCRIPT_DIR}/install-docker.sh" || error "Docker installation failed"
    success "Docker has been installed"
}

# Docker-compose installation
install_docker_compose() {
    print_header "Installing Docker Compose"
    info "Docker Compose is required for managing multi-container applications"
    bash "${SCRIPT_DIR}/install-docker-compose.sh" || error "Docker-compose installation failed"
    success "Docker Compose has been installed"
}

# Semaphore installation
install_semaphore() {
    print_header "Installing Ansible Semaphore"
    info "Semaphore provides a web UI for managing Ansible playbooks"
    info "This will set up the necessary directories and configurations"
    bash "${SCRIPT_DIR}/install-semaphore.sh" || error "Semaphore installation failed"
    success "Semaphore has been installed"
}

# MOTD installation
install_motd() {
    print_header "Installing HomeLab MOTD"
    info "Setting up the Message of the Day for the homelab"
    bash "${SCRIPT_DIR}/install-motd.sh" || error "MOTD installation failed"
    success "HomeLab MOTD has been installed"
}

main() {
    check_prerequisites
    install_git
    install_motd
    install_python3
    install_pip3
    install_docker
    install_docker_compose
    install_semaphore
    
    if command -v docker >/dev/null 2>&1; then
        echo
        info "Post-installation steps:"
        echo "1. Log out and log back in for docker group membership to take effect"
        echo "2. Verify Docker installation with: docker --version"
        if command -v docker-compose >/dev/null 2>&1; then
            echo "3. Check Semaphore UI at: http://localhost:3000"
            echo "4. Default Semaphore credentials can be found in .env file"
            echo
            warning "Make sure to change default passwords in production environments!"
        fi
    fi
}

main "$@"
