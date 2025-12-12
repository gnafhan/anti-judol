'use client';

/**
 * ScanFlow Component - Gambling Comment Detector
 * 
 * Provides a clear UX flow for scanning:
 * 1. Start scan (create job)
 * 2. Show progress with polling
 * 3. Display results when complete
 * 
 * Requirements: 3.7, 9.2
 */

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  MdSearch, 
  MdCheckCircle, 
  MdError, 
  MdHourglassEmpty,
  MdAnalytics,
  MdOpenInNew
} from 'react-icons/md';
import Card from 'components/card';
import { api } from 'lib/api';
import type { ScanResponse, ScanDetailResponse, ScanStatus } from 'lib/types';

interface ScanFlowProps {
  videoId: string;
  videoTitle?: string;
  isOwnVideo?: boolean;
  onComplete?: (result: ScanDetailResponse) => void;
  onError?: (error: string) => void;
}

type FlowStep = 'idle' | 'starting' | 'pending' | 'processing' | 'completed' | 'failed';

interface StepConfig {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
  bgColor: string;
}

const stepConfigs: Record<FlowStep, StepConfig> = {
  idle: {
    icon: <MdSearch className="h-8 w-8" />,
    title: 'Ready to Scan',
    description: 'Click the button below to start scanning for gambling comments',
    color: 'text-gray-600 dark:text-gray-400',
    bgColor: 'bg-gray-100 dark:bg-navy-700',
  },
  starting: {
    icon: <MdHourglassEmpty className="h-8 w-8 animate-pulse" />,
    title: 'Starting Scan...',
    description: 'Creating scan job and queuing for processing',
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
  },
  pending: {
    icon: <MdHourglassEmpty className="h-8 w-8 animate-bounce" />,
    title: 'Queued',
    description: 'Scan is in queue, waiting for worker to pick it up',
    color: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-50 dark:bg-amber-900/20',
  },
  processing: {
    icon: <MdAnalytics className="h-8 w-8 animate-pulse" />,
    title: 'Analyzing Comments',
    description: 'Fetching comments and running ML predictions...',
    color: 'text-brand-600 dark:text-brand-400',
    bgColor: 'bg-brand-50 dark:bg-brand-900/20',
  },
  completed: {
    icon: <MdCheckCircle className="h-8 w-8" />,
    title: 'Scan Complete!',
    description: 'Analysis finished. View the results below.',
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-50 dark:bg-green-900/20',
  },
  failed: {
    icon: <MdError className="h-8 w-8" />,
    title: 'Scan Failed',
    description: 'Something went wrong. Please try again.',
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-50 dark:bg-red-900/20',
  },
};

