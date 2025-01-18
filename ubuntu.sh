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

# Function to detect GPU type
detect_gpu() {
    if lspci | grep -i 'nvidia' &> /dev/null; then
        echo "⚠️ NVIDIA GPU detected."
        install_gpu_tools "nvidia"
    elif lspci | grep -i 'amd' | grep -i 'vga' &> /dev/null; then
        echo "⚠️ AMD GPU detected."
        install_gpu_tools "amd"
    else
        echo "✅ No NVIDIA or AMD GPU detected."
    fi
}

# Function to install GPU monitoring tools
install_gpu_tools() {
    local gpu_type=$1
    if [ "$gpu_type" = "nvidia" ]; then
        if ! command -v nvidia-smi &> /dev/null; then
            echo "📦 Installing NVIDIA drivers and nvidia-smi..."
            sudo $PACKAGE_MANAGER install -y nvidia-driver-470 nvidia-smi
        else
            echo "✅ nvidia-smi is already installed."
        fi
    elif [ "$gpu_type" = "amd" ]; then
        if ! command -v radeontop &> /dev/null; then
            echo "📦 Installing radeontop for AMD GPU monitoring..."
            sudo $PACKAGE_MANAGER install -y radeontop
        else
            echo "✅ radeontop is already installed."
        fi
    fi
}

append_launcher() {
    local desktop_file=$1
    local config_file="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"

    echo "🔄 Adding $desktop_file to the KDE taskbar..."
    killall plasmashell
    sed -i "/launchers=/ s/$/,applications:$desktop_file/" "$config_file"
    nohup plasmashell >/dev/null 2>&1 & disown

    echo "✅ $desktop_file has been added to the KDE taskbar."
}

get_latest_gl_default() {
  flatpak remote-info --log flathub org.freedesktop.Platform.GL.default \
  | grep -oP '(?<=runtime/org.freedesktop.Platform.GL.default/x86_64/)[0-9]+\.[0-9]+' \
  | sort -V | tail -n 1
}


# Detect and install GPU monitoring tools
detect_gpu

# Adding i386 architecture support
echo "🔄 Adding i386 architecture support..."
sudo dpkg --add-architecture i386
sudo $PACKAGE_MANAGER update

# Installing core system utilities and dependencies
echo "📦 Installing core system utilities and dependencies..."
sudo $PACKAGE_MANAGER install -y apt-transport-https software-properties-common curl wget gnupg lsb-release ca-certificates ubuntu-restricted-extras libfuse2 snapd flatpak

flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

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
sudo flatpak install dev.alextren.Spot --assumeyes

# Installing Discord
echo "💬 Installing Discord..."
cd /tmp
if wget -q -O discord.deb "https://discord.com/api/download?platform=linux&format=deb"; then
    sudo dpkg -i discord.deb || sudo $PACKAGE_MANAGER install -f -y
else
    echo "❌ Failed to download Discord. Skipping installation."
fi

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

sudo $PACKAGE_MANAGER install -y lm-sensors 

echo "🔥 Installing stress testing utilities..."
sudo $PACKAGE_MANAGER install -y s-tui stress

# Install email client
echo "Installing gnome packages"
# Gnome Flatpaks
flatpak install com.belmoussaoui.Authenticator --assumeyes
flatpak install org.gnome.Snapshot --assumeyes
flatpak install com.belmoussaoui.Decoder --assumeyes
flatpak install com.github.ADBeveridge.Raider --assumeyes
flatpak install io.gitlab.adhami3310.Impression --assumeyes
flatpak install com.belmoussaoui.Authenticator --assumeyes
flatpak install org.gnome.dspy --assumeyes
flatpak install org.gnome.Boxes --assumeyes

# Function to append a new launcher to KDE taskbar configuration


echo "🔄 Pinning apps to the KDE 6 taskbar..."
#append_launcher spotify_spotify.desktop
#append_launcher steam.desktop       
#append_launcher discord.desktop
#append_launcher org.kde.krita.desktop
#append_launcher com.obsproject.Studio.desktop

