# SubPulse Subdomain Enumeration – Technical Documentation

## 1. Overview
Subdomain enumeration is a critical reconnaissance phase used in vulnerability assessments to discover hidden web assets, administrative panels, and API endpoints belonging to a target organization.

---

## 2. Methodology & Workflow
1. **Input Validation:** Normalizes and verifies target domain formats using regular expressions.
2. **Wordlist & Transparency Probing:** Iterates through common subdomain prefixes combined with certificate log searches.
3. **Asset Inventory:** Aggregates live endpoints into structured tables and exportable JSON reports.