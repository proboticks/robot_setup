#!/usr/bin/env python3

import json
import os
import sys
import subprocess
import argparse
import yaml
import time  # <--- FIXED: Added missing import

class WifiStandalone:
    def __init__(self, json_path='/home/ubuntu/wifi_configs.json'): # Update path if needed
        self.json_path = json_path
        # Overrides TurtleBot default 50-wifis.yaml
        self.netplan_file = '/etc/netplan/50-wifis.yaml'

    def load_json(self):
        if not os.path.exists(self.json_path):
            print(f"Error: {self.json_path} not found.")
            sys.exit(1)
        with open(self.json_path, 'r') as f:
            return json.load(f)

    def generate_netplan(self, config):
        """Builds Netplan YAML using NetworkManager as the renderer."""
        wifi_node = {
            'dhcp4': config.get('dhcp', True),
            'optional': True,
            'access-points': {}
        }

        ssid = config['ssid']
        
        # Enterprise (PEAP/MSCHAPv2) logic
        if config.get('auth_type') == 'enterprise' or 'identity' in config:
            wifi_node['access-points'][ssid] = {
                'auth': {
                    'key-management': 'eap',
                    'method': 'peap',
                    'identity': config.get('identity'),
                    'password': config.get('password'),
                    'phase2-auth': 'mschapv2'
                }
            }
        else:
            # Standard PSK
            wifi_node['access-points'][ssid] = {
                'password': config.get('password')
            }

        if config.get('mode') == 'Access Point':
            wifi_node['access-points'][ssid]['mode'] = 'ap'
            
        if not config.get('dhcp', True) and 'ip' in config:
            wifi_node['addresses'] = [config['ip']]

        # IMPORTANT: renderer is now NetworkManager
        return {
            'network': {
                'version': 2,
                'renderer': 'NetworkManager',
                'wifis': {'wlan0': wifi_node}
            }
        }

    def select_profile_interactively(self, profiles):
        print("\n--- Available Wi-Fi Profiles ---")
        for i, p in enumerate(profiles):
            print(f"{i+1}) {p['name']} (SSID: {p['ssid']})")
        
        while True:
            try:
                choice = int(input(f"\nSelect a profile (1-{len(profiles)}): "))
                if 1 <= choice <= len(profiles):
                    return profiles[choice-1]
            except (ValueError, IndexError):
                pass
            print("Invalid selection. Please try again.")

    def run(self, force_ap=False, dry_run=False, force_confirm=False):
        data = self.load_json()
        
        if force_ap:
            selected = data.get('ap_settings', {}).copy()
            selected['name'] = "Access Point Mode"
            selected['mode'] = 'Access Point'
        else:
            profiles = data.get('profiles', [])
            if not profiles:
                print("No profiles found in JSON.")
                return
            selected = self.select_profile_interactively(profiles)

        # Generate YAML
        netplan_dict = self.generate_netplan(selected)
        yaml_str = yaml.dump(netplan_dict, default_flow_style=False)

        # Show Summary
        print("\n" + "="*50)
        print(f"CONFIGURATION SUMMARY FOR: {selected['name']}")
        print("="*50)
        print(f"SSID:      {selected.get('ssid')}")
        print(f"Renderer:  NetworkManager")
        print(f"Mode:      {selected.get('mode', 'Client')}")
        if 'identity' in selected:
            print(f"Identity:  {selected['identity']}")
        print(f"DHCP:      {selected.get('dhcp', True)}")
        print("-" * 50)

        if dry_run:
            print("\n[DRY RUN] Generated Netplan YAML:")
            print(yaml_str)
            return

        # --- NON-INTERACTIVE LOGIC ---
        if not force_confirm:
            print("\nIMPORTANT: This will apply changes and REBOOT the Raspberry Pi.")
            confirm = input("Proceed? (y/N): ").lower()
            if confirm != 'y':
                print("Aborted.")
                return
        else:
             print("\nForce flag detected. Proceeding automatically...")

        # Apply changes
        print("Applying Netplan Changes")
        with open(self.netplan_file, 'w') as f:
            f.write(yaml_str)
        
        time.sleep(2)
        print("Configuration saved. Rebooting now...")
        # Since script runs as root, sudo is technically redundant but harmless
        subprocess.run(['reboot'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ap', action='store_true', help="Force Access Point mode")
    parser.add_argument('--dry-run', action='store_true', help="Print config without applying")
    parser.add_argument('--force', action='store_true', help="Skip interactive confirmation") # <--- NEW FLAG
    args = parser.parse_args()

    if not args.dry_run and os.geteuid() != 0:
        print("Error: Please run with sudo.")
        sys.exit(1)

    WifiStandalone().run(force_ap=args.ap, dry_run=args.dry_run, force_confirm=args.force)