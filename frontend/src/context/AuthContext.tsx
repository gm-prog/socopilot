import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  fetchProfile,
  getStoredAccessToken,
  loginRequest,
  logoutRequest,
  persistAccessToken,
  refreshAccessToken,
  subscribeToAuthEvents,
  clearStoredAccessToken,
} from "../api/auth";

export interface UserProfile {
  id: string;
  email: string;
  role: string;
  tenant_id: string;
}

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  status: AuthStatus;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(getStoredAccessToken());
  const [status, setStatus] = useState<AuthStatus>("loading");
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const setAuthState = useCallback(
    (nextToken: string | null, nextUser: UserProfile | null, nextStatus: AuthStatus) => {
      if (!mountedRef.current) return;
      setToken(nextToken);
      setUser(nextUser);
      setStatus(nextStatus);
    },
    [],
  );

  const updateProfile = useCallback(async (accessToken: string): Promise<UserProfile | null> => {
    const profile = await fetchProfile(accessToken);
    if (!profile) {
      return null;
    }
    if (!mountedRef.current) return profile;
    setUser(profile);
    return profile;
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setStatus("loading");

    const accessToken = await loginRequest(email, password);
    persistAccessToken(accessToken, "login");
    setToken(accessToken);

    const profile = await updateProfile(accessToken);
    if (!profile) {
      clearStoredAccessToken();
      setAuthState(null, null, "unauthenticated");
      throw new Error("Failed to load authenticated identity");
    }

    setAuthState(accessToken, profile, "authenticated");
  }, [setAuthState, updateProfile]);

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } catch {
      // swallow network problems and still clear local state
    }
    clearStoredAccessToken();
    setAuthState(null, null, "unauthenticated");
  }, [setAuthState]);

  const refreshSession = useCallback(async (): Promise<string | null> => {
    setStatus("loading");
    const accessToken = await refreshAccessToken();
    if (!accessToken) {
      setAuthState(null, null, "unauthenticated");
      return null;
    }

    setToken(accessToken);
    setStatus("authenticated");

    if (!user) {
      const profile = await updateProfile(accessToken);
      if (!profile) {
        setAuthState(null, null, "unauthenticated");
        return null;
      }
    }

    return accessToken;
  }, [setAuthState, updateProfile, user]);

  const restoreSession = useCallback(async () => {
    setStatus("loading");

    const storedToken = getStoredAccessToken();
    if (storedToken) {
      const profile = await updateProfile(storedToken);
      if (profile) {
        setAuthState(storedToken, profile, "authenticated");
        return;
      }

      const refreshedToken = await refreshAccessToken();
      if (refreshedToken) {
        const profileFromRefresh = await updateProfile(refreshedToken);
        if (profileFromRefresh) {
          setAuthState(refreshedToken, profileFromRefresh, "authenticated");
          return;
        }
      }
    } else {
      const refreshedToken = await refreshAccessToken();
      if (refreshedToken) {
        const profileFromRefresh = await updateProfile(refreshedToken);
        if (profileFromRefresh) {
          setAuthState(refreshedToken, profileFromRefresh, "authenticated");
          return;
        }
      }
    }

    setAuthState(null, null, "unauthenticated");
  }, [refreshAccessToken, setAuthState, updateProfile]);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  useEffect(() => {
    const unsubscribe = subscribeToAuthEvents(async (message) => {
      if (message.action === "logout") {
        setAuthState(null, null, "unauthenticated");
        return;
      }

      const storedToken = getStoredAccessToken();
      if (!storedToken) {
        setAuthState(null, null, "unauthenticated");
        return;
      }

      if (storedToken === token && user) {
        return;
      }

      const profile = await updateProfile(storedToken);
      if (profile) {
        setAuthState(storedToken, profile, "authenticated");
      } else {
        const refreshedToken = await refreshAccessToken();
        if (refreshedToken) {
          const refreshedProfile = await updateProfile(refreshedToken);
          if (refreshedProfile) {
            setAuthState(refreshedToken, refreshedProfile, "authenticated");
            return;
          }
        }
        setAuthState(null, null, "unauthenticated");
      }
    });

    return unsubscribe;
  }, [token, user, setAuthState, updateProfile]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        status,
        isAuthenticated: status === "authenticated",
        login,
        logout,
        refreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

export default AuthContext;
