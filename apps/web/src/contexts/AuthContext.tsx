import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { authLogin, authLogout, authMe, authSignup } from "../lib/api";
import type { User } from "../lib/api";

type AuthContextType = {
  user: User | null;
  isLoading: boolean;
  login: (
    email: string,
    password: string,
    rememberMe?: boolean,
  ) => Promise<User>;
  signup: (name: string, email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function refreshUser() {
    try {
      setUser(await authMe());
    } catch {
      setUser(null);
    }
  }

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));
  }, []);

  async function login(
    email: string,
    password: string,
    rememberMe = false,
  ): Promise<User> {
    const me = await authLogin({ email, password, remember_me: rememberMe });
    setUser(me);
    return me;
  }

  async function signup(
    name: string,
    email: string,
    password: string,
  ): Promise<User> {
    const me = await authSignup({ name, email, password });
    setUser(me);
    return me;
  }

  async function logout() {
    await authLogout();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, isLoading, login, signup, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
