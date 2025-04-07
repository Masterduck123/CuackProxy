# CuackProxy

## Description

CuackProxy is a project designed to provide anonymous browsing using the Tor network. This proxy aims to enhance privacy by routing internet traffic through the Tor network, masking the user's IP address and location.

## Features

- Automatically connect to the Tor network
- Change MAC address for additional anonymity
- Decrypt and view encrypted logs
- Renew Tor identity to get a new IP address

## Installation

To install CuackProxy, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/Masterduck123/CuackProxy.git
   ```
2. Navigate to the project directory:
   ```bash
   cd CuackProxy
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To use CuackProxy, follow these steps:

1. Run the script with root privileges:
   ```bash
   sudo python CuackProxy.py
   ```
2. You will see a menu with the following options:
   - Connect to Tor
   - Decrypt Logs
   - Renew Tor Identity
   - Exit
3. Select "Connect to Tor" to start using the proxy. You may be prompted to enter:
   - Proxy IP (default: 127.0.0.1)
   - Proxy Port (default: 9050)
   - Country Code for the exit node (leave blank for a random node)
   - Network Interface (e.g., eth0) for changing the MAC address

## How It Works

1. **Connecting to Tor:**
   - The script checks if Tor is installed and running.
   - If Tor is not running, it writes a `torrc` configuration file and starts the Tor process.
   - The script configures the proxy to use the Tor network.

2. **Changing MAC Address:**
   - The script changes the MAC address of the specified network interface to enhance anonymity.

3. **Checking IP and Location:**
   - After connecting to Tor, the script retrieves and displays the current IP address and location through the Tor network.

4. **Decrypting Logs:**
   - The script can decrypt and display encrypted error logs using a generated encryption key.

5. **Renewing Tor Identity:**
   - The script can renew the Tor identity to obtain a new IP address without restarting the Tor process.

## Contributing

If you would like to contribute to CuackProxy, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/new-feature`).
3. Make your changes and commit them (`git commit -am 'Add new feature'`).
4. Push your changes (`git push origin feature/new-feature`).
5. Open a Pull Request.
