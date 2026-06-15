// Biometric availability check (Capacitor). False on web. The actual unlock is
// enforced by the OS at the Keychain/Keystore layer (see lib/secureToken) — the
// stored token simply can't be read without biometric auth — so there's no
// separate "verify" gesture to get out of sync with the credential read.

import { Capacitor } from "@capacitor/core";

export async function isBiometricAvailable(): Promise<boolean> {
  if (!Capacitor.isNativePlatform()) return false;
  const { NativeBiometric } = await import("@capgo/capacitor-native-biometric");
  try {
    const result = await NativeBiometric.isAvailable();
    return result.isAvailable;
  } catch {
    return false;
  }
}