const ScanFlow = ({ videoId, videoTitle, isOwnVideo = false, onComplete, onError }: ScanFlowProps) => {
  const router = useRouter();
  const [step, setStep] = useState<FlowStep>('idle');
  const [scan, setScan] = useState<ScanResponse | null>(null);
  const [result, setResult] = useState<ScanDetailResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pollCount, setPollCount] = useState(0);

  /**
   * Start the scan process
   */
  const startScan = useCallback(async () => {
    setStep('starting');
    setErrorMessage(null);
    setPollCount(0);

    try {
      const scanResponse = await api.scan.create(videoId, undefined, isOwnVideo);
      setScan(scanResponse);
      setStep('pending');
    } catch (err) {
      console.error('Failed to start scan:', err);
      setStep('failed');
      const message = err instanceof Error ? err.message : 'Failed to start scan';
      setErrorMessage(message);
      onError?.(message);
    }
  }, [videoId, isOwnVideo, onError]);

  /**
   * Poll scan status
   */
  useEffect(() => {
    if (!scan || step === 'completed' || step === 'failed' || step === 'idle' || step === 'starting') {
      return;
    }

    const pollStatus = async () => {
      try {
        const status = await api.scan.status(scan.id);
        setPollCount(prev => prev + 1);

        if (status.status === 'processing') {
          setStep('processing');
        } else if (status.status === 'completed') {
          setStep('completed');
          // Fetch full results
          const fullResult = await api.scan.get(scan.id);
          setResult(fullResult);
          onComplete?.(fullResult);
        } else if (status.status === 'failed') {
          setStep('failed');
          setErrorMessage(status.error_message || 'Scan failed');
          onError?.(status.error_message || 'Scan failed');
        }
      } catch (err) {
        console.error('Failed to poll status:', err);
        // Don't fail on poll errors, just continue
      }
    };

    const interval = setInterval(pollStatus, 2000);
    pollStatus(); // Initial poll

    return () => clearInterval(interval);
  }, [scan, step, onComplete, onError]);

  /**
   * Reset to try again
   */
  const reset = () => {
    setStep('idle');
    setScan(null);
    setResult(null);
    setErrorMessage(null);
    setPollCount(0);
  };

  const config = stepConfigs[step];
  const isActive = step !== 'idle' && step !== 'completed' && step !== 'failed';

  return (
    <Card extra={`!p-6 ${config.bgColor} border-2 border-transparent ${isActive ? 'border-current' : ''}`}>
      {/* Progress Steps Indicator */}
      <div className="flex items-center justify-center gap-2 mb-6">
        {['pending', 'processing', 'completed'].map((s, i) => {
          const stepIndex = ['pending', 'processing', 'completed'].indexOf(step);
          const currentIndex = i;
          const isCompleted = stepIndex > currentIndex || step === 'completed';
          const isCurrent = step === s;
          
          return (
            <div key={s} className="flex items-center">
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                ${isCompleted ? 'bg-green-500 text-white' : 
                  isCurrent ? `${config.bgColor} ${config.color} border-2 border-current` : 
                  'bg-gray-200 dark:bg-navy-600 text-gray-400'}
              `}>
                {isCompleted ? '✓' : i + 1}
              </div>
              {i < 2 && (
                <div className={`w-12 h-1 mx-1 rounded ${
                  isCompleted ? 'bg-green-500' : 'bg-gray-200 dark:bg-navy-600'
                }`} />
              )}
            </div>
          );
        })}
      </div>

      {/* Main Content */}
      <div className="text-center">
        {/* Icon */}
        <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${config.bgColor} ${config.color} mb-4`}>
          {config.icon}
        </div>

        {/* Title & Description */}
        <h3 className={`text-xl font-bold ${config.color} mb-2`}>
          {config.title}
        </h3>
        <p className={`text-sm ${config.color} opacity-80 mb-4`}>
          {errorMessage || config.description}
        </p>

        {/* Video Title */}
        {videoTitle && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Video: <span className="font-medium">{videoTitle}</span>
          </p>
        )}

        {/* Poll Counter (for active states) */}
        {isActive && (
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent opacity-50" />
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Checking status... ({pollCount} checks)
            </span>
          </div>
        )}

        {/* Results Summary */}
        {step === 'completed' && result && (
          <div className="flex items-center justify-center gap-6 mb-4 p-4 bg-white dark:bg-navy-800 rounded-xl">
            <div className="text-center">
              <p className="text-2xl font-bold text-navy-700 dark:text-white">
                {result.total_comments}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Total Comments</p>
            </div>
            <div className="h-10 w-px bg-gray-200 dark:bg-navy-600" />
            <div className="text-center">
              <p className="text-2xl font-bold text-red-500">
                {result.gambling_count}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Gambling</p>
            </div>
            <div className="h-10 w-px bg-gray-200 dark:bg-navy-600" />
            <div className="text-center">
              <p className="text-2xl font-bold text-green-500">
                {result.clean_count}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Clean</p>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-center gap-3">
          {step === 'idle' && (
            <button
              onClick={startScan}
              className="flex items-center gap-2 px-6 py-3 bg-brand-500 text-white rounded-xl hover:bg-brand-600 transition-colors font-semibold"
            >
              <MdSearch className="h-5 w-5" />
              Start Scan
            </button>
          )}

          {step === 'failed' && (
            <>
              <button
                onClick={reset}
                className="flex items-center gap-2 px-6 py-3 bg-brand-500 text-white rounded-xl hover:bg-brand-600 transition-colors font-semibold"
              >
                <MdSearch className="h-5 w-5" />
                Try Again
              </button>
            </>
          )}

          {step === 'completed' && result && (
            <>
              <button
                onClick={() => router.push(`/admin/scan/${result.id}`)}
                className="flex items-center gap-2 px-6 py-3 bg-brand-500 text-white rounded-xl hover:bg-brand-600 transition-colors font-semibold"
              >
                <MdOpenInNew className="h-5 w-5" />
                View Full Results
              </button>
              <button
                onClick={reset}
                className="flex items-center gap-2 px-4 py-3 bg-gray-100 dark:bg-navy-700 text-navy-700 dark:text-white rounded-xl hover:bg-gray-200 dark:hover:bg-navy-600 transition-colors"
              >
                Scan Again
              </button>
            </>
          )}
        </div>
      </div>
    </Card>
  );
};

export default ScanFlow;
