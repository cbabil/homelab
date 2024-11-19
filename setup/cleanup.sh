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

print_header() {
    echo
    info "================================================================"
    info " ${1}"
    info "================================================================"
    echo
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root. Exiting..."
fi

cleanup_git() {
    print_header "Removing Git"
    apt-get remove --purge -y git
    apt-get autoremove -y
    rm -rf ~/.git
    success "Git has been removed"
}

cleanup_python3() {
    print_header "Removing Python3"
    apt-get remove --purge -y python3 python3-pip python3-dev
    apt-get autoremove -y
    rm -rf ~/.local/lib/python*
    success "Python3 has been removed"
}

cleanup_pip3() {
    print_header "Removing Pip3"
    apt-get remove --purge -y python3-pip
    apt-get autoremove -y
    rm -rf ~/.cache/pip
    success "Pip3 has been removed"
}

cleanup_docker() {
    print_header "Removing Docker"
    # Stop all running containers
    if command -v docker >/dev/null 2>&1; then
        docker stop $(docker ps -aq) 2>/dev/null || true
        docker rm $(docker ps -aq) 2>/dev/null || true
    fi
    
    # Remove Docker packages
    apt-get remove --purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    apt-get autoremove -y
    
    # Remove Docker files and directories
    rm -rf /var/lib/docker
    rm -rf /var/lib/containerd
    rm -rf ~/.docker
    
    # Remove Docker group
    groupdel docker 2>/dev/null || true
    
    success "Docker has been removed"
}

cleanup_docker_compose() {
    print_header "Removing Docker Compose"
    rm -f /usr/local/bin/docker-compose
    success "Docker Compose has been removed"
}

cleanup_semaphore() {
    print_header "Removing Ansible Semaphore"
    # Stop and remove Semaphore containers
    if command -v docker >/dev/null 2>&1; then
        docker stop semaphore mysql 2>/dev/null || true
        docker rm semaphore mysql 2>/dev/null || true
        docker volume rm semaphore-mysql 2>/dev/null || true
    fi
    
    # Remove Semaphore directories
    rm -rf ansible/semaphore
    rm -rf /etc/semaphore
    
    success "Semaphore has been removed"
}

cleanup_all() {
    print_header "Removing All Components"
    cleanup_semaphore
    cleanup_docker_compose
    cleanup_docker
    cleanup_pip3
    cleanup_python3
    cleanup_git
    success "All components have been removed"
}

show_usage() {
    echo "Usage: $0 [OPTION]"
    echo "Clean up homelab components"
    echo
    echo "Options:"
    echo "  -a, --all            Remove all components"
    echo "  -g, --git            Remove Git"
    echo "  -p, --python         Remove Python3"
    echo "  -i, --pip            Remove Pip3"
    echo "  -d, --docker         Remove Docker"
    echo "  -c, --compose        Remove Docker Compose"
    echo "  -s, --semaphore      Remove Ansible Semaphore"
    echo "  -h, --help           Display this help message"
    echo
    echo "Example: $0 --docker --semaphore"
}

# No arguments provided
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Parse command line arguments
while [ $# -gt 0 ]; do
    case "$1" in
        -a|--all)
            warning "This will remove all components. Are you sure? (y/N)"
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                cleanup_all
            fi
            ;;
        -g|--git)
            cleanup_git
            ;;
        -p|--python)
            cleanup_python3
            ;;
        -i|--pip)
            cleanup_pip3
            ;;
        -d|--docker)
            cleanup_docker
            ;;
        -c|--compose)
            cleanup_docker_compose
            ;;
        -s|--semaphore)
            cleanup_semaphore
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
    shift
done

print_header "Cleanup Complete!"
info "System may need to be rebooted for all changes to take effect" 