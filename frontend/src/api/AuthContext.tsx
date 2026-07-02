import { createContext, useState, useCallback, useEffect, useContext, type ReactNode } from 'react';
import { API_BASE_URL } from './config';

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export interface Annotator {
  id: number;
  username: string;
}

export interface Assignment {
  query_id: string;
  query: string;
}

interface AuthState {
  token: string | null;
  annotator: Annotator | null;
  assignments: Assignment[];
  loading: boolean;
}

export interface AuthContextValue extends AuthState {
  signup: (username: string, password: string) => Promise<void>;
  signin: (username: string, password: string) => Promise<void>;
  signout: () => void;
  authFetch: (url: string, options?: RequestInit) => Promise<Response>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = 'annotation_token';

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<AuthState>({
    token: localStorage.getItem(TOKEN_KEY),
    annotator: null,
    assignments: [],
    loading: true,
  });

  const authFetch = useCallback((url: string, options?: RequestInit): Promise<Response> => {
    const token = localStorage.getItem(TOKEN_KEY);
    const headers = new Headers(options?.headers);
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    return fetch(url, { ...options, headers });
  }, []);

  const fetchMe = useCallback(async (token: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        localStorage.removeItem(TOKEN_KEY);
        setState({ token: null, annotator: null, assignments: [], loading: false });
        return;
      }
      const data = await response.json();
      setState({
        token,
        annotator: data.annotator,
        assignments: data.assignments,
        loading: false,
      });
    } catch {
      localStorage.removeItem(TOKEN_KEY);
      setState({ token: null, annotator: null, assignments: [], loading: false });
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      fetchMe(token);
    } else {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [fetchMe]);

  const signup = useCallback(async (username: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Signup failed');
    }
    const data = await response.json();
    localStorage.setItem(TOKEN_KEY, data.token);
    setState({
      token: data.token,
      annotator: data.annotator,
      assignments: data.assignments,
      loading: false,
    });
  }, []);

  const signin = useCallback(async (username: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Signin failed');
    }
    const data = await response.json();
    localStorage.setItem(TOKEN_KEY, data.token);
    setState({
      token: data.token,
      annotator: data.annotator,
      assignments: data.assignments,
      loading: false,
    });
  }, []);

  const signout = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      try {
        await fetch(`${API_BASE_URL}/auth/signout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        // ignore network errors on signout
      }
    }
    localStorage.removeItem(TOKEN_KEY);
    setState({ token: null, annotator: null, assignments: [], loading: false });
  }, []);

  const value: AuthContextValue = {
    ...state,
    signup,
    signin,
    signout,
    authFetch,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
