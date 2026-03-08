## 🛠️ Step 1: Obtain a Clean Base Image
You need a "pure" Ubuntu image to ensure isolation. There are two ways to do this:

### Option A: Direct Download (Fastest)
Download a fresh RootFS (tarball) from Ubuntu's official cloud images.
1. Download from [Ubuntu Cloud Images](https://cloud-images.ubuntu.com/wsl/noble/current/) (the file ending in `.rootfs.tar.gz`).
2. Save to `C:\temp\ubuntu_clean.tar.gz`.

### Option B: Install & Export (Safest for WSL compatibility)
If you prefer using `wsl --install`, you can create a temporary instance and export it directly to your D: drive.

**From PowerShell (Host):**
```powershell
# 1. Install a temporary clean instance
wsl --install -d Ubuntu-24.04 --name TempBase

# 2. Export it to your preferred Disk location
mkdir D:\WSL\Export
wsl --export TempBase D:\WSL\Export\ubuntu_clean.tar

# 3. Cleanup the temporary instance
wsl --unregister TempBase
```

## 🛠️ Step 2: Import as a New Distribution
This step creates the isolated environment on your D: drive.

**From PowerShell (Host):**
```powershell
# Define paths (Locating in D:\WSL to keep things organized)
$DistroName = "OpenClaw"
$InstallPath = "D:\WSL\OpenClaw"
# Make sure this matches where you saved the file in Step 1!
$ImagePath = "D:\WSL\Export\ubuntu_clean.tar"

# Check if image exists before importing
Test-Path $ImagePath

mkdir $InstallPath
wsl --import $DistroName $InstallPath $ImagePath
```

## � Step 3: Strict Security Isolation (Block Host Access)
By default, WSL mounts all your Windows drives (C:, D:, etc.) under `/mnt/`. For OpenClaw, we want to disable this to prevent the engine from accessing your host files.

### 1. Disable Automount
Inside the **OpenClaw** distribution, create or edit the WSL configuration file:

```bash
# Inside WSL OpenClaw
sudo nano /etc/wsl.conf
```

Add the following content:
```ini
[automount]
enabled = false
mountfstab = true

[network]
generateHosts = true
generateResolvConf = true

[interop]
enabled = false
appendWindowsPath = false
```

> [!IMPORTANT]
> **Why `appendWindowsPath = false`?**
> Since we disabled automount, WSL cannot find your Windows executables. Keeping this enabled causes "Failed to translate" errors at every login. Disabling it ensures a **completely clean Linux-only PATH**, further isolating OpenClaw from your Windows environment.

### 2. Configure Specific Mounts (Restricted)
If you need OpenClaw to access a *specific* folder (e.g., only the game assets), avoid automounting the whole drive. Instead, use `/etc/fstab` for a precise, "least-privilege" mount.

```bash
sudo nano /etc/fstab
```

Example of mounting the OpenClaw workspace from your D: drive:
```text
# <Windows Path>           <Mount Point>   <Type>   <Options>
D:/WSL/mount/OpenClaw      /data           drvfs    defaults,rw,uid=1000,gid=1000  0 0
```
*Note: We use `rw` (Read-Write) here so OpenClaw can save logs and project files.*

---

## 🚀 Step 4: Environment Setup with Pixi
Instead of polluting the system with global packages, use **Pixi** for a reproducible, isolated environment.

### 1. Restart the Distribution (Mandatory)
For the `wsl.conf` security changes to take effect, you **must** terminate the instance from Windows.

**From PowerShell (Host):**
```powershell
wsl --terminate OpenClaw
wsl -d OpenClaw
```

### 2. Initialize Pixi Environment
```bash
# Install Pixi (if not present)
curl -fsSL https://pixi.sh/install.sh | bash
[ -n "$ZSH_VERSION" ] && source ~/.zshrc || source ~/.bashrc

# Initialize environment for OpenClaw
mkdir -p ~/projects/openclaw && cd ~/projects/openclaw
pixi init .
pixi add nodejs
```

## 🎮 Step 5: Install & Run OpenClaw
Since you are using the Node.js version, you can install it directly via npm.

```bash
# Install OpenClaw
pixi run npm i -g openclaw

# Initialize and setup
pixi run openclaw onboard
```

## ⌨️ Step 6: PowerShell Integration (CLI Shortcuts)
To make switching to your new environment as easy as typing `openclaw`, add this to your PowerShell Profile.

**From PowerShell (Host):**
1. Open your profile: `notepad $PROFILE`
2. Add the following function:
```powershell
# Alias for OpenClaw isolated environment
function openclaw {
    wsl -d OpenClaw --cd /home/fancyshenmue/projects/openclaw
}
```
3. Save and reload:
```powershell
. $PROFILE
```

Now you can simply type `openclaw` from any terminal to enter your isolated game engine environment.

---

## 🎨 Step 6: UI/UX Personalization (zsh & p10k)
You can make your isolated environment as beautiful as your main dev environment.

### 1. Change Default Shell to Zsh
```bash
sudo apt install zsh -y
chsh -s $(which zsh)
```

### 2. Install p10k (Manual Method - Simplest)
The simplest way to install p10k without heavy frameworks:

```bash
# Clone the repository
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ~/powerlevel10k

# Add to your .zshrc
echo 'source ~/powerlevel10k/powerlevel10k.zsh-theme' >> ~/.zshrc

# Restart shell and follow the wizard
zsh
```
*If you need to re-run the configuration later, use `p10k configure`.*

### 3. Font Requirements (Crucial!)
> [!IMPORTANT]
> **You do NOT need to install fonts inside WSL.**
> WSL only sends text codes; your **Windows Terminal (or Warp)** is what actually draws the pixels.

1. **Download**: On your **Windows host**, download and install the [MesloLGS NF Fonts](https://github.com/romkatv/dotfiles-public/tree/master/dotfiles/.local/share/fonts/NerdFonts).
2. **Configure**:
   - **Warp**: Go to Settings > Appearance > Text > Font, and select `MesloLGS NF`.
   - **Windows Terminal**: Settings > OpenClaw Profile > Appearance > Font face > `MesloLGS NF`.

---

## 💡 Pro Tips for Management
- **List all distros**: `wsl -l -v`
- **Terminate the distro**: `wsl --terminate OpenClaw` (Stops all processes and saves VRAM).
- **Unregister (Delete everything)**: `wsl --unregister OpenClaw` (Use with caution! This deletes the VHDX).

---

## 🚀 Why This Matters
By using a dedicated distribution for OpenClaw:
1. **Dependency Isolation**: No conflict between your LLM fine-tuning libraries and game engine libraries.
2. **Disk Management**: You can move the entire 100GB+ VHDX to a different drive easily.
3. **Snapshotting**: You can export the `OpenClaw` distro at any time as a backup.
