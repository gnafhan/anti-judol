'use client';

/**
 * Authentication Context Provider
 * 
 * Manages authentication state and provides login/logout functionality.
 * Requirements: 1.1, 1.2, 1.4, 1.6
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { api, getAccessToken, setTokens, clearTokens } from '../lib/api';
import type { UserResponse } from '../lib/types';

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => void;
  logout: () => Promise<void>;
  handleOAuthCallback: (accessToken: string, refreshToken?: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getAccessToken();
      if (token) {
        try {
          const userData = await api.auth.me();
          setUser(userData);
        } catch (error) {
          // Token invalid or expired, clear it
          clearTokens();
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);


  /**
   * Redirect to Google OAuth login
   * Requirements: 1.1
   */
  const login = useCallback(() => {
    const authUrl = api.auth.getGoogleAuthUrl();
    window.location.href = authUrl;
  }, []);

  /**
   * Handle OAuth callback - store tokens and fetch user
   * Requirements: 1.2, 1.4
   */
  const handleOAuthCallback = useCallback(async (accessToken: string, refreshToken?: string) => {
    setTokens(accessToken, refreshToken);
    try {
      const userData = await api.auth.me();
      setUser(userData);
    } catch (error) {
      clearTokens();
      throw error;
    }
  }, []);

  /**
   * Logout - revoke tokens and clear state
   * Requirements: 1.6
   */
  const logout = useCallback(async () => {
    try {
      await api.auth.logout();
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API error:', error);
    } finally {
      clearTokens();
      setUser(null);
      window.location.href = '/auth/sign-in';
    }
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    handleOAuthCallback,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access authentication context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
