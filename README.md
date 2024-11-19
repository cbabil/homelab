# homelab

1. Install Bookworm on your raspberry pi 5 (https://www.raspberrypi.com/software/operating-systems/)

2. Update and upgrade your system
sudo apt-get update -y
sudo apt-get upgrade -y

2. Install Docker Engine

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker packages
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin



3. Install docker-compose


4. Clone this repo



5. Run `docker-compose up -d`

# make sure the .env file contains the following variables without quotes around the values
# MYSQL
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DB=semaphore
MYSQL_DB_HOST=127.0.0.1
MYSQL_DB_PORT=3306

# SEMAPHORE
SEMAPHORE_ADMIN=admin
SEMAPHORE_ADMIN_PASSWORD=password
SEMAPHORE_ADMIN_NAME=admin
SEMAPHORE_ADMIN_EMAIL=admin@localhost
#
# create with head -c32 /dev/urandom | base64
SEMAPHORE_ACCESS_KEY_ENCRYPTION=<MYACCESS_KEY>


# You need to define your inventory in a text file and put it
# in inventory directory
[homelab]
pihole ansible_host=10.0.5.254



# generate the ssh key
ssh-keygen -t rsa -b 4096




inventory 
secure auth to servers
create playbooks (store on github)
environments


workflow
---------

Install docker
Install ansible/semaphore
Create inventory and update inventory in semaphore
Load playbooks



| Application   | Description   | Folder            |
| ------------- | ------------- | ------------------|
| Semaphore     | Ansible UI    | ansible/semaphore |
| Content Cell  | Content Cell  |                   |


