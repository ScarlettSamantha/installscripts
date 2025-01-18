#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🔄 Adding i386 architecture support..."
sudo dpkg --add-architecture i386
sudo apt update

echo "📦 Installing essential 32-bit libraries..."
sudo apt install -y libc6:i386 libstdc++6:i386 libgl1-mesa-glx:i386 libgl1-mesa-dri:i386

echo "📦 Installing core system utilities and dependencies..."
sudo apt install -y apt-transport-https software-properties-common curl wget gnupg lsb-release ca-certificates ubuntu-restricted-extras libfuse2

echo "🛠 Installing development tools and kernel module support..."
sudo apt install -y build-essential dkms

echo "➕ Adding OBS Studio PPA..."
sudo add-apt-repository -y ppa:obsproject/obs-studio
sudo apt update

echo "⬆️ Upgrading existing packages..."
sudo apt upgrade -y

echo "🎨 Installing creative and media software..."
sudo apt install -y krita vlc gimp mesa-utils fonts-firacode

echo "🎵 Installing Spotify..."
curl -sS https://download.spotify.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb http://repository.spotify.com stable non-free" | sudo tee /etc/apt/sources.list.d/spotify.list
sudo apt update
sudo apt install -y spotify-client

echo "💬 Installing Discord..."
cd /tmp
wget -q -O discord.deb "https://discord.com/api/download?platform=linux&format=deb"
sudo dpkg -i discord.deb || sudo apt install -f -y

echo "💬 Installing OpenRGB..."
wget -q -O openrgb.deb "https://gitlab.com/CalcProgrammer1/OpenRGB/-/jobs/artifacts/master/download?job=Linux+amd64+.deb+%28Debian+Bookworm%29"
sudo dpkg -i openrgb.deb || sudo apt install -f -y

echo "🎮 Installing optional gaming tools..."
sudo apt install -y steam gamemode vulkan-utils

echo "🛠 Installing system utilities..."
sudo apt install -y ntfs-3g arp-scan nmap exfat-fuse exfat-utils btrfs-progs fuse fling exfatprogs autoconf libtool pkg-config smartmontools nvme-cli hdparm

echo "🖥 Installing productivity tools..."
sudo apt install -y remmina transmission-qt git mc docker.io htop btop

echo "🐍 Installing Python development tools..."
sudo apt install -y python3 python3-dev python3-pip python3-venv python3-flask python3-gunicorn

echo "🍷 Installing Wine and Proton tools..."
sudo apt install -y fonts-wine proton-call protontricks wine wine32 wine64 winetricks

echo "🌐 Installing Google Chrome..."
cd /tmp
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo apt install -f -y

echo "🔄 Final system update and upgrade..."
sudo apt update -y
sudo apt upgrade -y

echo "✅ Installation and setup complete!"
