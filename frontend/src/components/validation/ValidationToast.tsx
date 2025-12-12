'use client';

/**
 * ValidationToast Component - Auto ML Retraining
 * 
 * Displays toast notifications for validation actions with undo capability.
 * Auto-dismisses after 5 seconds unless user interacts.
 * 
 * Requirements: 1.4, 7.1
 */

import { useEffect, useState, useCallback } from 'react';
import { MdCheck, MdEdit, MdUndo, MdClose } from 'react-icons/md';
import type { ValidationResponse } from 'lib/types';

export interface ValidationToastProps {
  /** The validation that was just submitted */
  validation: ValidationResponse | null;
  /** Time remaining for undo (in seconds) */
  undoTimeRemaining: number;
  /** Whether undo is available */
  canUndo: boolean;
  /** Callback when user clicks undo - can be sync or async */
  onUndo: () => void | Promise<boolean>;
  /** Callback when toast is dismissed */
  onDismiss: () => void;
  /** Whether undo operation is in progress */
  isUndoing?: boolean;
}

/**
 * ValidationToast - Toast notification for validation actions
 * 
 * Shows a brief confirmation when a user validates a prediction,
 * with an undo button that's available for 5 seconds.
 * 
 * Requirements:
 * - 1.4: Show brief toast notification confirming action without blocking UI
 * - 7.1: Display "Undo" option in toast notification for 5 seconds
 * 
 * @example
 * ```tsx
 * <ValidationToast
 *   validation={recentValidation}
 *   undoTimeRemaining={undoTimeRemaining}
 *   canUndo={canUndo}
 *   onUndo={handleUndo}
 *   onDismiss={clearRecentValidation}
 * />
 * ```
 */
const ValidationToast = ({
  validation,
  undoTimeRemaining,
  canUndo,
  onUndo,
  onDismiss,
  isUndoing = false,
}: ValidationToastProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  // Show toast when validation changes
  useEffect(() => {
    if (validation) {
      setIsVisible(true);
      setIsExiting(false);
    }
  }, [validation]);

  // Hide toast when undo window expires
  useEffect(() => {
    if (!canUndo && validation) {
      handleDismiss();
    }
  }, [canUndo, validation]);

  /**
   * Handle dismiss with exit animation
   */
  const handleDismiss = useCallback(() => {
    setIsExiting(true);
    // Wait for exit animation before calling onDismiss
    setTimeout(() => {
      setIsVisible(false);
      setIsExiting(false);
      onDismiss();
    }, 200);
  }, [onDismiss]);

  /**
   * Handle undo click
   */
  const handleUndo = useCallback(() => {
    if (canUndo && !isUndoing) {
      onUndo();
    }
  }, [canUndo, isUndoing, onUndo]);

  // Don't render if no validation or not visible
  if (!validation || !isVisible) {
    return null;
  }

  const isCorrection = validation.is_correction;
  const correctedLabel = validation.corrected_label;

  // Determine message based on validation type
  const getMessage = () => {
    if (isCorrection) {
      return correctedLabel ? 'Marked as Gambling' : 'Marked as Clean';
    }
    return 'Prediction Confirmed';
  };

  return (
    <div
      className={`
        fixed bottom-4 right-4 z-50
        flex items-center gap-3
        px-4 py-3 rounded-lg shadow-lg
        bg-white dark:bg-navy-700
        border border-gray-200 dark:border-navy-600
        transition-all duration-200 ease-out
        ${isExiting ? 'opacity-0 translate-y-2' : 'opacity-100 translate-y-0'}
      `}
      role="alert"
      aria-live="polite"
    >
      {/* Icon */}
      <div
        className={`
          flex items-center justify-center
          w-8 h-8 rounded-full
          ${isCorrection
            ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400'
            : 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
          }
        `}
      >
        {isCorrection ? (
          <MdEdit className="w-4 h-4" />
        ) : (
          <MdCheck className="w-4 h-4" />
        )}
      </div>

      {/* Message */}
      <div className="flex flex-col">
        <span className="text-sm font-medium text-gray-900 dark:text-white">
          {getMessage()}
        </span>
        {canUndo && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {undoTimeRemaining}s to undo
          </span>
        )}
      </div>

      {/* Undo Button */}
      {canUndo && (
        <button
          onClick={handleUndo}
          disabled={isUndoing}
          className={`
            flex items-center gap-1
            px-3 py-1.5 ml-2
            text-sm font-medium
            rounded-md
            transition-colors
            ${isUndoing
              ? 'bg-gray-100 dark:bg-navy-600 text-gray-400 dark:text-gray-500 cursor-not-allowed'
              : 'bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 hover:bg-brand-100 dark:hover:bg-brand-900/50'
            }
          `}
          aria-label="Undo validation"
        >
          {isUndoing ? (
            <>
              <div className="w-3 h-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
              <span>Undoing...</span>
            </>
          ) : (
            <>
              <MdUndo className="w-4 h-4" />
              <span>Undo</span>
            </>
          )}
        </button>
      )}

      {/* Close Button */}
      <button
        onClick={handleDismiss}
        className="
          p-1 ml-1
          text-gray-400 dark:text-gray-500
          hover:text-gray-600 dark:hover:text-gray-300
          rounded-md
          transition-colors
        "
        aria-label="Dismiss notification"
      >
        <MdClose className="w-4 h-4" />
      </button>

      {/* Progress Bar (visual countdown) */}
      {canUndo && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-100 dark:bg-navy-600 rounded-b-lg overflow-hidden">
          <div
            className="h-full bg-brand-500 transition-all duration-1000 ease-linear"
            style={{ width: `${(undoTimeRemaining / 5) * 100}%` }}
          />
        </div>
      )}
    </div>
  );
};

export default ValidationToast;
