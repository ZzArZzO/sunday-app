// Native push registration (Capacitor). No-op on web: `isNativePlatform()` is
// false in a browser, so the native plugin is never dynamically imported there
// and the web build is unaffected. On a device this requests notification
// permission, then ships the OS-issued FCM/APNs token to the API.

import { Capacitor } from "@capacitor/core";

import { registerPushToken } from "@/lib/api";

export type PushRegistration =
  | { supported: false; reason: string }
  | { supported: true; granted: boolean };

// addListener registers a global handler; attach the token-forwarders only once
// per app session so re-priming doesn't stack duplicates.
let listenersAttached = false;

export async function registerForPush(): Promise<PushRegistration> {
  if (!Capacitor.isNativePlatform()) {
    return { supported: false, reason: "Notifications are available in the installed app." };
  }

  const { PushNotifications } = await import("@capacitor/push-notifications");

  const perm = await PushNotifications.requestPermissions();
  if (perm.receive !== "granted") {
    return { supported: true, granted: false };
  }

  if (!listenersAttached) {
    listenersAttached = true;
    // The OS delivers the token asynchronously after register().
    void PushNotifications.addListener("registration", (token) => {
      const platform = Capacitor.getPlatform() === "ios" ? "ios" : "android";
      void registerPushToken(token.value, platform).catch(() => {
        // Best-effort: a failed sync just means no push until the next launch.
      });
    });
    void PushNotifications.addListener("registrationError", () => {
      // Re-priming will retry; nothing to surface here.
    });
  }

  await PushNotifications.register();
  return { supported: true, granted: true };
}
