import os

# --- CONFIGURATION ---
NUM_BOTS = 15
WIFI_SSID = "Your_WiFi_Name"
WIFI_PASS = "Your_Password"
BASE_IP = "192.168.1."  # The prefix for your static IPs
START_IP_SUFFIX = 101   # Bot 1 will be .101, Bot 2 .102, etc.
GATEWAY = "192.168.1.1"
DNS = "8.8.8.8"

# --- GENERATION ---
def generate_configs():
    for i in range(1, NUM_BOTS + 1):
        # Configuration Variables
        bot_id_str = f"{i:02d}" # Formats as 01, 02 (Used for Hostname)
        bot_id_int = i          # Formats as 1, 2 (Used for ID file, SSID, and ROS_DOMAIN_ID)
        
        hostname = f"turtlebot{bot_id_str}"
        ip_addr = f"{BASE_IP}{START_IP_SUFFIX + i - 1}"
        
        # Create a directory for this bot's files
        folder = f"configs/bot{bot_id_str}"
        os.makedirs(folder, exist_ok=True)

        # 1. Generate user-data (Updated with ROS_DOMAIN_ID logic)
        user_data_content = f"""#cloud-config
hostname: {hostname}
manage_etc_hosts: true
ssh_pwauth: true
chpasswd:
  list: |
    ubuntu:turtlebot
  expire: False

# Commands to run on first boot only
runcmd:
  # 1. Output the ID to the hidden file
  - echo "{bot_id_int}" > /home/ubuntu/.turtlebot_id
  - chown ubuntu:ubuntu /home/ubuntu/.turtlebot_id
  
  # 2. Update the wifi_configs.json using sed (Find and Replace)
  - sed -i 's/"ssid": "TurtleBot_AP_"/"ssid": "TurtleBot_AP_{bot_id_int}"/' /home/ubuntu/wifi_configs.json
  
  # 3. Update ROS_DOMAIN_ID in /etc/turtlebot4/setup.bash
  # Replaces 'export ROS_DOMAIN_ID="0"' with 'export ROS_DOMAIN_ID="<ID>"'
  - sed -i 's/export ROS_DOMAIN_ID=.*/export ROS_DOMAIN_ID="{bot_id_int}"/' /etc/turtlebot4/setup.bash

  # 4. Update the Robot Namespace in /etc/turtlebot4/setup.bash
  # We use | as a delimiter because the string contains slashes
  - sed -i 's|export ROBOT_NAMESPACE=.*|export ROBOT_NAMESPACE="/robot_{bot_id_str}"|' /etc/turtlebot4/setup.bash

  # 5. Ensure the json file is still owned by ubuntu after modification
  - chown ubuntu:ubuntu /home/ubuntu/wifi_configs.json
"""

        # 2. Generate network-config (Unchanged)
        network_config_content = f"""version: 2
ethernets:
  eth0:
    dhcp4: true
    dhcp-identifier: mac
wifis:
  wlan0:
    dhcp4: no
    addresses: [{ip_addr}/24]
    gateway4: {GATEWAY}
    nameservers:
      addresses: [{DNS}]
    access-points:
      "{WIFI_SSID}":
        password: "{WIFI_PASS}"
"""

        # Write files
        with open(f"{folder}/user-data", "w") as f:
            f.write(user_data_content)
        
        with open(f"{folder}/network-config", "w") as f:
            f.write(network_config_content)

    print(f"Successfully generated configs for {NUM_BOTS} robots in the /configs folder.")

if __name__ == "__main__":
    generate_configs()