#!/bin/bash

# Update the system and refresh repositories
echo "Updating system and refreshing repositories..."
sudo zypper refresh -n

# Install development tools and utilities
echo "Installing development tools and utilities..."
sudo zypper install -yn gcc gcc-c++ cmake make git git-core git-lfs git-extras \
python3-pip python3-virtualenv nodejs yasm \
dotnet-sdk-8.0 mono-devel qt6-base-devel python3-qt5-devel python3-qt6-devel castxml bpftrace \
docker docker-compose virtualbox virtualbox-qt wine winetricks keepassxc copyq \
gnuradio gnuradio-devel gr-osmosdr gqrx airspy bladerf hackrf soapysdr rtl_433 rtl-sdr cryfs \
btop nvtop radeontop i2c-tools inxi unar unrar zstd p7zip yt-dlp aria2 pigz \
wireshark nmap john tcpdump net-tools hydra sqlmap \
libreoffice ffmpeg gstreamer

# Install PHP versions and extensions
echo "Installing PHP versions and extensions..."
sudo zypper install -yn php7 php7-devel php7-pear php7-json php7-xml php7-curl php7-mbstring \
php7-openssl php7-zip php7-intl php7-pdo php7-gd php7-ctype php7-tokenizer php7-bcmath

sudo zypper install -yn php8 php8-devel php8-pear php8-json php8-xml php8-curl php8-mbstring \
php8-openssl php8-zip php8-intl php8-pdo php8-gd php8-ctype php8-tokenizer php8-bcmath

# Install Composer and PHP tools
echo "Installing Composer and PHP tools..."
sudo zypper install -yn composer php-pear php-xdebug

# Set up alternatives for PHP versions
echo "Setting up alternatives for PHP versions..."
sudo update-alternatives --install /usr/bin/php php /usr/bin/php7 70 --force
sudo update-alternatives --install /usr/bin/php php /usr/bin/php8 80 --force

sudo update-alternatives --install /usr/bin/php-config php-config /usr/bin/php-config7 70 --force
sudo update-alternatives --install /usr/bin/php-config php-config /usr/bin/php-config8 80 --force

sudo update-alternatives --install /usr/bin/phpize phpize /usr/bin/phpize7 70 --force
sudo update-alternatives --install /usr/bin/phpize phpize /usr/bin/phpize8 80 --force

# Install Python 3.8 and Python 3.11
echo "Installing Python 3.8 and Python 3.11..."
sudo zypper install -yn python38 python38-devel python38-pip python38-virtualenv
sudo zypper install -yn python311 python311-devel python311-pip python311-virtualenv

# Install Flask and gunicorn for Python 3.8
echo "Installing Flask and gunicorn for Python 3.8..."
sudo pip3.8 install --quiet Flask gunicorn

# Install Flask and gunicorn for Python 3.11
echo "Installing Flask and gunicorn for Python 3.11..."
sudo pip3.11 install --quiet Flask gunicorn

# Install Flatpak and add Flathub repository
echo "Installing Flatpak and adding Flathub repository..."
sudo zypper install -yn flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install applications via Flatpak
echo "Installing applications via Flatpak..."
flatpak install -y --noninteractive flathub com.jetbrains.PhpStorm
flatpak install -y --noninteractive flathub com.jetbrains.PyCharm-Professional
flatpak install -y --noninteractive flathub com.visualstudio.code
flatpak install -y --noninteractive flathub md.obsidian.Obsidian
flatpak install -y --noninteractive flathub rest.insomnia.Insomnia
flatpak install -y --noninteractive flathub com.discordapp.Discord
flatpak install -y --noninteractive flathub org.kde.neochat
flatpak install -y --noninteractive flathub com.microsoft.Teams
flatpak install -y --noninteractive flathub com.heidisql.HeidiSQL

# Install Blender, Krita, FreeCAD via Flatpak
echo "Installing Blender, Krita, and FreeCAD..."
flatpak install -y --noninteractive flathub org.blender.Blender
flatpak install -y --noninteractive flathub org.kde.krita
flatpak install -y --noninteractive flathub org.freecadweb.FreeCAD

# Install ddev
echo "Installing ddev..."
wget -q https://github.com/drud/ddev/releases/download/v1.21.4/ddev_v1.21.4_linux.amd64.rpm
sudo rpm -ivh --nodigest --nosignature ddev_v1.21.4_linux.amd64.rpm

# Install Google Chrome
echo "Installing Google Chrome..."
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo zypper install -yn ./google-chrome-stable_current_x86_64.rpm

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

# Add security repository for additional tools
echo "Adding security repository for additional tools..."
sudo zypper ar -f -n security https://download.opensuse.org/repositories/security/openSUSE_Tumbleweed/ security
sudo zypper refresh -n

# Install additional security tools
echo "Installing additional security tools..."
sudo zypper install -yn hydra sqlmap

# Install Git and Git tools
echo "Installing Git and Git tools..."
sudo zypper install -yn git git-core git-lfs git-extras

# Final message
echo "Setup complete. Please log out and log back in for group changes to take effect."
