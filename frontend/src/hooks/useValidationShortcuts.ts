'use client';

/**
 * useValidationShortcuts Hook - Auto ML Retraining
 * 
 * Provides keyboard shortcuts for validation actions.
 * V for validate correct, X for mark incorrect, Enter to confirm.
 * 
 * Requirements: 8.1 - Keyboard shortcuts for quick validation
 */

import { useEffect, useCallback, useState } from 'react';

export interface UseValidationShortcutsOptions {
  /** Whether shortcuts are enabled */
  enabled?: boolean;
  /** Currently focused item index */
  focusedIndex: number;
  /** Callback when V is pressed (validate correct) */
  onValidateCorrect?: (index: number) => void;
  /** Callback when X is pressed (mark incorrect) */
  onMarkIncorrect?: (index: number) => void;
  /** Callback when Enter is pressed (confirm) */
  onConfirm?: (index: number) => void;
  /** Callback when G is pressed (correct to gambling) */
  onCorrectToGambling?: (index: number) => void;
  /** Callback when C is pressed (correct to clean) */
  onCorrectToClean?: (index: number) => void;
  /** Callback when ? is pressed (show help) */
  onShowHelp?: () => void;
}

export interface UseValidationShortcutsReturn {
  /** Whether correction mode is active */
  isCorrectionMode: boolean;
  /** Enter correction mode */
  enterCorrectionMode: () => void;
  /** Exit correction mode */
  exitCorrectionMode: () => void;
}

/**
 * Custom hook for validation keyboard shortcuts
 * 
 * @example
 * ```tsx
 * const { isCorrectionMode } = useValidationShortcuts({
 *   focusedIndex,
 *   onValidateCorrect: (index) => handleValidate(index, true),
 *   onMarkIncorrect: (index) => handleValidate(index, false),
 * });
 * ```
 */
export function useValidationShortcuts({
  enabled = true,
  focusedIndex,
  onValidateCorrect,
  onMarkIncorrect,
  onConfirm,
  onCorrectToGambling,
  onCorrectToClean,
  onShowHelp,
}: UseValidationShortcutsOptions): UseValidationShortcutsReturn {
  const [isCorrectionMode, setIsCorrectionMode] = useState(false);

  const enterCorrectionMode = useCallback(() => {
    setIsCorrectionMode(true);
  }, []);

  const exitCorrectionMode = useCallback(() => {
    setIsCorrectionMode(false);
  }, []);

  // Reset correction mode when focus changes
  useEffect(() => {
    setIsCorrectionMode(false);
  }, [focusedIndex]);

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't handle if user is typing in an input
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // Only handle validation shortcuts if an item is focused
      if (focusedIndex < 0) {
        // Still allow ? for help
        if (event.key === '?') {
          event.preventDefault();
          onShowHelp?.();
        }
        return;
      }

      const key = event.key.toLowerCase();

      // In correction mode, handle G and C
      if (isCorrectionMode) {
        switch (key) {
          case 'g':
            event.preventDefault();
            onCorrectToGambling?.(focusedIndex);
            setIsCorrectionMode(false);
            break;
          case 'c':
            event.preventDefault();
            onCorrectToClean?.(focusedIndex);
            setIsCorrectionMode(false);
            break;
          case 'escape':
            event.preventDefault();
            setIsCorrectionMode(false);
            break;
        }
        return;
      }

      // Normal mode shortcuts
      switch (key) {
        case 'v':
          event.preventDefault();
          onValidateCorrect?.(focusedIndex);
          break;
        case 'x':
          event.preventDefault();
          onMarkIncorrect?.(focusedIndex);
          setIsCorrectionMode(true);
          break;
        case 'enter':
          event.preventDefault();
          onConfirm?.(focusedIndex);
          break;
        case '?':
          event.preventDefault();
          onShowHelp?.();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    enabled,
    focusedIndex,
    isCorrectionMode,
    onValidateCorrect,
    onMarkIncorrect,
    onConfirm,
    onCorrectToGambling,
    onCorrectToClean,
    onShowHelp,
  ]);

  return {
    isCorrectionMode,
    enterCorrectionMode,
    exitCorrectionMode,
  };
}

export default useValidationShortcuts;
