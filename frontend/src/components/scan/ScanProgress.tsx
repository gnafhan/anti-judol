'use client';

/**
 * Scan Progress Component - Gambling Comment Detector
 * 
 * Polls scan status and shows progress indicator.
 * Requirements: 3.7, 9.2
 */

import { useEffect, useState, useCallback } from 'react';
import { MdSearch, MdCheckCircle, MdError, MdHourglassEmpty } from 'react-icons/md';
import { api } from 'lib/api';
import type { ScanStatus } from 'lib/types';

interface ScanProgressProps {
  /** The scan ID to poll status for */
  scanId: string;
  /** Initial status (optional) */
  initialStatus?: ScanStatus;
  /** Callback when scan completes successfully */
  onComplete?: (scanId: string) => void;
  /** Callback when scan fails */
  onFailed?: (scanId: string, errorMessage?: string) => void;
  /** Polling interval in milliseconds (default: 2000) */
  pollInterval?: number;
  /** Whether to show compact version */
  compact?: boolean;
}

interface StatusInfo {
  icon: React.ReactNode;
  label: string;
  color: string;
  bgColor: string;
  description: string;
}

const statusConfig: Record<ScanStatus, StatusInfo> = {
  pending: {
    icon: <MdHourglassEmpty className="h-5 w-5" />,
    label: 'Pending',
    color: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-100 dark:bg-amber-900/30',
    description: 'Scan is queued and waiting to start...',
  },
  processing: {
    icon: <MdSearch className="h-5 w-5 animate-pulse" />,
    label: 'Processing',
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    description: 'Analyzing comments for gambling content...',
  },
  completed: {
    icon: <MdCheckCircle className="h-5 w-5" />,
    label: 'Completed',
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    description: 'Scan completed successfully!',
  },
  failed: {
    icon: <MdError className="h-5 w-5" />,
    label: 'Failed',
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
    description: 'Scan failed. Please try again.',
  },
};

/**
 * ScanProgress component that polls scan status and displays progress
 * 
 * @example
 * ```tsx
 * <ScanProgress 
 *   scanId="abc123"
 *   onComplete={(id) => router.push(`/admin/scan/${id}`)}
 *   onFailed={(id, error) => setError(error)}
 * />
 * ```
 */
const ScanProgress = ({
  scanId,
  initialStatus = 'pending',
  onComplete,
  onFailed,
  pollInterval = 2000,
  compact = false,
}: ScanProgressProps) => {
  const [status, setStatus] = useState<ScanStatus>(initialStatus);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(true);

  /**
   * Poll scan status from API
   * Requirements: 3.7 - Allow status polling via GET /api/scan/{scan_id}/status
   */
  const pollStatus = useCallback(async () => {
    try {
      const response = await api.scan.status(scanId);
      setStatus(response.status as ScanStatus);

      if (response.status === 'completed') {
        setIsPolling(false);
        onComplete?.(scanId);
      } else if (response.status === 'failed') {
        setIsPolling(false);
        setErrorMessage(response.error_message || 'Unknown error occurred');
        onFailed?.(scanId, response.error_message);
      }
    } catch (err) {
      console.error('Failed to poll scan status:', err);
      // Don't stop polling on network errors, just log them
    }
  }, [scanId, onComplete, onFailed]);

  /**
   * Set up polling interval
   * Requirements: 9.2 - Update scan status progressively
   */
  useEffect(() => {
    if (!isPolling) return;

    // Initial poll
    pollStatus();

    // Set up interval
    const interval = setInterval(pollStatus, pollInterval);

    return () => clearInterval(interval);
  }, [isPolling, pollStatus, pollInterval]);

  const config = statusConfig[status];

  // Compact version for inline display
  if (compact) {
    return (
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bgColor}`}>
        <span className={config.color}>{config.icon}</span>
        <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
        {(status === 'pending' || status === 'processing') && (
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent opacity-50" />
        )}
      </div>
    );
  }

  // Full version with description
  return (
    <div className={`p-4 rounded-xl ${config.bgColor}`}>
      <div className="flex items-center gap-3">
        {/* Status Icon */}
        <div className={`flex-shrink-0 ${config.color}`}>
          {(status === 'pending' || status === 'processing') ? (
            <div className="relative">
              {config.icon}
              <div className="absolute inset-0 animate-ping opacity-30">
                {config.icon}
              </div>
            </div>
          ) : (
            config.icon
          )}
        </div>

        {/* Status Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`font-semibold ${config.color}`}>{config.label}</span>
            {(status === 'pending' || status === 'processing') && (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent opacity-50" />
            )}
          </div>
          <p className={`text-sm ${config.color} opacity-80`}>
            {errorMessage || config.description}
          </p>
        </div>

        {/* Progress indicator for active states */}
        {(status === 'pending' || status === 'processing') && (
          <div className="flex-shrink-0">
            <div className="w-16 h-1.5 bg-white/30 rounded-full overflow-hidden">
              <div 
                className={`h-full ${status === 'processing' ? 'w-2/3' : 'w-1/3'} ${config.color.replace('text-', 'bg-')} rounded-full animate-pulse`}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanProgress;
