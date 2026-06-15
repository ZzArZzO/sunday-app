// Whether the biometric app-lock is enabled. A plain on/off flag (no secret),
// defaulting to on so a signed-in device is locked unless the user opts out.

const KEY = "sunday_biometric_lock";

export function isLockEnabled(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(KEY) !== "off";
  } catch {
    return true;
  }
}

export function setLockEnabled(enabled: boolean): void {
  try {
    window.localStorage.setItem(KEY, enabled ? "on" : "off");
  } catch {
    // storage unavailable — preference simply won't persist
  }
}
