'use client';

/**
 * ValidationToggle Component - Auto ML Retraining
 * 
 * Provides inline validation controls for scan results.
 * Users can confirm predictions as correct or mark them as incorrect.
 * 
 * Requirements: 1.1, 1.2, 1.3
 */

import { useState, useCallback } from 'react';
import { MdCheck, MdClose, MdEdit, MdUndo } from 'react-icons/md';

export interface ValidationToggleProps {
  /** Unique ID of the scan result */
  resultId: string;
  /** Whether the model predicted this as gambling */
  isGambling: boolean;
  /** Model's confidence score (0-1) */
  confidence: number;
  /** Callback when user validates */
  onValidate: (isCorrect: boolean, correctedLabel?: boolean) => void;
  /** Whether this result has been validated */
  isValidated?: boolean;
  /** Current validation state */
  validationState?: 'confirmed' | 'corrected';
  /** Whether validation is in progress */
  isLoading?: boolean;
  /** Whether to show compact version */
  compact?: boolean;
}

type ValidationMode = 'idle' | 'confirming' | 'correcting';

/**
 * ValidationToggle - Inline validation control for scan results
 * 
 * Displays subtle validation controls that allow users to:
 * - Confirm a prediction as correct
 * - Mark a prediction as incorrect and provide the correct label
 * 
 * @example
 * ```tsx
 * <ValidationToggle
 *   resultId="abc123"
 *   isGambling={true}
 *   confidence={0.85}
 *   onValidate={(isCorrect, correctedLabel) => handleValidation(isCorrect, correctedLabel)}
 * />
 * ```
 */
const ValidationToggle = ({
  resultId,
  isGambling,
  confidence,
  onValidate,
  isValidated = false,
  validationState,
  isLoading = false,
  compact = false,
}: ValidationToggleProps) => {
  const [mode, setMode] = useState<ValidationMode>('idle');

  /**
   * Handle confirm correct action
   * Requirements: 1.2 - Mark prediction as "confirmed correct"
   */
  const handleConfirmCorrect = useCallback(() => {
    onValidate(true);
    setMode('idle');
  }, [onValidate]);

  /**
   * Handle mark incorrect action - show correction options
   * Requirements: 1.3 - Display quick correction option
   */
  const handleMarkIncorrect = useCallback(() => {
    setMode('correcting');
  }, []);

  /**
   * Handle correction submission
   * Requirements: 1.3 - Quick correction option (gambling ↔ clean)
   */
  const handleCorrection = useCallback((correctedLabel: boolean) => {
    onValidate(false, correctedLabel);
    setMode('idle');
  }, [onValidate]);

  /**
   * Cancel correction mode
   */
  const handleCancel = useCallback(() => {
    setMode('idle');
  }, []);

  // Already validated - show status
  if (isValidated && validationState) {
    return (
      <div className={`inline-flex items-center gap-1.5 ${compact ? 'text-xs' : 'text-sm'}`}>
        {validationState === 'confirmed' ? (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
            <MdCheck className="h-3.5 w-3.5" />
            <span>Confirmed</span>
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">
            <MdEdit className="h-3.5 w-3.5" />
            <span>Corrected</span>
          </span>
        )}
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className={`inline-flex items-center gap-2 ${compact ? 'text-xs' : 'text-sm'}`}>
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
        <span className="text-gray-500 dark:text-gray-400">Saving...</span>
      </div>
    );
  }

  // Correction mode - show label options
  if (mode === 'correcting') {
    return (
      <div className={`inline-flex items-center gap-2 ${compact ? 'text-xs' : 'text-sm'}`}>
        <span className="text-gray-500 dark:text-gray-400">Correct to:</span>
        <button
          onClick={() => handleCorrection(true)}
          className="px-2 py-1 rounded-md bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
          title="Mark as Gambling"
        >
          Gambling
        </button>
        <button
          onClick={() => handleCorrection(false)}
          className="px-2 py-1 rounded-md bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors"
          title="Mark as Clean"
        >
          Clean
        </button>
        <button
          onClick={handleCancel}
          className="p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-navy-600 transition-colors"
          title="Cancel"
        >
          <MdClose className="h-4 w-4" />
        </button>
      </div>
    );
  }

  // Default idle mode - show validation buttons
  return (
    <div className={`inline-flex items-center gap-1 ${compact ? 'text-xs' : 'text-sm'}`}>
      <button
        onClick={handleConfirmCorrect}
        className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-gray-500 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
        title="Confirm prediction is correct"
      >
        <MdCheck className="h-4 w-4" />
        {!compact && <span>Correct</span>}
      </button>
      <button
        onClick={handleMarkIncorrect}
        className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
        title="Mark prediction as incorrect"
      >
        <MdClose className="h-4 w-4" />
        {!compact && <span>Wrong</span>}
      </button>
    </div>
  );
};

export default ValidationToggle;
