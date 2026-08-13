# Changelog

All notable changes to the Shek Mun monitoring system. Newest first.

## [1.0.0] - 2026-08-13
- Initial release of the monitoring system.
- Inventory built from the IP assignment tables in "Shek Mun SOP Short.docx".
- Devices: 9 rooms (SM-11-01..08 + Common Rm), 283 room devices + 4 unique (DSP-Ctrl, DSP-Dante, XSM4216F, AVoIP-Manager).
- Per-room IPs increment by +1 across the table columns (e.g. Speaker-3: .181, .182, ... .189).
- Correction: SM-11-05 Dock-2ch documented as 172.18.2.65 duplicates the 4ch block; corrected to 172.18.2.75.
- Naming: encoders exist on both subnets, disambiguated as EN-PC-Dante / EN-PC-AVoIP, EN-Laptop-Dante / EN-Laptop-AVoIP, EN-Mac-Dante / EN-Mac-AVoIP.
- Config: master interval 10s, jitter 50%, timeout 3s, log retention 30 days.
