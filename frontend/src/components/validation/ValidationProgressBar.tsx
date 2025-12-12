'use client';

/**
 * ValidationProgressBar Component - Auto ML Retraining
 * 
 * Displays validation progress and contribution toward model retraining.
 * Shows motivational messages when approaching retraining threshold.
 * 
 * Requirements: 4.1, 4.2, 4.3
 */

import { useMemo } from 'react';
import { MdCheckCircle, MdEdit, MdAutorenew, MdTrendingUp } from 'react-icons/md';

export interface ValidationProgressProps {
  /** Total number of comments in the scan */
  totalComments: number;
  /** Number of validated comments */
  validatedCount: number;
  /** Number of corrections made */
  correctionsCount: number;
  /** Progress toward retraining threshold (0-100) */
  thresholdProgress: number;
  /** Retraining threshold value */
  threshold?: number;
  /** Whether to show compact version */
  compact?: boolean;
}

/**
 * Get motivational message based on threshold progress
 * Requirements: 4.3 - Display motivational message near threshold
 */
function getMotivationalMessage(progress: number): string | null {
  if (progress >= 100) {
    return '🎉 Threshold reached! Model retraining will begin soon.';
  }
  if (progress >= 90) {
    return '🔥 Almost there! Just a few more validations to improve the model.';
  }
  if (progress >= 80) {
    return '💪 Great progress! Your validations are making a difference.';
  }
  if (progress >= 50) {
    return '📈 Halfway there! Keep validating to help improve accuracy.';
  }
  return null;
}

/**
 * Check if threshold progress should show notification
 * Requirements: 4.3 - Show message when count reaches 80% or more
 */
export function shouldShowThresholdNotification(progress: number): boolean {
  return progress >= 80;
}

/**
 * ValidationProgressBar - Shows validation progress and retraining contribution
 * 
 * Displays:
 * - Validated vs unvalidated comment counts
 * - Progress bar for scan validation
 * - Progress toward retraining threshold
 * - Motivational messages near threshold
 * 
 * @example
 * ```tsx
 * <ValidationProgressBar
 *   totalComments={100}
 *   validatedCount={45}
 *   correctionsCount={12}
 *   thresholdProgress={75}
 *   threshold={100}
 * />
 * ```
 */
const ValidationProgressBar = ({
  totalComments,
  validatedCount,
  correctionsCount,
  thresholdProgress,
  threshold = 100,
  compact = false,
}: ValidationProgressProps) => {
  // Calculate scan validation progress
  const scanProgress = useMemo(() => {
    if (totalComments === 0) return 0;
    return Math.round((validatedCount / totalComments) * 100);
  }, [validatedCount, totalComments]);

  // Get motivational message
  const motivationalMessage = useMemo(() => {
    return getMotivationalMessage(thresholdProgress);
  }, [thresholdProgress]);

  // Determine if we should highlight threshold progress
  const showThresholdHighlight = shouldShowThresholdNotification(thresholdProgress);

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        {/* Compact stats */}
        <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
          <MdCheckCircle className="h-3.5 w-3.5 text-green-500" />
          <span>{validatedCount}/{totalComments}</span>
        </div>
        
        {/* Compact progress bar */}
        <div className="flex-1 h-1.5 bg-gray-200 dark:bg-navy-600 rounded-full overflow-hidden">
          <div 
            className="h-full bg-brand-500 rounded-full transition-all duration-300"
            style={{ width: `${scanProgress}%` }}
          />
        </div>
        
        {/* Threshold indicator */}
        {showThresholdHighlight && (
          <div className="flex items-center gap-1 text-xs text-amber-500">
            <MdAutorenew className="h-3.5 w-3.5 animate-spin" />
            <span>{thresholdProgress}%</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-4 bg-white dark:bg-navy-800 rounded-xl shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-navy-700 dark:text-white">
          Validation Progress
        </h4>
        <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
          <MdTrendingUp className="h-4 w-4" />
          <span>Help improve the model</span>
        </div>
      </div>

      {/* Scan Validation Progress */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Scan Progress
          </span>
          <span className="text-xs font-medium text-navy-700 dark:text-white">
            {validatedCount} / {totalComments} validated
          </span>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-navy-600 rounded-full overflow-hidden">
          <div 
            className="h-full bg-brand-500 rounded-full transition-all duration-300"
            style={{ width: `${scanProgress}%` }}
          />
        </div>
      </div>

      {/* Stats Row */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex items-center gap-1.5">
          <div className="p-1.5 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <MdCheckCircle className="h-4 w-4 text-green-500" />
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Validated</p>
            <p className="text-sm font-semibold text-navy-700 dark:text-white">
              {validatedCount}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-1.5">
          <div className="p-1.5 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
            <MdEdit className="h-4 w-4 text-amber-500" />
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Corrections</p>
            <p className="text-sm font-semibold text-navy-700 dark:text-white">
              {correctionsCount}
            </p>
          </div>
        </div>
      </div>

      {/* Retraining Threshold Progress */}
      
    </div>
  );
};

export default ValidationProgressBar;
