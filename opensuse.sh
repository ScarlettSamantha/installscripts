#!/bin/bash

# Update the system and refresh repositories
echo "Updating system and refreshing repositories..."
sudo zypper refresh --non-interactive

# Add PHP repository
echo "Adding PHP repository..."
sudo zypper addrepo --non-interactive https://download.opensuse.org/repositories/devel:/languages:/php/openSUSE_Tumbleweed/devel:languages:php.repo
sudo rpm --import https://download.opensuse.org/repositories/devel:/languages:/php/openSUSE_Tumbleweed/repodata/repomd.xml.key

# Add Python repository for multiple versions
echo "Adding Python repository for multiple versions..."
sudo zypper addrepo --non-interactive https://download.opensuse.org/repositories/devel:/languages:/python/openSUSE_Tumbleweed/devel:languages:python.repo
sudo rpm --import https://download.opensuse.org/repositories/devel:/languages:/python/openSUSE_Tumbleweed/repodata/repomd.xml.key

# Refresh repositories
echo "Refreshing repositories..."
sudo zypper refresh --non-interactive

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
sudo zypper install -yn php74 php74-devel php74-pear php74-json php74-xml php74-curl php74-mbstring \
php74-openssl php74-zip php74-intl php74-pdo php74-gd php74-ctype php74-tokenizer php74-bcmath

sudo zypper install -yn php82 php82-devel php82-pear php82-json php82-xml php82-curl php82-mbstring \
php82-openssl php82-zip php82-intl php82-pdo php82-gd php82-ctype php82-tokenizer php82-bcmath

sudo zypper install -yn php83 php83-devel php83-pear php83-json php83-xml php83-curl php83-mbstring \
php83-openssl php83-zip php83-intl php83-pdo php83-gd php83-ctype php83-tokenizer php83-bcmath

# Install Composer and PHP tools
echo "Installing Composer and PHP tools..."
sudo zypper install -yn php-pear php-xdebug composer

# Set up alternatives for PHP versions
echo "Setting up alternatives for PHP versions..."
sudo update-alternatives --install /usr/bin/php php /usr/bin/php7.4 74 --force
sudo update-alternatives --install /usr/bin/php php /usr/bin/php8.2 82 --force
sudo update-alternatives --install /usr/bin/php php /usr/bin/php8.3 83 --force

sudo update-alternatives --install /usr/bin/php-config php-config /usr/bin/php-config7.4 74 --force
sudo update-alternatives --install /usr/bin/php-config php-config /usr/bin/php-config8.2 82 --force
sudo update-alternatives --install /usr/bin/php-config php-config /usr/bin/php-config8.3 83 --force

sudo update-alternatives --install /usr/bin/phpize phpize /usr/bin/phpize7.4 74 --force
sudo update-alternatives --install /usr/bin/phpize phpize /usr/bin/phpize8.2 82 --force
sudo update-alternatives --install /usr/bin/phpize phpize /usr/bin/phpize8.3 83 --force

# Install Python 3.8 and Python 3.12
echo "Installing Python 3.8 and Python 3.12..."
sudo zypper install -yn python38 python38-devel python38-pip python38-virtualenv
sudo zypper install -yn python312 python312-devel python312-pip python312-virtualenv

# Install Flask and gunicorn for Python 3.8
echo "Installing Flask and gunicorn for Python 3.8..."
sudo zypper install -yn python38-Flask python38-gunicorn

# Install Flask and gunicorn for Python 3.12
echo "Installing Flask and gunicorn for Python 3.12..."
sudo zypper install -yn python312-Flask python312-gunicorn

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
sudo zypper ar -f https://download.opensuse.org/repositories/security/openSUSE_Tumbleweed/security.repo
sudo zypper refresh --non-interactive

# Install additional security tools
echo "Installing additional security tools..."
sudo zypper install -yn hydra sqlmap

# Install additional Python development tools
echo "Installing additional Python development tools..."
sudo zypper install -yn python38-virtualenv python38-pip \
python312-virtualenv python312-pip

# Install Git and Git tools
echo "Installing Git and Git tools..."
sudo zypper install -yn git git-core git-lfs git-extras

# Final message
echo "Setup complete. Please log out and log back in for group changes to take effect."
