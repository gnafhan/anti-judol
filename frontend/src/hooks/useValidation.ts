'use client';

/**
 * useValidation Hook - Auto ML Retraining
 * 
 * Manages validation state and provides methods for submitting,
 * batch validating, and undoing validations.
 * 
 * Requirements: 1.2, 2.3, 7.1, 7.2, 7.3
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from 'lib/api';
import type {
  ValidationResponse,
  ValidationStats,
  BatchValidationResult,
  BatchAction,
} from 'lib/types';

/** Undo window duration in milliseconds (5 seconds) */
const UNDO_WINDOW_MS = 5000;

export interface UseValidationOptions {
  /** Callback when validation is submitted successfully */
  onValidationSuccess?: (validation: ValidationResponse) => void;
  /** Callback when validation fails */
  onValidationError?: (error: Error) => void;
  /** Callback when batch validation completes */
  onBatchComplete?: (result: BatchValidationResult) => void;
  /** Callback when undo is successful */
  onUndoSuccess?: () => void;
  /** Callback when undo fails */
  onUndoError?: (error: Error) => void;
  /** Auto-fetch stats on mount */
  autoFetchStats?: boolean;
  /** Enable toast notifications (default: true) */
  showToast?: boolean;
}

export interface UseValidationReturn {
  /** Submit a single validation */
  submitValidation: (
    resultId: string,
    isCorrect: boolean,
    correctedLabel?: boolean
  ) => Promise<ValidationResponse | null>;
  /** Submit batch validation */
  batchValidate: (
    resultIds: string[],
    action: BatchAction
  ) => Promise<BatchValidationResult | null>;
  /** Undo the most recent validation (within time window) */
  undoValidation: () => Promise<boolean>;
  /** Validation statistics */
  validationStats: ValidationStats | null;
  /** Refresh validation statistics */
  refreshStats: () => Promise<void>;
  /** Whether a validation operation is in progress */
  isLoading: boolean;
  /** Whether batch validation is in progress */
  isBatchLoading: boolean;
  /** Most recent validation (for undo toast) */
  recentValidation: ValidationResponse | null;
  /** Whether undo is available for recent validation */
  canUndo: boolean;
  /** Time remaining for undo (in seconds) */
  undoTimeRemaining: number;
  /** Clear the recent validation (dismiss undo option) */
  clearRecentValidation: () => void;
  /** Error from last operation */
  error: Error | null;
  /** Props to pass to ValidationToast component */
  toastProps: {
    validation: ValidationResponse | null;
    undoTimeRemaining: number;
    canUndo: boolean;
    onUndo: () => Promise<boolean>;
    onDismiss: () => void;
    isUndoing: boolean;
  };
}


/**
 * Custom hook for managing validation operations
 * 
 * Provides methods for submitting validations, batch operations,
 * and undo functionality with time-limited window.
 * 
 * Requirements: 1.2, 2.3, 7.1, 7.2, 7.3
 * 
 * @example
 * ```tsx
 * import { ValidationToast } from 'components/validation';
 * 
 * const {
 *   submitValidation,
 *   batchValidate,
 *   toastProps,
 * } = useValidation({
 *   onValidationSuccess: (v) => console.log('Validated!'),
 *   onUndoSuccess: () => console.log('Validation undone'),
 * });
 * 
 * // Submit single validation
 * await submitValidation(resultId, true); // Confirm correct
 * await submitValidation(resultId, false, true); // Correct to gambling
 * 
 * // Batch validation
 * await batchValidate(selectedIds, 'confirm_all');
 * 
 * // Render toast with undo functionality
 * return (
 *   <>
 *     {/* Your content *\/}
 *     <ValidationToast {...toastProps} />
 *   </>
 * );
 * ```
 */
