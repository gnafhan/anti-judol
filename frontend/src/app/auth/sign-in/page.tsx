'use client';

/**
 * Sign In Page with Google OAuth
 * 
 * Provides Google OAuth login button for authentication.
 * Requirements: 1.1, 1.2, 1.4
 */

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Default from 'components/auth/variants/DefaultAuthLayout';
import { FcGoogle } from 'react-icons/fc';
import { useAuth } from '../../../contexts/AuthContext';

function SignInDefault() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, handleOAuthCallback, isAuthenticated, isLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Handle OAuth callback
  useEffect(() => {
    const processCallback = async () => {
      const accessToken = searchParams.get('access_token');
      const refreshToken = searchParams.get('refresh_token');
      const errorParam = searchParams.get('error');

      if (errorParam) {
        setError(decodeURIComponent(errorParam));
        return;
      }

      if (accessToken) {
        setIsProcessing(true);
        try {
          await handleOAuthCallback(accessToken, refreshToken || undefined);
          router.push('/admin');
        } catch (err) {
          setError('Failed to complete authentication. Please try again.');
          console.error('OAuth callback error:', err);
        } finally {
          setIsProcessing(false);
        }
      }
    };

    processCallback();
  }, [searchParams, handleOAuthCallback, router]);


  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/admin');
    }
  }, [isAuthenticated, isLoading, router]);

  const handleGoogleLogin = () => {
    setError(null);
    login();
  };

  // Show loading state while checking auth or processing callback
  if (isLoading || isProcessing) {
    return (
      <Default
        maincard={
          <div className="mb-16 mt-16 flex h-full w-full items-center justify-center px-2 md:mx-0 md:px-0 lg:mb-10 lg:items-center lg:justify-start">
            <div className="mt-[10vh] w-full max-w-full flex-col items-center md:pl-4 lg:pl-0 xl:max-w-[420px]">
              <div className="flex flex-col items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent"></div>
                <p className="mt-4 text-gray-600">
                  {isProcessing ? 'Completing sign in...' : 'Loading...'}
                </p>
              </div>
            </div>
          </div>
        }
      />
    );
  }

  return (
    <Default
      maincard={
        <div className="mb-16 mt-16 flex h-full w-full items-center justify-center px-2 md:mx-0 md:px-0 lg:mb-10 lg:items-center lg:justify-start">
          {/* Sign in section */}
          <div className="mt-[10vh] w-full max-w-full flex-col items-center md:pl-4 lg:pl-0 xl:max-w-[420px]">
            <h3 className="mb-2.5 text-4xl font-bold text-navy-700 dark:text-white">
              Sign In
            </h3>
            <p className="mb-9 ml-1 text-base text-gray-600">
              Sign in with your Google account to detect gambling comments on YouTube videos.
            </p>

            {/* Error message */}
            {error && (
              <div className="mb-6 rounded-xl bg-red-50 p-4 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400">
                {error}
              </div>
            )}

            {/* Google OAuth button */}
            <button
              onClick={handleGoogleLogin}
              className="mb-6 flex h-[50px] w-full items-center justify-center gap-2 rounded-xl bg-lightPrimary transition-all duration-200 hover:cursor-pointer hover:bg-gray-200 dark:bg-navy-800 dark:text-white dark:hover:bg-navy-700"
            >
              <div className="rounded-full text-xl">
                <FcGoogle />
              </div>
              <p className="text-sm font-medium text-navy-700 dark:text-white">
                Sign In with Google
              </p>
            </button>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                By signing in, you agree to allow access to your YouTube account
                for comment scanning and management.
              </p>
            </div>
          </div>
        </div>
      }
    />
  );
}

export default SignInDefault;
