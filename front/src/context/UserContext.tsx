import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";
import type { UserRecord } from "@/lib/types";

type UserContextValue = {
  currentUser: UserRecord | null;
  setCurrentUser: (user: UserRecord | null) => void;
};

const STORAGE_KEY = "pepe-grillo-user";

const UserContext = createContext<UserContextValue | undefined>(undefined);

export function UserProvider({ children }: PropsWithChildren) {
  const [currentUser, setCurrentUserState] = useState<UserRecord | null>(null);

  useEffect(() => {
    const rawValue = window.localStorage.getItem(STORAGE_KEY);
    if (!rawValue) {
      return;
    }
    setCurrentUserState(JSON.parse(rawValue) as UserRecord);
  }, []);

  const setCurrentUser = useCallback((user: UserRecord | null) => {
    setCurrentUserState(user);
    if (user) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
      return;
    }
    window.localStorage.removeItem(STORAGE_KEY);
  }, []);

  const value = useMemo(
    () => ({
      currentUser,
      setCurrentUser,
    }),
    [currentUser, setCurrentUser],
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within UserProvider.");
  }
  return context;
}
