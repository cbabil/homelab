#!/bin/bash

print_header "Installing HomeLab MOTD"
info "Configuring SSH settings for MOTD"

# Update SSH configuration
if [ -f /etc/ssh/sshd_config ]; then
    sed -i 's/^#*UsePAM.*/UsePAM no/' /etc/ssh/sshd_config || error "Failed to update UsePAM setting"
    sed -i 's/^#*PrintMOTD.*/PrintMOTD no/' /etc/ssh/sshd_config || error "Failed to update PrintMOTD setting"
    sed -i 's/^#*PrintLastLog.*/PrintLastLog no/' /etc/ssh/sshd_config || error "Failed to update PrintLastLog setting"
    info "SSH configuration updated successfully"
else
    error "SSH config file not found at /etc/ssh/sshd_config"
fi

# Download and setup MOTD script
info "Downloading and setting up MOTD script"
wget https://raw.githubusercontent.com/cbabil/motd/master/homelab/10-uname || error "Failed to download MOTD script"
mv 10-uname /etc/motd.sh || error "Failed to move MOTD script"
chmod +x /etc/motd.sh || error "Failed to set executable permissions"
rm -f /etc/motd || error "Failed to remove default MOTD"

# Add MOTD to profile
info "Adding MOTD to profile"
printf "# MOTD\n/etc/motd.sh\n" | tee -a /etc/profile > /dev/null 2>&1 || error "Failed to update profile"

# Restart SSH service
info "Restarting SSH service"
systemctl restart sshd || error "Failed to restart SSH service"