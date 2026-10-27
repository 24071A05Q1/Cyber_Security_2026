---

### 3. `DOCUMENTATION.md` (Technical Documentation)

```markdown
# NetPulse IP Range Scanner – Technical Documentation

## 1. Overview
The **NetPulse IP Range Scanner** is a client-side web application built to simulate and demonstrate foundational network discovery concepts. It provides a user-friendly graphical interface for executing ping sweeps, identifying active/inactive hosts within a specified subnet, and probing common TCP ports.

---

## 2. Architecture & Components

### A. Input & Validation Module
- Parses user input for CIDR subnets (e.g., `/24`, `/16`).
- Validates IPv4 octets (0–255 range checks) and catches malformed inputs, triggering error alerts in the live terminal log.

### B. Scanning Engine Simulation
- **Ping Sweep (ICMP/ARP):** Simulates low-level echo requests to discover live IP addresses.
- **TCP Connect / SYN Probes:** Tests common service ports (`22 - SSH`, `80 - HTTP`, `443 - HTTPS`, `445 - SMB`, `3389 - RDP`) on discovered live hosts.
- **Randomized Latency Calculation:** Generates realistic response times (e.g., 2ms–120ms) to mirror real-world network conditions.

### C. Visualization & Reporting
- **Host Grid:** Dynamically renders color-coded host cards (Emerald for Active, Slate/Gray for Inactive).
- **Interactive Inspection Modal:** Click any active host to inspect simulated open ports, MAC addresses, and OS guesses.
- **Data Export:** Serializes scan state into downloadable JSON report files for academic lab submissions.

---

## 3. Lab Usage Guide
1. **Target Setup:** Enter your test lab subnet (e.g., `192.168.1.0/24`).
2. **Execution:** Select your desired scan aggressiveness and click **Start Scan**.
3. **Analysis:** Observe active nodes in real-time through the terminal and host cards. Review exported logs for your lab report.
