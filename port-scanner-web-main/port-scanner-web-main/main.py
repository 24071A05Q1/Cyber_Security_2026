import sys
import argparse
from colorama import init, Fore, Style
from tabulate import tabulate
from utils import validate_target, parse_port_range, export_results_to_csv
from scanner import run_port_scanner

init(autoreset=True)

def main():
    print(f"{Fore.CYAN}=== Network Security Port Scanner Prototype ==={Style.RESET_ALL}\n")
    parser = argparse.ArgumentParser(description="A safe, multithreaded TCP port scanner.")
    parser.add_argument("-t", "--target", required=True, help="Target hostname or IPv4 address")
    parser.add_argument("-p", "--ports", default="common", help="Port specification ('common', single, range, or list)")
    parser.add_argument("--threads", type=int, default=100, help="Max concurrent threads")
    parser.add_argument("--timeout", type=float, default=0.8, help="Socket timeout")
    parser.add_argument("--export", type=str, default="", help="Export results to CSV file")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    try:
        resolved_ip = validate_target(args.target)
        print(f"{Fore.GREEN}[+] Target resolved: {resolved_ip}{Style.RESET_ALL}")
    except ValueError as e:
        print(f"{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
        sys.exit(1)

    try:
        ports_list = parse_port_range(args.ports)
    except ValueError as e:
        print(f"{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
        sys.exit(1)

    results, duration = run_port_scanner(resolved_ip, ports_list, args.threads, args.timeout)

    open_ports = [r for r in results if r['status'] == 'Open']
    
    print(f"\n{Fore.CYAN}--- SCAN RESULTS ---{Style.RESET_ALL}")
    if open_ports:
        table_data = [[r['port'], f"{Fore.GREEN}OPEN{Style.RESET_ALL}", r['service'], r['banner']] for r in open_ports]
        print(tabulate(table_data, headers=["Port", "Status", "Service", "Banner"], tablefmt="fancy_grid"))
    else:
        print(f"{Fore.YELLOW}No open ports found.{Style.RESET_ALL}")

    print(f"\nScanned {len(results)} ports in {duration}s. Open: {len(open_ports)}")

    if args.export:
        export_results_to_csv(args.export, resolved_ip, results)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Aborted.{Style.RESET_ALL}")
        sys.exit(0)