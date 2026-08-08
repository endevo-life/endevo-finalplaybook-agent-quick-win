import { useCallback, useEffect, useState } from "react";
import { authLogout, authStart, authVerify, getMe, getToken, setToken } from "../api/client";

// Minimal auth state hook. Restores the session on load from the persisted
// token, exposes login (two-step: start -> verify) and logout, and holds the
// server-side entitlement snapshot (tier + remaining quota).
export function useAuth() {
  const [account, setAccount] = useState(null); // server entitlement snapshot
  const [loading, setLoading] = useState(true);

  // Returns the fresh entitlement snapshot (or null) as well as storing it, so
  // callers can act on the result immediately instead of waiting a render for
  // `account` to settle -- the post-Stripe poll needs to read the tier it just
  // fetched.
  const refresh = useCallback(async () => {
    if (!getToken()) {
      setAccount(null);
      setLoading(false);
      return null;
    }
    try {
      const me = await getMe();
      setAccount(me);
      return me;
    } catch {
      setToken(null); // token expired/invalid -> drop it
      setAccount(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const startLogin = useCallback((email) => authStart(email), []);

  const verifyLogin = useCallback(async (email, code, session) => {
    const { token, user } = await authVerify(email, code, session);
    setToken(token);
    setAccount(user);
    return user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authLogout();
    } catch {
      /* ignore */
    }
    setToken(null);
    setAccount(null);
  }, []);

  const isPaid = account?.tier === "paid";

  return { account, loading, isPaid, startLogin, verifyLogin, logout, refresh };
}
