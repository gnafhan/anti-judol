'use client';

/**
 * OAuth Callback Page
 * 
 * Handles the OAuth callback from the backend API.
 * The backend redirects here with tokens in the URL.
 * 
 * Requirements: 1.2, 1.4
 */

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '../../../contexts/AuthContext';

export default function OAuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { handleOAuthCallback } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      const accessToken = searchParams.get('access_token');
      const refreshToken = searchParams.get('refresh_token');
      const errorParam = searchParams.get('error');

      if (errorParam) {
        setError(decodeURIComponent(errorParam));
        // Redirect to sign-in with error after a delay
        setTimeout(() => {
          router.push(`/auth/sign-in?error=${encodeURIComponent(errorParam)}`);
        }, 2000);
        return;
      }

      if (accessToken) {
        try {
          await handleOAuthCallback(accessToken, refreshToken || undefined);
          router.push('/admin');
        } catch (err) {
          console.error('OAuth callback error:', err);
          setError('Failed to complete authentication. Please try again.');
          setTimeout(() => {
            router.push('/auth/sign-in?error=auth_failed');
          }, 2000);
        }
      } else {
        // No token provided, redirect to sign-in
        router.push('/auth/sign-in');
      }
    };

    processCallback();
  }, [searchParams, handleOAuthCallback, router]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-navy-900">
        <div className="text-center">
          <div className="mb-4 text-red-500">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Authentication Error</h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">{error}</p>
          <p className="mt-4 text-sm text-gray-500">Redirecting to sign in...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-navy-900">
      <div className="text-center">
        <div className="h-12 w-12 mx-auto animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
        <p className="mt-4 text-gray-600 dark:text-gray-400">Completing sign in...</p>
      </div>
    </div>
  );
}
