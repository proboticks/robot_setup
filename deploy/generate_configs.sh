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
        bot_id = f"{i:02d}" # Formats as 01, 02, etc.
        hostname = f"turtlebot{bot_id}"
        ip_addr = f"{BASE_IP}{START_IP_SUFFIX + i - 1}"
        
        # Create a directory for this bot's files
        folder = f"configs/bot{bot_id}"
        os.makedirs(folder, exist_ok=True)

        # 1. Generate user-data
        user_data_content = f"""#cloud-config
hostname: {hostname}
manage_etc_hosts: true
ssh_pwauth: true
chpasswd:
  list: |
     ubuntu:turtlebot
  expire: False
"""

        # 2. Generate network-config
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

        with open(f"{folder}/user-data", "w") as f:
            f.write(user_data_content)
        
        with open(f"{folder}/network-config", "w") as f:
            f.write(network_config_content)

    print(f"Successfully generated configs for {NUM_BOTS} robots in the /configs folder.")

if __name__ == "__main__":
    generate_configs()
