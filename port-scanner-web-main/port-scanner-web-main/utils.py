import socket
import csv
from colorama import Fore, Style

COMMON_SERVICES = {
    21: "FTP", 22: "SSH", 23: "TELNET", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt"
}

PRESET_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 8080, 8443]

def validate_target(target: str) -> str:
    try:
        socket.inet_pton(socket.AF_INET, target)
        return target
    except socket.error:
        try:
            return socket.gethostbyname(target)
        except socket.gaierror as e:
            raise ValueError(f"Unable to resolve hostname '{target}': {e}")

def parse_port_range(port_input: str) -> list:
    ports = set()
    if port_input.lower() == "common":
        return PRESET_PORTS

    parts = port_input.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if not (1 <= start <= 65535 and 1 <= end <= 65535 and start <= end):
                    raise ValueError
                ports.update(range(start, end + 1))
            except ValueError:
                raise ValueError(f"Invalid port range format: '{part}'. Ports must be between 1 and 65535.")
        else:
            try:
                port = int(part)
                if not (1 <= port <= 65535):
                    raise ValueError
                ports.add(port)
            except ValueError:
                raise ValueError(f"Invalid port format: '{part}'. Must be an integer between 1 and 65535.")
    return sorted(list(ports))

def identify_service(port: int) -> str:
    return COMMON_SERVICES.get(port, "Unknown / Unassigned")

def grab_banner(ip: str, port: int, timeout: float = 1.0) -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, port))
            banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
            return banner.replace('\n', ' ') if banner else "No banner returned"
    except Exception:
        return "No banner available"

def export_results_to_csv(filename: str, target: str, results: list):
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Target IP", "Port", "Status", "Service", "Banner / Info"])
            for r in results:
                writer.writerow([target, r['port'], r['status'], r['service'], r['banner']])
        print(f"{Fore.GREEN}[+] Results successfully exported to {filename}{Style.RESET_ALL}")
    except IOError as e:
        print(f"{Fore.RED}[!] Error writing to CSV file: {e}{Style.RESET_ALL}")