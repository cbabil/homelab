#!/bin/bash


# Function to check if the script is run as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root. Exiting..."
    fi
}

# Function to check if the OS is supported
check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "${ID}" in
            debian|ubuntu)
                info "${ID} detected..."
                ;;
            *)
                error "${ID} detected, not supported..."
                ;;
        esac
    else
        error "Could not determine OS type..."
    fi
}

# Execute checks
check_root
check_os