import os

def create_project_structure():
    # Ensure templates folder exists for the web app
    os.makedirs("templates", exist_ok=True)

    files = {
        "requirements.txt": "tabulate>=0.9.0\ncolorama>=0.4.6\nflask>=2.0.0\n",
        
        "utils.py": '''import socket
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
            return banner.replace('\\n', ' ') if banner else "No banner returned"
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
''',

        "scanner.py": '''import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import identify_service, grab_banner

def scan_single_port(ip: str, port: int, timeout: float) -> dict:
    result = {
        "port": port,
        "status": "Closed",
        "service": identify_service(port),
        "banner": ""
    }
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            code = s.connect_ex((ip, port))
            if code == 0:
                result["status"] = "Open"
                result["banner"] = grab_banner(ip, port, timeout=0.5)
            else:
                result["status"] = "Closed"
    except socket.timeout:
        result["status"] = "Filtered"
    except socket.error:
        result["status"] = "Unreachable"
    return result

def run_port_scanner(ip: str, ports: list, max_threads: int = 100, timeout: float = 0.8):
    results = []
    start_time = time.time()
    try:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_port = {
                executor.submit(scan_single_port, ip, port, timeout): port 
                for port in ports
            }
            for future in as_completed(future_to_port):
                results.append(future.result())
    except KeyboardInterrupt:
        pass

    duration = round(time.time() - start_time, 2)
    return sorted(results, key=lambda x: x['port']), duration
''',

        "app.py": '''from flask import Flask, render_template, request
from utils import validate_target, parse_port_range
from scanner import run_port_scanner

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    duration = None
    target_ip = None
    error_message = None
    
    if request.method == "POST":
        target = request.form.get("target", "").strip()
        ports_input = request.form.get("ports", "common").strip()
        
        try:
            target_ip = validate_target(target)
            ports_list = parse_port_range(ports_input)
            results, duration = run_port_scanner(ip=target_ip, ports=ports_list, max_threads=100, timeout=0.8)
        except Exception as e:
            error_message = str(e)
            
    return render_template("index.html", results=results, duration=duration, target_ip=target_ip, error=error_message)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
''',

        "templates/index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Security Port Scanner</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col justify-between">
    <header class="bg-white border-b border-slate-200 shadow-sm py-4 px-6">
        <div class="max-w-5xl mx-auto flex items-center justify-between">
            <h1 class="text-xl font-bold text-slate-900 flex items-center gap-2">
                🛡️ PortScanner <span class="text-xs font-semibold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">Prototyper</span>
            </h1>
            <span class="text-sm text-slate-500">Educational Security Dashboard</span>
        </div>
    </header>
    <main class="max-w-5xl mx-auto w-full px-6 py-8 flex-grow">
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8">
            <h2 class="text-lg font-semibold text-slate-900 mb-4">Configure Target Scan</h2>
            <form method="POST" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-700 mb-1">Target Hostname or IP</label>
                        <input type="text" name="target" required placeholder="e.g., scanme.nmap.org or 127.0.0.1" 
                               class="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-800">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-700 mb-1">Port Selection</label>
                        <input type="text" name="ports" value="common" placeholder="common, 80, 1-1024, etc." 
                               class="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-800">
                    </div>
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition duration-200 shadow-sm">
                    Launch Scan
                </button>
            </form>
            {% if error %}
            <div class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                <strong>Error:</strong> {{ error }}
            </div>
            {% endif %}
        </div>
        {% if results %}
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
            <div class="flex items-center justify-between mb-6">
                <div>
                    <h3 class="text-lg font-semibold text-slate-900">Scan Results</h3>
                    <p class="text-sm text-slate-500">Target resolved to: <span class="font-mono text-slate-700">{{ target_ip }}</span></p>
                </div>
                <div class="text-right">
                    <span class="text-xs font-medium bg-slate-100 text-slate-600 px-3 py-1.5 rounded-lg">Completed in {{ duration }}s</span>
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-200 text-slate-500 text-xs font-semibold uppercase tracking-wider">
                            <th class="py-3 px-4">Port</th>
                            <th class="py-3 px-4">Status</th>
                            <th class="py-3 px-4">Likely Service</th>
                            <th class="py-3 px-4">Banner / Info</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100 text-sm">
                        {% for r in results %}
                        {% if r.status == 'Open' %}
                        <tr class="hover:bg-slate-50">
                            <td class="py-3 px-4 font-mono font-medium text-slate-900">{{ r.port }}</td>
                            <td class="py-3 px-4"><span class="bg-emerald-100 text-emerald-700 text-xs font-semibold px-2.5 py-1 rounded-full">OPEN</span></td>
                            <td class="py-3 px-4 text-slate-700">{{ r.service }}</td>
                            <td class="py-3 px-4 font-mono text-xs text-slate-500 truncate max-w-xs">{{ r.banner }}</td>
                        </tr>
                        {% endif %}
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endif %}
    </main>
    <footer class="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        Port Scanner Prototype &bull; For Authorized Defensive Testing Only
    </footer>
</body>
</html>
'''
    }

    print("[*] Generating full web project structure...")
    for filepath, content in files.items():
        # Handle subdirectories like templates/index.html automatically
        os.makedirs(os.path.dirname(filepath), exist_ok=True) if "/" in filepath or "\\" in filepath else None
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"[+] Created: {filepath}")

    print("\n[SUCCESS] Web app files generated successfully!")

if __name__ == "__main__":
    create_project_structure()