import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, UserRole } from '../types';
import { api } from '../api/services';

interface AuthContextType {
  user: User | null;
  role: UserRole | null;
  token: string | null;
  permissions: string[];
  isAuthenticated: boolean;
  isLoading: boolean;
  unreadCount: number;
  setUnreadCount: React.Dispatch<React.SetStateAction<number>>;
  login: (email: string, password: string) => Promise<User>;
  register: (data: { email: string; password: string; full_name: string; role?: string }) => Promise<User>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  role: null,
  token: null,
  permissions: [],
  isAuthenticated: false,
  isLoading: true,
  unreadCount: 0,
  setUnreadCount: () => {},
  login: async () => { throw new Error('AuthContext not initialized'); },
  register: async () => { throw new Error('AuthContext not initialized'); },
  logout: () => {},
  hasPermission: () => false,
  refreshUser: async () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('logiagent_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [unreadCount, setUnreadCount] = useState<number>(0);

  const refreshUser = useCallback(async () => {
    const currentToken = localStorage.getItem('logiagent_token');
    if (!currentToken) {
      setUser(null);
      setToken(null);
      setIsLoading(false);
      return;
    }
    try {
      const me = await api.getMe();
      setUser(me);
      setToken(currentToken);
    } catch (err) {
      console.warn('Authentication session invalid or expired:', err);
      localStorage.removeItem('logiagent_token');
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    try {
      const res = await api.login(email, password);
      localStorage.setItem('logiagent_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      return res.user;
    } catch (err: any) {
      localStorage.removeItem('logiagent_token');
      setUser(null);
      setToken(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: { email: string; password: string; full_name: string; role?: string }): Promise<User> => {
    setIsLoading(true);
    try {
      const res = await api.register(data);
      localStorage.setItem('logiagent_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      return res.user;
    } catch (err: any) {
      localStorage.removeItem('logiagent_token');
      setUser(null);
      setToken(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    api.logout().catch(() => {});
    localStorage.removeItem('logiagent_token');
    setUser(null);
    setToken(null);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    if (user.role === 'Admin') return true;
    if (!user.permissions || user.permissions.length === 0) return false;

    const target = permission.toLowerCase().trim();
    // Direct match
    if (user.permissions.includes(target)) return true;
    
    // Singular/plural alias match (e.g., shipment:read vs shipments:read)
    const altTarget = target.includes(':')
      ? (target.startsWith('shipments:') ? target.replace('shipments:', 'shipment:') : target.replace('shipment:', 'shipments:'))
      : target;
    if (user.permissions.includes(altTarget)) return true;

    // Wildcard / manage permission match
    if (target.includes(':')) {
      const [res] = target.split(':');
      if (user.permissions.includes(`${res}:manage`) || user.permissions.includes(`${res}s:manage`)) {
        return true;
      }
    }

    return false;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role || null,
        token,
        permissions: user?.permissions || [],
        isAuthenticated: !!user,
        isLoading,
        unreadCount,
        setUnreadCount,
        login,
        register,
        logout,
        hasPermission,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