# Final system update and upgrade
echo "🔄 Final system update and upgrade..."        
sudo $PACKAGE_MANAGER update
sudo $PACKAGE_MANAGER upgrade -y

# Enabling TRIM support on NVMe
echo "✂️ Enabling TRIM support on NVMe..."
sudo systemctl enable --now fstrim.timer
sudo systemctl is-active --quiet fstrim.timer && echo "✂️ TRIM is active." || echo "❌ Failed to enable TRIM."

echo "🧹 Cleanup of temp files"
rm -f /tmp/discord.deb /tmp/openrgb.deb /tmp/google-chrome-stable_current_amd64.deb

echo "⚙️ Enable services"
sudo systemctl enable --now snapd docker

echo "🔍 Detecting hardware sensors..."
yes | sudo sensors-detect --auto

echo "🔄 Reloading sensor modules..."
sudo systemctl restart systemd-modules-load.service

sudo add-apt-repository ppa:cappelikan/ppa
sudo $PACKAGE_MANAGER update && sudo $PACKAGE_MANAGER upgrade -y  

LATEST_GL_VERSION=$(get_latest_gl_default)

echo "🎵 Installing Ardour... Please wait."
if [ -n "$LATEST_GL_VERSION" ]; then
  echo "🔍 Installing org.freedesktop.Platform.GL.default version $LATEST_GL_VERSION"
  flatpak install flathub "org.freedesktop.Platform.GL.default//$LATEST_GL_VERSION" --assumeyes
else
  echo "⚠️ Could not determine the latest version. Installing default."
  flatpak install flathub org.freedesktop.Platform.GL.default --assumeyes
fi

sudo flatpak install flathub org.freedesktop.Platform.VulkanLayer.MESA --assumeyes
export MESA_NO_AVX512=1
sudo $PACKAGE_MANAGER install ardour
sudo flatpak install org.pipewire.Helvum --assumeyes

sudo flatpak install io.github.webcamoid.Webcamoid --assumeyes
sudo flatpak install com.bitwig.BitwigStudio --assumeyes
sudo flatpak install md.obsidian.Obsidian --assumeyes
sudo flatpak install org.kde.kdenlive --assumeyes

sudo flatpak install org.freecad.FreeCAD --assumeyes
sudo flatpak install org.onlyoffice.desktopeditors --assumeyes

sudo flatpak install io.github.seadve.Kooha --assumeyes
sudo flatpak install dev.geopjr.Calligraphy --assumeyes
sudo flatpak install io.gitlab.adhami3310.Impression --assumeyes
sudo flatpak install net.mkiol.Jupii --assumeyes
sudo flatpak install io.github.amit9838.mousam --assumeyes
sudo flatpak intsall org.kde.audiotube --assumeyes
sudo flatpak install io.github.realmazharhussain.GdmSettings --assumeyes
sudo flatpak install hu.irl.cameractrls --assumeyes
sudo flatpak install io.gitlab.leesonwai.Sums --assumeyes 
sudo flatpak install com.raggesilver.BlackBox --assumeyes
sudo flatpak install org.gnome.Calculator --assumeyes
sudo flatpak install de.hummdudel.Libellus --assumeyes
sudo flatpak install ru.linux_gaming.PortProton --assumeyes
sudo flatpak install org.gnome.Firmware --assumeyes

# Displaying sensor readings
echo "📊 Displaying sensor readings..."
sensors

# Displaying completion message with Zenity
zenity --info --width=400 --height=425 --title="Installation Complete" \
       --text="✅ All software installations and system configurations have been completed successfully!"

# Prompt for reboot
REBOOT_CHOICE=$(zenity --question --width=600 --height=400 \
    --title="Reboot Required" \
    --text="🔄 Do you want to reboot the system now?\n(Highly recommended)" \
    --ok-label="Reboot" \
    --cancel-label="Later")

if [ "$REBOOT_CHOICE" -eq 0 ]; then
    echo "🔄 Rebooting the system..."
    reboot
else
    zenity --info --width=300 --height=100 --title="Reboot Skipped" \
           --text="❌ Reboot skipped. Please reboot manually later."
fi

echo "✅ Installation and setup complete!"