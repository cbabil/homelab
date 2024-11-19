#/bin/bash

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

error() {
    printf '%s' "${RED}Error: ${1}${NC}" >&2
    printf '\n'
    exit 1
}

info() {
    printf '%s' "${BLUE}Info: ${1}${NC}"
    printf '\n'
}

success() {
    printf '%s' "${GREEN}Success: ${1}${NC}"
    printf '\n'
}

warning() {
    printf '%s' "${YELLOW}Warning: ${1}${NC}"
    printf '\n'
}

# Check if we are on a supported OS
case "${ID}" in
    debian|ubuntu)
        info "${ID} detected..."
        ;;
    *)
        error "${ID} detected, not supported..."
        ;;
esac

# Check if we are root
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root. Exiting..."
    exit 1
    return
fi

# Check if we have git
if! command -v git >/dev/null 2>&1; then
    warning "Git is not installed. Installing...."
else
    success "Git is already installed..."
fi

# Check if we have pip3
if! command -v pip3 >/dev/null 2>&1; then
    warning "Pip3 is not installed. Installing..."
else
    success "Pip3 is already installed..."
fi

# Check if we have python3
if! command -v python3 >/dev/null 2>&1; then
    warning "Python3 is not installed. Installing..."
else
    success "Python3 is already installed..."
fi

# Check if we have docker
if! command -v docker >/dev/null 2>&1; then
    warning "Docker is not installed. Installing..."
else
    success "Docker is already installed..."
fi

# Check if we have docker-compose
if! command -v docker-compose >/dev/null 2>&1; then
    warning "Docker-compose is not installed. Installing..."
else
    success "Docker-compose is already installed..."
fi

# Check if we have Ansible Semaphore 
if! command -v    >/dev/null 2>&1; then
    warning "Ansible Semaphore is not installed. Installing..."
else
    success "Ansible Semaphore is already installed..."
fi
