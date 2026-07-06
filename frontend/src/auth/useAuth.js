import { useCallback, useEffect, useState } from "react";
import { authLogout, authStart, authVerify, getMe, getToken, setToken } from "../api/client";

// Minimal auth state hook. Restores the session on load from the persisted
// token, exposes login (two-step: start -> verify) and logout, and holds the
// server-side entitlement snapshot (tier + remaining quota).
export function useAuth() {
  const [account, setAccount] = useState(null); // server entitlement snapshot
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setAccount(null);
      setLoading(false);
      return;
    }
    try {
      setAccount(await getMe());
    } catch {
      setToken(null); // token expired/invalid -> drop it
      setAccount(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const startLogin = useCallback((email) => authStart(email), []);

  const verifyLogin = useCallback(async (email, code) => {
    const { token, user } = await authVerify(email, code);
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
