import socket
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