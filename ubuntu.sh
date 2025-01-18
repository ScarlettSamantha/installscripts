#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
sudo mkdir -p /etc/apt/keyrings
export DEBIAN_FRONTEND=noninteractive

echo "🔄 Adding i386 architecture support..."
sudo dpkg --add-architecture i386
sudo apt update

echo "📦 Installing core system utilities and dependencies..."
sudo apt install -y apt-transport-https software-properties-common curl wget gnupg lsb-release ca-certificates ubuntu-restricted-extras libfuse2 snapd

echo "🛠 Installing development tools and kernel module support..."
sudo apt install -y build-essential dkms clang

echo "➕ Adding OBS Studio PPA..."
sudo add-apt-repository -y ppa:obsproject/obs-studio
sudo apt update

echo "⬆️ Upgrading existing packages..."
sudo apt upgrade -y

echo "🎨 Installing creative and media software..."
sudo apt install -y krita vlc gimp mesa-utils fonts-firacode obs-studio

echo "🎵 Installing Spotify..."
sudo snap install spotify

echo "💬 Installing Discord..."
cd /tmp
wget -q -O discord.deb "https://discord.com/api/download?platform=linux&format=deb"
sudo dpkg -i discord.deb || sudo apt install -f -y

echo "💬 Installing OpenRGB..."
wget -q -O openrgb.deb https://openrgb.org/releases/release_0.9/openrgb_0.9_amd64_bookworm_b5f46e3.deb
sudo dpkg -i openrgb.deb || sudo apt install -f -y

echo "🎮 Installing optional gaming tools..."
sudo apt install -y gamemode libvulkan1

echo "🎮 Installing steam..."
sudo snap install steam --classic

echo "🛠 Installing system utilities..."
sudo apt install -y ntfs-3g arp-scan nmap exfat-fuse btrfs-progs fuse fling exfatprogs autoconf libtool pkg-config smartmontools nvme-cli hdparm

echo "💻 Installing productivity tools..."
sudo apt install -y remmina transmission-qt git mc docker.io htop btop

echo "🐍 Installing Python development tools..."
sudo apt install -y python3 python3-dev python3-pip python3-venv python3-flask python3-gunicorn

echo "🍹 Installing Wine and Proton tools..."
sudo apt install -y protontricks wine wine32 wine64 winetricks

echo "🔑 Installing Keychain for SSH key management..."
sudo apt install -y keychain

echo "🌐 Installing Google Chrome..."
cd /tmp
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo apt install -f -y

# Function to append a new launcher to KDE taskbar configuration
append_launcher() {
    local desktop_file=$1
    local config_file="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"

    echo "🔄 Adding $desktop_file to the KDE taskbar..."
    kquitapp6 plasmashell
    sed -i "/launchers=/ s/$/,applications:$desktop_file/" "$config_file"
    kstart6 plasmashell

    echo "✅ $desktop_file has been added to the KDE taskbar."
}

echo "🔄 Pinning Spotify, Steam, Discord, OBS Studio, and Krita to the KDE 6 taskbar..."
append_launcher spotify_spotify.desktop
append_launcher steam.desktop
append_launcher discord.desktop
append_launcher org.kde.krita.desktop
append_launcher com.obsproject.Studio.desktop

echo "🔄 Final system update and upgrade..."
sudo apt update -y
sudo apt upgrade -y

echo "✅ Installation and setup complete!"

# Prompt for reboot
read -rp "🔄 Do you want to reboot the system now (heavily recommended)? [Y/n]: " REBOOT_CHOICE
REBOOT_CHOICE=${REBOOT_CHOICE:-Y}

if [[ "$REBOOT_CHOICE" =~ ^[Yy]$ ]]; then
    echo "🔄 Rebooting the system..."
    sudo reboot
else
    echo "❌ Reboot skipped. You can reboot manually later."
fi
