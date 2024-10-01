#!/bin/bash

# Update the system and refresh repositories
echo "Updating system and refreshing repositories..."
sudo zypper -n refresh

# Add necessary repositories
echo "Adding necessary repositories..."

# devel:languages:python for multiple Python versions
sudo zypper ar -f https://download.opensuse.org/repositories/devel:/languages:/python/openSUSE_Leap_15.5/
sudo zypper ar -f https://download.opensuse.org/repositories/devel:/languages:/php:/php74/openSUSE_Leap_15.5/ php74
sudo zypper ar -f https://download.opensuse.org/repositories/devel:/languages:/php:/php82/openSUSE_Leap_15.5/ php82
sudo zypper ar -f https://download.opensuse.org/repositories/devel:/languages:/php:/php83/openSUSE_Leap_15.5/ php83
sudo zypper ar -f https://download.opensuse.org/repositories/hardware:/sdr/openSUSE_Leap_15.5/hardware:sdr.repo
sudo zypper ar -f https://packages.microsoft.com/sles/15/prod
sudo zypper --gpg-auto-import-keys ref

# Refresh repositories
echo "Refreshing repositories..."
sudo zypper -n refresh

# Install development tools and utilities
echo "Installing development tools and utilities..."
sudo zypper install -yn gcc gcc-c++ cmake make git git-core git-lfs \
python3-pip python3-virtualenv nodejs16 \
dotnet-sdk-6.0 mono-devel qt6-devel python310-qt6-devel \
docker docker-compose virtualbox virtualbox-qt wine winetricks keepassxc \
btop nvtop radeontop i2c-tools inxi unar unrar zstd p7zip \
yt-dlp aria2 pigz wireshark nmap john tcpdump net-tools \
libreoffice ffmpeg gstreamer php83 php83-xml php83-json php82 php82-xml php82-json

# Note: Some packages may not be available in Leap 15.5 and are commented out
# Removed packages: git-extras, castxml, bpftrace, copyq, bladerf, hackrf, soapysdr, rtl_433, rtl-sdr, cryfs

# Install PHP versions and extensions
echo "Installing PHP versions and extensions..."
# PHP 7 (Default in Leap 15.5)
sudo zypper install -yn php7 php7-devel php7-pear php7-json php7-xml \
php7-curl php7-mbstring php7-openssl php7-zip php7-intl php7-pdo php7-gd \
php7-ctype php7-tokenizer php7-bcmath composer

# PHP 8 (Not available in Leap 15.5 default repos)
# Alternative: Install PHP 8 via source or third-party repositories (not recommended)
echo "PHP 8 is not available in the default repositories for openSUSE Leap 15.5."

# Install Composer and PHP tools
echo "Installing Composer and PHP tools..."
sudo zypper install -yn composer php7-pear

# Set up alternatives for PHP versions (Only PHP 7 is available)
echo "Setting up alternatives for PHP versions..."
sudo update-alternatives --install /usr/bin/php php /usr/bin/php7 70 --force

# Install Python 3.8 and Python 3.10
echo "Installing Python 3.8 and Python 3.10..."
sudo zypper install -yn python38 python38-devel python38-pip python38-virtualenv
sudo zypper install -yn python310 python310-devel python310-pip python310-virtualenv

# Install Flask and gunicorn for Python 3.8
echo "Installing Flask and gunicorn for Python 3.8..."
sudo pip3.8 install --quiet Flask gunicorn

# Install Flask and gunicorn for Python 3.10
echo "Installing Flask and gunicorn for Python 3.10..."
sudo pip3.10 install --quiet Flask gunicorn

# Install Flatpak and add Flathub repository
echo "Installing Flatpak and adding Flathub repository..."
sudo zypper install -yn flatpak
sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install applications via Flatpak
echo "Installing applications via Flatpak..."
flatpak install -y flathub com.jetbrains.PhpStorm
flatpak install -y flathub com.jetbrains.PyCharm-Professional
flatpak install -y flathub com.visualstudio.code
flatpak install -y flathub md.obsidian.Obsidian
flatpak install -y flathub rest.insomnia.Insomnia
flatpak install -y flathub com.discordapp.Discord
flatpak install -y flathub org.kde.neochat
flatpak install -y flathub com.microsoft.Teams
flatpak install -y flathub com.heidisql.HeidiSQL
flatpak install -y flathub org.blender.Blender
flatpak install -y flathub org.kde.krita
flatpak install -y flathub org.freecadweb.FreeCAD

# Install ddev
echo "Installing ddev..."
wget -q https://github.com/drud/ddev/releases/download/v1.21.4/ddev_v1.21.4_linux.amd64.rpm
sudo rpm -ivh ddev_v1.21.4_linux.amd64.rpm

# Install Google Chrome
echo "Installing Google Chrome..."
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo zypper install -yn google-chrome-stable_current_x86_64.rpm

# Install Metasploit Framework
echo "Installing Metasploit Framework..."
curl -s https://raw.githubusercontent.com/rapid7/metasploit-framework/master/msfinstall -o msfinstall
chmod +x msfinstall
sudo ./msfinstall

# Install magic-wormhole and pre-commit via pip
echo "Installing magic-wormhole and pre-commit via pip..."
sudo pip3 install --quiet magic-wormhole pre-commit

# Enable and start Docker service
echo "Enabling and starting Docker service..."
sudo systemctl enable --now docker
sudo usermod -aG docker $USER

# Add user to vboxusers group for VirtualBox
echo "Adding user to vboxusers group for VirtualBox..."
sudo usermod -aG vboxusers $USER

# Install Snap and enable services
echo "Installing Snap and enabling services..."
sudo zypper install -yn snapd
sudo systemctl enable --now snapd
sudo systemctl enable --now snapd.apparmor
sudo ln -s /var/lib/snapd/snap /snap

# Install Git and Git tools
echo "Installing Git and Git tools..."
sudo zypper install -yn git git-core git-lfs

# Final message
echo "Setup complete. Please log out and log back in for group changes to take effect."
