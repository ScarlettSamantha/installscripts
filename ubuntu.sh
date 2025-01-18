#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e


# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script must be run as root. Prompting for root access..."
    exec sudo bash "$0" "$@"
    exit
fi

# Check if Zenity is installed for GUI prompts
if ! command -v zenity &> /dev/null; then
    echo "📦 Installing zenity for GUI dialogs..."
    apt update
    apt install -y zenity
fi

# Check if nala is installed
if command -v nala &> /dev/null; then
    PACKAGE_MANAGER="nala"
    echo "📦 Using Nala for package management."
else
    PACKAGE_MANAGER="apt"
    echo "📦 Nala not found. Falling back to APT."
fi

sudo mkdir -p /etc/apt/keyrings
export DEBIAN_FRONTEND=noninteractive

# Install nala if not already installed
if [ "$PACKAGE_MANAGER" = "apt" ]; then
    sudo apt update
    sudo apt install -y nala
    if command -v nala &> /dev/null; then
        PACKAGE_MANAGER="nala"
        echo "📦 Nala installed successfully. Switching to Nala."
    fi
fi

# Adding i386 architecture support
echo "🔄 Adding i386 architecture support..."
sudo dpkg --add-architecture i386
sudo $PACKAGE_MANAGER update

# Installing core system utilities and dependencies
echo "📦 Installing core system utilities and dependencies..."
sudo $PACKAGE_MANAGER install -y apt-transport-https software-properties-common curl wget gnupg lsb-release ca-certificates ubuntu-restricted-extras libfuse2 snapd

# Installing development tools and kernel module support
echo "🛠 Installing development tools and kernel module support..."
sudo $PACKAGE_MANAGER install -y build-essential dkms clang

# Adding OBS Studio PPA
echo "➕ Adding OBS Studio PPA..."
sudo add-apt-repository -y ppa:obsproject/obs-studio
sudo $PACKAGE_MANAGER update

# Upgrading existing packages
echo "⬆️ Upgrading existing packages..."
sudo $PACKAGE_MANAGER upgrade -y

# Installing creative and media software
echo "🎨 Installing creative and media software..."
sudo $PACKAGE_MANAGER install -y krita vlc gimp mesa-utils fonts-firacode obs-studio

# Installing Spotify
echo "🎵 Installing Spotify..."
sudo snap install spotify

# Installing Discord
echo "💬 Installing Discord..."
cd /tmp
wget -q -O discord.deb "https://discord.com/api/download?platform=linux&format=deb"
sudo dpkg -i discord.deb || sudo $PACKAGE_MANAGER install -f -y

# Installing OpenRGB
echo "💬 Installing OpenRGB..."
wget -q -O openrgb.deb https://openrgb.org/releases/release_0.9/openrgb_0.9_amd64_bookworm_b5f46e3.deb
sudo dpkg -i openrgb.deb || sudo $PACKAGE_MANAGER install -f -y

# Installing optional gaming tools
echo "🎮 Installing optional gaming tools..."
sudo $PACKAGE_MANAGER install -y gamemode libvulkan1

# Installing Steam
echo "🎮 Installing Steam..."
sudo snap install steam --classic

# Installing system utilities
echo "🛠 Installing system utilities..."
sudo $PACKAGE_MANAGER install -y ntfs-3g arp-scan nmap exfat-fuse btrfs-progs fuse fling exfatprogs autoconf libtool pkg-config smartmontools nvme-cli hdparm

# Installing productivity tools
echo "💻 Installing productivity tools..."
sudo $PACKAGE_MANAGER install -y remmina transmission-qt git mc docker.io htop btop

# Installing Python development tools
echo "🐍 Installing Python development tools..."
sudo $PACKAGE_MANAGER install -y python3 python3-dev python3-pip python3-venv python3-flask python3-gunicorn

# Installing Wine and Proton tools
echo "🍹 Installing Wine and Proton tools..."
sudo $PACKAGE_MANAGER install -y protontricks wine wine32 wine64 winetricks

# Installing Keychain for SSH key management
echo "🔑 Installing Keychain for SSH key management..."
sudo $PACKAGE_MANAGER install -y keychain

# Installing Google Chrome
echo "🌐 Installing Google Chrome..."
cd /tmp
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo $PACKAGE_MANAGER install -f -y

# Function to append a new launcher to KDE taskbar configuration
append_launcher() {
    local desktop_file=$1
    local config_file="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"

    echo "🔄 Adding $desktop_file to the KDE taskbar..."
    killall plasmashell
    sed -i "/launchers=/ s/$/,applications:$desktop_file/" "$config_file"
    nohup plasmashell >/dev/null 2>&1 & disown

    echo "✅ $desktop_file has been added to the KDE taskbar."
}

echo "🔄 Pinning apps to the KDE 6 taskbar..."
append_launcher spotify_spotify.desktop
append_launcher steam.desktop       
append_launcher discord.desktop
append_launcher org.kde.krita.desktop
append_launcher com.obsproject.Studio.desktop

# Final system update and upgrade
echo "🔄 Final system update and upgrade..."
sudo $PACKAGE_MANAGER update -y
sudo $PACKAGE_MANAGER upgrade -y

# Displaying completion message with Zenity
zenity --info --width=800 --height=400 --title="Installation Complete" \
       --text="✅ All software installations and system configurations have been completed successfully!"

# Prompt for reboot
REBOOT_CHOICE=$(zenity --question --width=800 --height=600 \
    --title="Reboot Required" \
    --text="🔄 Do you want to reboot the system now?\n(Highly recommended)" \
    --ok-label="Reboot" \
    --cancel-label="Later")

if [ $? -eq 0 ]; then
    echo "🔄 Rebooting the system..."
    reboot
else
    zenity --info --width=300 --height=100 --title="Reboot Skipped" \
           --text="❌ Reboot skipped. Please reboot manually later."
fi

echo "✅ Installation and setup complete!"