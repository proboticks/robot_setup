# TurtleBot 4 Fleet Deployment Guide

This directory contains the automation tools and configuration files for deploying a fleet of 15 TurtleBot 4 (Raspberry Pi 4B) units. By using **cloud-init**, we customize each robot's identity and network settings without ever needing to plug in a monitor or keyboard.

---

## File Descriptions

### 1. `user-data` (Identity & Logic)
This file handles the **"Who am I?"** and **"What do I do?"** of the robot.
* **`hostname`**: Sets the unique name (e.g., `turtlebot01`).
* **`manage_etc_hosts`**: Automatically updates `/etc/hosts`. This ensures the robot knows its own name, preventing `sudo` lag and ROS 2 node resolution errors.
* **`ssh_pwauth: true`**: Allows password-based SSH login (User: `ubuntu` / Pass: `turtlebot`).
* **`chpasswd`**: Ensures the password is set correctly on the first boot.
* **`runcmd`**: A list of commands that run **once** on first boot. We use this to inject the `ROS_DOMAIN_ID` and `ROBOT_NAMESPACE` into the `/etc/turtlebot4_setup/config.bash` file.

### 2. `network-config` (Connectivity)
This file handles the **"How do I talk?"** part of the robot.
* **`eth0`**: Configured for the internal bridge to the iRobot Create® 3 base.
* **`wlan0`**: Configured with a **Static IP** (e.g., `192.168.1.101`).
* **`access-points`**: Contains the Wi-Fi credentials for the lab.

---

## Deployment Workflow

### Phase 1: Prepare the Master SD Card
1. Set up one "Master" TurtleBot exactly how you want it (packages, scripts, etc.).
2. Run the **Prep Script** to wipe unique IDs:
   - Delete SSH host keys: `sudo rm /etc/ssh/ssh_host_*`
   - Wipe machine-id: `sudo truncate -s 0 /etc/machine-id`
   - Clean cloud-init: `sudo cloud-init clean --logs`
3. Power down and pull the SD card.
4. Create an image (`.img`) on your PC and use **PiShrink** to make it small.

### Phase 2: Mass Generate Configs
1. Run the `generate_configs.py` script on your PC.
2. This will create a `configs/` folder with subfolders `bot01` through `bot15`.

### Phase 3: Flashing and Branding
1. **Flash**: Flash the Golden Image to an SD card.
2. **Mount**: Keep the card in your PC. Open the `system-boot` partition.
3. **Inject**: 
   - Copy `user-data` and `network-config` from `configs/botXX/`.
   - **Overwrite** the existing files in the `system-boot` partition.
4. **Boot**: Insert the card into the robot and power on.

---

## Troubleshooting & Verification

### The "First Boot" Process
On the first boot, the robot will:
1. Resize the SD card partition to full size.
2. Generate brand new, unique SSH host keys.
3. Apply the Static IP and Hostname.
4. Reboot the TurtleBot 4 ROS services.
**Note:** This first boot can take 2-3 minutes. Do not pull the power.

### Post-Boot Checks
Once the robot is on the network, verify the setup from your laptop:

1. **Ping the bot:** `ping turtlebot01.local` or `ping 192.168.1.101`
2. **Check ROS 2 Environment:**
   `ssh ubuntu@192.168.1.101 'export | grep ROS'`
---
