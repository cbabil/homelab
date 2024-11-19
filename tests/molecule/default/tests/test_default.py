import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

def test_pihole_installed(host):
    """Test if Pi-hole is installed and running"""
    pihole = host.file("/usr/local/bin/pihole")
    assert pihole.exists
    assert pihole.mode == 0o755

    ftl = host.service("pihole-FTL")
    assert ftl.is_running
    assert ftl.is_enabled

def test_pihole_web_interface(host):
    """Test if Pi-hole web interface is accessible"""
    lighttpd = host.service("lighttpd")
    assert lighttpd.is_running
    assert lighttpd.is_enabled
    
    assert host.socket("tcp://0.0.0.0:80").is_listening

def test_pihole_gravity(host):
    """Test if gravity database exists"""
    gravity_db = host.file("/etc/pihole/gravity.db")
    assert gravity_db.exists

def test_required_packages(host):
    """Test if required packages are installed"""
    packages = [
        "curl",
        "git",
        "iproute2",
        "whiptail"
    ]
    for package in packages:
        assert host.package(package).is_installed
    