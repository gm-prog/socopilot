import { useAuth } from "../context/AuthContext";

export function useAuthToken(): string | null {
  const { token } = useAuth();
  return token;
}
