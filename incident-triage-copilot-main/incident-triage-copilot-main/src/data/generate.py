from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

from src.config import ROOT

SEED = 42

TEMPLATES = {
    "network": {
        "severity": ["medium", "high"],
        "titles": [
            "Wi-Fi disconnecting in lecture hall",
            "Device receives self-assigned IP address",
            "Ethernet port has no connectivity",
            "High packet loss during video session",
        ],
        "details": [
            "The laptop receives a 169.254 address and cannot reach internal services.",
            "Multiple devices disconnect every few minutes while neighboring rooms remain stable.",
            "The wall port shows no link light after a known-good cable is connected.",
            "Latency exceeds 800 ms and packet loss disrupts the live class stream.",
        ],
    },
    "av": {
        "severity": ["medium", "high"],
        "titles": [
            "Projector shows no signal",
            "Room speakers produce no audio",
            "Lecture capture camera is offline",
            "HDMI input flickers during presentation",
        ],
        "details": [
            "The display is powered on but reports no signal from the instructor station.",
            "Audio meters move in software but no sound is produced by room speakers.",
            "The capture application cannot detect the installed camera device.",
            "The image drops every few seconds with two different laptops and cables.",
        ],
    },
    "authentication": {
        "severity": ["low", "medium"],
        "titles": [
            "User cannot sign in after password reset",
            "MFA prompt never arrives",
            "Account repeatedly locks",
            "SSO redirects back to login page",
        ],
        "details": [
            "The new password works on one service but fails on the classroom workstation.",
            "The user has network access but receives no push notification on the registered device.",
            "The account locks immediately after the user enters verified credentials.",
            "The browser loops between the identity provider and application login screen.",
        ],
    },
    "software": {
        "severity": ["low", "medium"],
        "titles": [
            "Presentation application crashes on launch",
            "Required plugin is missing",
            "Video conference client cannot share screen",
            "Application update fails repeatedly",
        ],
        "details": [
            "The application exits with an error after a recent operating-system update.",
            "The course tool opens but reports that a required browser extension is unavailable.",
            "Screen sharing is disabled even though camera and microphone permissions are granted.",
            "The installer rolls back and reports insufficient permissions on the managed device.",
        ],
    },
    "hardware": {
        "severity": ["medium", "high"],
        "titles": [
            "Instructor computer will not power on",
            "Touch panel is unresponsive",
            "Document camera has intermittent power",
            "Laptop overheats and shuts down",
        ],
        "details": [
            "No power LEDs appear after checking the outlet and reseating the power cable.",
            "The control panel displays content but does not respond to touch input.",
            "The device powers off when its arm is repositioned during use.",
            "The fan runs at maximum speed before the device shuts down unexpectedly.",
        ],
    },
}

RUNBOOKS = [
    ("RB-NET-001", "Self-assigned IP address", "network", "Confirm the device has a 169.254 address. Renew the DHCP lease, verify the switch port and VLAN assignment, test a known-good cable, and escalate to network operations if neighboring devices are also affected."),
    ("RB-NET-002", "Intermittent wireless connectivity", "network", "Compare impact across devices and nearby rooms. Check signal strength, access-point health, authentication logs, and recent configuration changes. Capture packet loss before escalating."),
    ("RB-AV-001", "Projector no signal", "av", "Verify projector power, selected input, cable seating, and source output mode. Test a known-good cable and source. Reboot the switcher only after documenting the active class state."),
    ("RB-AV-002", "Room audio failure", "av", "Confirm the correct playback device, application volume, mute state, DSP status, and amplifier power. Test local program audio before replacing hardware."),
    ("RB-AUTH-001", "Password and cached credential mismatch", "authentication", "Confirm the account is active, test web sign-in, remove cached credentials, synchronize the workstation, and retry. Do not ask the user to disclose a password."),
    ("RB-AUTH-002", "MFA delivery failure", "authentication", "Verify the registered factor and device connectivity. Offer an approved backup factor or recovery workflow and escalate identity changes through the authorized service desk."),
    ("RB-SW-001", "Application crash after update", "software", "Record the version and error, test with a clean profile, check compatibility, clear application cache, and roll back only through the approved software-management process."),
    ("RB-SW-002", "Screen-sharing permission failure", "software", "Check operating-system privacy permissions, application permissions, meeting role, and display-capture settings. Restart the application after permissions change."),
    ("RB-HW-001", "Device will not power on", "hardware", "Confirm the outlet, power strip, adapter, and cable with known-good components. Disconnect peripherals, hold power for 15 seconds, retry, and tag the device for repair if there is still no response."),
    ("RB-HW-002", "Touch controller unresponsive", "hardware", "Check network and power indicators, clean and restart the panel, verify the controller service, and use the documented manual fallback while the class is active."),
]


def generate_incidents(output: Path, n: int = 750) -> pd.DataFrame:
    random.seed(SEED)
    rows = []
    categories = list(TEMPLATES)
    for idx in range(n):
        category = categories[idx % len(categories)]
        template = TEMPLATES[category]
        title = random.choice(template["titles"])
        detail = random.choice(template["details"])
        room = random.choice(["Stevenson 1206", "Featheringill 134", "Wilson 103", "Buttrick 102", "Alumni 201"])
        context = random.choice([
            f"The issue started at the beginning of a class in {room}.",
            f"A support technician reproduced the issue in {room}.",
            f"The instructor reports this is the first failure this semester in {room}.",
        ])
        rows.append({
            "incident_id": f"INC-{idx + 1:05d}",
            "title": title,
            "description": f"{detail} {context}",
            "category": category,
            "severity": random.choice(template["severity"]),
        })
    df = pd.DataFrame(rows).sample(frac=1, random_state=SEED).reset_index(drop=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return df


def generate_runbooks(output: Path) -> pd.DataFrame:
    df = pd.DataFrame(RUNBOOKS, columns=["source_id", "title", "category", "content"])
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return df


def main() -> None:
    generate_incidents(ROOT / "data" / "incidents.csv")
    generate_runbooks(ROOT / "data" / "runbooks.csv")
    print("Generated synthetic incidents and runbooks.")


if __name__ == "__main__":
    main()
