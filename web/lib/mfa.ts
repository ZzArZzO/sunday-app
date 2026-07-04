// TOTP multi-factor auth via Supabase's built-in MFA API (free, on by default —
// see https://supabase.com/docs/guides/auth/auth-mfa/totp).

import { createClient } from "@/lib/supabase/client";

export type TotpFactor = {
  id: string;
  friendlyName: string | null;
  status: "verified" | "unverified";
};

export type EnrollResult = {
  factorId: string;
  qrCodeSvg: string;
  secret: string;
};

/** Step 1 of enrollment: registers a new TOTP factor and returns a QR code to scan. */
export async function enrollTotp(): Promise<EnrollResult> {
  const { data, error } = await createClient().auth.mfa.enroll({ factorType: "totp" });
  if (error) throw new Error(error.message);
  return { factorId: data.id, qrCodeSvg: data.totp.qr_code, secret: data.totp.secret };
}

/** Step 2: verify the 6-digit code from the authenticator app to activate the factor. */
export async function verifyTotpEnrollment(factorId: string, code: string): Promise<void> {
  const supabase = createClient();
  const { data: challenge, error: challengeError } = await supabase.auth.mfa.challenge({ factorId });
  if (challengeError) throw new Error(challengeError.message);

  const { error: verifyError } = await supabase.auth.mfa.verify({
    factorId,
    challengeId: challenge.id,
    code,
  });
  if (verifyError) throw new Error(verifyError.message);
}

export async function listTotpFactors(): Promise<TotpFactor[]> {
  const { data, error } = await createClient().auth.mfa.listFactors();
  if (error) throw new Error(error.message);
  return data.totp.map((f) => ({ id: f.id, friendlyName: f.friendly_name ?? null, status: f.status }));
}

export async function unenrollTotp(factorId: string): Promise<void> {
  const { error } = await createClient().auth.mfa.unenroll({ factorId });
  if (error) throw new Error(error.message);
}

/**
 * Whether the current session needs an MFA challenge before it's fully
 * authenticated — true when the user has a verified factor (nextLevel aal2)
 * but this session hasn't gone through it yet (currentLevel aal1).
 */
export async function needsMfaChallenge(): Promise<boolean> {
  const { data, error } = await createClient().auth.mfa.getAuthenticatorAssuranceLevel();
  if (error) return false;
  return data.nextLevel === "aal2" && data.nextLevel !== data.currentLevel;
}

/** Complete the login-time MFA challenge with a code from the authenticator app. */
export async function verifyTotpChallenge(code: string): Promise<void> {
  const supabase = createClient();
  const { data: factors, error: factorsError } = await supabase.auth.mfa.listFactors();
  if (factorsError) throw new Error(factorsError.message);

  const factor = factors.totp[0];
  if (!factor) throw new Error("No authenticator app is enrolled on this account.");

  const { data: challenge, error: challengeError } = await supabase.auth.mfa.challenge({
    factorId: factor.id,
  });
  if (challengeError) throw new Error(challengeError.message);

  const { error: verifyError } = await supabase.auth.mfa.verify({
    factorId: factor.id,
    challengeId: challenge.id,
    code,
  });
  if (verifyError) throw new Error(verifyError.message);
}
