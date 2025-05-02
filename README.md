# Package Installer

A terminal-based, curses-powered TUI that makes it easy to bulk install, uninstall and manage common developer and productivity packages on Ubuntu.

## 🔍 Overview

This app presents a simple menu-driven interface to:

1. **Select** your distro backend (APT, Snap, Flatpak, or raw/manual installers).  
2. **Browse** logical categories (e.g. shells & editors, CLI productivity, container and orchestration tools, multimedia & graphics, cloud CLIs, games, security & networking, Python stacks, database servers, system utilities, and more).  
3. **Toggle** individual or whole-category selections.  
4. **Install** (or uninstall) all selected packages with progress bars, spinners, and detailed logs.

Under the hood it uses Python’s `curses` module for the UI, `concurrent.futures` to preload install-status checks, and simple shell commands (`apt`, `snap`, `flatpak`, `dpkg`) to drive installations.

---

## 🚀 Getting Started

### Prerequisites

- **Ubuntu (or Debian-based)** system  
- **PIP**
- **Python 3.12+**

### Installation

Clone this repo:  
    
    git clone https://github.com/ScarlettSamantha/installscripts  
    cd installscripts  

### Usage
    pip3 install -r requirements.txt
    python3 main.py
---

## 📦 What’s Included

Rather than hard-coding every single package here, the default `packages.json` groups popular tools into high-level categories:

- **Shells & Editors** (e.g. zsh, fish, vim, emacs)  
- **CLI Productivity** (curl, wget, fzf, ripgrep, bat, jq, httpie…)  
- **Dev Runtimes & Frameworks** (Node.js, Java SDK, .NET, Go, Python environments…)  
- **Container & Orchestration** (Docker, Podman, Kubernetes CLIs)  
- **Monitoring & Diagnostics** (htop, nethogs, netdata…)  
- **Backup & Recovery** (borg, restic, timeshift…)  
- **Cloud CLIs** (AWS, Azure, GCP)  
- **Games** (open-source titles via APT, Snap or Flatpak)  
- **Security & Networking** (nmap, wireguard, fail2ban…)  
- **Virtualization & VMs** (QEMU, libvirt, LXD, Vagrant)  
- **Multimedia & Graphics** (GIMP, VLC, OBS, Inkscape…)  
- **Fonts & UI Themes**  
- **Printing & Power Management**  
- **System Utilities** (filesystems, disk tools, sensors…)  
- **Databases** (PostgreSQL, MySQL, Redis, MongoDB)  
- **Compression & Archiving**  
- **Terminal Enhancements** (tmux, screen…)  
- **Plus** curated Snap and Flatpak application bundles, and “Raw” manual-download installers (Chrome, Discord, Zoom, etc.)

You can easily extend or remodel categories by editing `packages.json` to suit your workflow.
