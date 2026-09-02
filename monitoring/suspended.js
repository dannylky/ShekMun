// Devices under suspension: kept in the dashboard but NOT counted as
// failures while offline. When such a device comes back online it
// resumes normal status display automatically.
window.SUSPENDED_IPS = new Set([
  // SM-11-02
  '172.18.2.242',   // Speaker-9-USBMac
  // Common Rm
  '172.18.22.129',  // EN-Laptop-AVoIP
  '172.18.22.119',  // EN-PC-AVoIP
  '172.18.22.109',  // MediaBox
  '172.18.22.49',   // TV-DEC-1
  '172.18.2.129',   // EN-Laptop-Dante
  '172.18.2.119',   // EN-PC-Dante
  '172.18.2.59',    // AVProc-Pi5
  '172.18.2.79',    // Dock-2ch
  '172.18.2.49',    // HardKey
  '172.18.2.29',    // PCU-Lectern
  '172.18.22.29'    // SW-Lectern
]);