export function useValidation(options: UseValidationOptions = {}): UseValidationReturn {
  const {
    onValidationSuccess,
    onValidationError,
    onBatchComplete,
    onUndoSuccess,
    onUndoError,
    autoFetchStats = false,
    showToast = true,
  } = options;

  // State
  const [isLoading, setIsLoading] = useState(false);
  const [isBatchLoading, setIsBatchLoading] = useState(false);
  const [validationStats, setValidationStats] = useState<ValidationStats | null>(null);
  const [recentValidation, setRecentValidation] = useState<ValidationResponse | null>(null);
  const [undoTimeRemaining, setUndoTimeRemaining] = useState(0);
  const [error, setError] = useState<Error | null>(null);

  // Refs for timer management
  const undoTimerRef = useRef<NodeJS.Timeout | null>(null);
  const countdownRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Clear undo timers
   */
  const clearUndoTimers = useCallback(() => {
    if (undoTimerRef.current) {
      clearTimeout(undoTimerRef.current);
      undoTimerRef.current = null;
    }
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
  }, []);

  /**
   * Clear recent validation and timers
   */
  const clearRecentValidation = useCallback(() => {
    clearUndoTimers();
    setRecentValidation(null);
    setUndoTimeRemaining(0);
  }, [clearUndoTimers]);

  /**
   * Start undo countdown timer
   * Requirements: 7.1 - Display "Undo" option for 5 seconds
   */
  const startUndoTimer = useCallback((validation: ValidationResponse) => {
    clearUndoTimers();
    setRecentValidation(validation);
    setUndoTimeRemaining(5);

    // Countdown timer (updates every second)
    countdownRef.current = setInterval(() => {
      setUndoTimeRemaining((prev) => {
        if (prev <= 1) {
          clearUndoTimers();
          setRecentValidation(null);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    // Auto-clear after undo window expires
    // Requirements: 7.3 - Persist validation after window expires
    undoTimerRef.current = setTimeout(() => {
      clearRecentValidation();
    }, UNDO_WINDOW_MS);
  }, [clearUndoTimers, clearRecentValidation]);

  /**
   * Fetch validation statistics
   */
  const refreshStats = useCallback(async () => {
    try {
      const stats = await api.validation.stats();
      setValidationStats(stats);
    } catch (err) {
      console.error('Failed to fetch validation stats:', err);
    }
  }, []);

  /**
   * Submit a single validation
   * Requirements: 1.2 - Mark prediction as confirmed/corrected
   */
  const submitValidation = useCallback(
    async (
      resultId: string,
      isCorrect: boolean,
      correctedLabel?: boolean
    ): Promise<ValidationResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const validation = await api.validation.submit(resultId, isCorrect, correctedLabel);
        
        // Start undo timer for this validation
        // Requirements: 7.1 - Display undo option in toast
        if (validation.can_undo) {
          startUndoTimer(validation);
        }

        onValidationSuccess?.(validation);
        
        // Refresh stats after successful validation
        refreshStats();

        return validation;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Validation failed');
        setError(error);
        onValidationError?.(error);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [onValidationSuccess, onValidationError, startUndoTimer, refreshStats]
  );

  /**
   * Submit batch validation
   * Requirements: 2.3 - Update all selected items
   */
  const batchValidate = useCallback(
    async (
      resultIds: string[],
      action: BatchAction
    ): Promise<BatchValidationResult | null> => {
      if (resultIds.length === 0) return null;

      setIsBatchLoading(true);
      setError(null);

      try {
        const result = await api.validation.batch(resultIds, action);
        
        onBatchComplete?.(result);
        
        // Refresh stats after batch validation
        refreshStats();

        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Batch validation failed');
        setError(error);
        onValidationError?.(error);
        return null;
      } finally {
        setIsBatchLoading(false);
      }
    },
    [onBatchComplete, onValidationError, refreshStats]
  );

  /**
   * Undo the most recent validation
   * Requirements: 7.2 - Revert validation and restore previous state
   */
  const undoValidation = useCallback(async (): Promise<boolean> => {
    if (!recentValidation) return false;

    setIsLoading(true);
    setError(null);

    try {
      await api.validation.undo(recentValidation.id);
      
      // Clear the recent validation
      clearRecentValidation();
      
      onUndoSuccess?.();
      
      // Refresh stats after undo
      refreshStats();

      return true;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Undo failed');
      setError(error);
      onUndoError?.(error);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [recentValidation, clearRecentValidation, onUndoSuccess, onUndoError, refreshStats]);

  // Auto-fetch stats on mount if enabled
  useEffect(() => {
    if (autoFetchStats) {
      refreshStats();
    }
  }, [autoFetchStats, refreshStats]);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      clearUndoTimers();
    };
  }, [clearUndoTimers]);

  // Computed: can undo if we have a recent validation and time remaining
  const canUndo = recentValidation !== null && undoTimeRemaining > 0;

  // Toast props for easy integration with ValidationToast component
  // Requirements: 7.1, 7.2, 7.3 - Toast with undo functionality
  const toastProps = {
    validation: showToast ? recentValidation : null,
    undoTimeRemaining,
    canUndo,
    onUndo: undoValidation,
    onDismiss: clearRecentValidation,
    isUndoing: isLoading && recentValidation !== null,
  };

  return {
    submitValidation,
    batchValidate,
    undoValidation,
    validationStats,
    refreshStats,
    isLoading,
    isBatchLoading,
    recentValidation,
    canUndo,
    undoTimeRemaining,
    clearRecentValidation,
    error,
    toastProps,
  };
}

export default useValidation;
