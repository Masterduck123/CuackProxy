import sys
import platform
import os
import subprocess
import requests
import time
import socks
import socket
from cryptography.fernet import Fernet, InvalidToken
import random
from stem.control import Controller
import shutil

KEY_FILE = "fernet_key.key"

def is_command_installed(command):
    return shutil.which(command) is not None

def is_tor_running():
    try:
        subprocess.run(['pgrep', '-x', 'tor'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def write_torrc(country_code=None):
    torrc_path = f"/tmp/torrc_{os.getpid()}"
    if country_code:
        torrc_content = f"ExitNodes {country_code}\nStrictNodes 1"
    else:
        torrc_content = "StrictNodes 0"  # Allow random nodes
    torrc_content += "\nControlPort 9051\nCookieAuthentication 1"
    with open(torrc_path, "w") as file:
        file.write(torrc_content)
    return torrc_path

def launch_tor_process(torrc_path):
    try:
        tor_process = subprocess.Popen(["tor", "-f", torrc_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timeout = 60
        start_time = time.time()
        while time.time() - start_time < timeout:
            if tor_process.poll() is None:  # Check if Tor is running
                if is_tor_ready():
                    return tor_process
            time.sleep(1)
        print("Failed to start the Tor process. Check the logs.")
        return None
    except Exception as e:
        log_error(f"Error starting Tor: {e}")
        return None

def is_tor_ready():
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            bootstrap_status = controller.get_info("status/bootstrap-phase")
            return "TAG=done" in bootstrap_status
    except Exception:
        return False

def start_tor(country_code=None):
    if not is_command_installed("tor"):
        return None
    if is_tor_running():
        if is_tor_ready():
            log_error("Tor is already running and ready.")
            return "running"
        else:
            log_error("Tor is running but not ready.")
            return None
    torrc_path = write_torrc(country_code)
    return launch_tor_process(torrc_path)

def configure_tor_proxy(proxy_ip="127.0.0.1", proxy_port=9050):
    try:
        socks.set_default_proxy(socks.SOCKS5, proxy_ip, proxy_port)
    except Exception as e:
        log_error(f"Error configuring Tor proxy: {e}")
        sys.exit(1)

def check_ip_and_location():
    try:
        session = requests.Session()
        session.proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
        response = session.get("https://ipinfo.io/json", timeout=10)
        data = response.json()
        ip = data.get("ip", "Unknown")
        location = f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
        return ip, location
    except requests.exceptions.ProxyError:
        log_error("Error: Tor proxy is not working.")
        return "Error", "Unknown"
    except requests.exceptions.RequestException as e:
        log_error(f"Error checking IP and location via Tor: {e}")
        return "Error", "Unknown"

def log_error(message):
    try:
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S] ")
        key = load_or_generate_key()
        cipher_suite = Fernet(key)
        encrypted_message = cipher_suite.encrypt((timestamp + message).encode())
        with open("error_log.txt", "ab") as file:
            file.write(encrypted_message + b'\n')
    except Exception as e:
        print(f"Error logging message: {e}")

def load_or_generate_key():
    if not os.path.exists(KEY_FILE):
        print("Encryption key not found. Previous logs cannot be decrypted.")
        return None
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

def change_mac_address(interface):
    if not os.path.exists(f"/sys/class/net/{interface}"):
        print("Invalid interface.")
        return False
    try:
        new_mac = "02:%02x:%02x:%02x:%02x:%02x" % tuple(random.randint(0, 255) for _ in range(5))

        if is_command_installed("ifconfig"):
            subprocess.run(["ifconfig", interface, "down"], check=True)
            subprocess.run(["ifconfig", interface, "hw", "ether", new_mac], check=True)
            subprocess.run(["ifconfig", interface, "up"], check=True)
        elif is_command_installed("ip"):
            subprocess.run(["ip", "link", "set", "dev", interface, "down"], check=True)
            subprocess.run(["ip", "link", "set", "dev", interface, "address", new_mac], check=True)
            subprocess.run(["ip", "link", "set", "dev", interface, "up"], check=True)
        else:
            log_error("Neither ifconfig nor ip command found.")
            return False
        
        print(f"MAC address changed to {new_mac}")
        return True
    except subprocess.CalledProcessError as e:
        print("Error changing MAC. Is the interface valid? Do you have root permissions?")
        log_error(f"Error changing MAC address: {e}")
        return False

def decrypt_logs():
    if not os.path.exists("error_log.txt"):
        return "No logs to show."
    key = load_or_generate_key()
    if key is None:
        return "No key to decrypt the logs."
    try:
        cipher_suite = Fernet(key)
        with open("error_log.txt", "rb") as file:
            encrypted_logs = file.readlines()
        
        decrypted_logs = []
        for encrypted_message in encrypted_logs:
            try:
                decrypted_message = cipher_suite.decrypt(encrypted_message.strip()).decode()
                decrypted_logs.append(decrypted_message)
            except InvalidToken:
                decrypted_logs.append("[ERROR] Corrupt log or incorrect key.")
        
        return "\n".join(decrypted_logs)
    except Exception as e:
        return f"Error decrypting logs: {e}"

def check_platform():
    if platform.system() == "Windows":
        print("This script is only supported on Linux.")
        sys.exit()

def renew_tor_identity():
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal("NEWNYM")
            print("Tor identity renewed.")
    except Exception as e:
        log_error(f"Error renewing Tor identity: {e}")

def main():
    check_platform()
    
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("This script must be run as root.")
        sys.exit(1)
    
    tor_process = None
    
    try:
        while True:
            if os.name == 'posix' and os.getenv("TERM"):
                os.system('clear')
            print("\n--- CuackProxy ---")
            print("1. Connect to Tor")
            print("2. Decrypt Logs")
            print("3. Renew Tor Identity")
            print("4. Exit")
            
            choice = input("Enter your choice: ")
            
            if choice == '1':
                proxy_ip = input("Enter Proxy IP (default: 127.0.0.1): ") or "127.0.0.1"
                proxy_port = input("Enter Proxy Port (default: 9050): ") or "9050"
                try:
                    proxy_port = int(proxy_port)
                except ValueError:
                    print("Invalid port.")
                    continue
                
                country_code = input("Enter Country Code (or 'Random' for random exit node): ")
                if country_code.lower() == "random":
                    country_code = None
                elif country_code and (not country_code.isalpha() or len(country_code) != 2):
                    print("Invalid country code.")
                    continue
                
                interface = input("Enter Network Interface (e.g., eth0): ")
                
                if not change_mac_address(interface):
                    print("Error changing MAC address")
                    continue
                
                configure_tor_proxy(proxy_ip, proxy_port)
                result = start_tor(country_code)
                
                if result == "running":
                    print("Using already running Tor...")
                    tor_process = None
                elif result:
                    tor_process = result
                    print("Connected to Tor")
                else:
                    print("Error starting Tor")
                    continue
                
                ip, location = check_ip_and_location()
                if ip == "Error":
                    print("[✘] Could not get IP via Tor.")
                else:
                    print(f"IP: {ip}, Location: {location}")
            
            elif choice == '2':
                decrypted_logs = decrypt_logs()
                print("\n--- Decrypted Logs ---")
                print(decrypted_logs)
            
            elif choice == '3':
                renew_tor_identity()
            
            elif choice == '4':
                print("Exiting...")
                break
            
            else:
                print("Invalid choice. Please try again.")
    
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
    
    finally:
        if tor_process and tor_process.poll() is None:
            tor_process.terminate()
            print("Tor process terminated.")
        torrc_path = f"/tmp/torrc_{os.getpid()}"
        if os.path.exists(torrc_path):
            os.remove(torrc_path)

if __name__ == "__main__":
    main()