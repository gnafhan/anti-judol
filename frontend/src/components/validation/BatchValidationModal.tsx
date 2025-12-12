'use client';

/**
 * BatchValidationModal Component - Auto ML Retraining
 * 
 * Modal for bulk validation of multiple scan results.
 * Allows users to confirm all, mark all as gambling, or mark all as clean.
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4
 */

import { useState, useCallback } from 'react';
import { 
  MdClose, 
  MdCheckCircle, 
  MdWarning, 
  MdCleaningServices,
  MdCasino
} from 'react-icons/md';
import type { ScanResultResponse } from 'lib/types';

export type BatchAction = 'confirm_all' | 'mark_gambling' | 'mark_clean';

export interface BatchValidationModalProps {
  /** Selected scan results to validate */
  selectedResults: ScanResultResponse[];
  /** Callback when batch action is confirmed */
  onConfirm: (action: BatchAction) => Promise<void>;
  /** Callback to close modal */
  onClose: () => void;
  /** Whether modal is open */
  isOpen: boolean;
}

interface BatchProgress {
  total: number;
  completed: number;
  status: 'idle' | 'processing' | 'completed' | 'error';
  error?: string;
}

/**
 * BatchValidationModal - Bulk validation modal for scan results
 * 
 * Provides options to:
 * - Confirm all selected predictions as correct
 * - Mark all selected as gambling
 * - Mark all selected as clean
 * 
 * Shows progress indicator during batch operations.
 * 
 * @example
 * ```tsx
 * <BatchValidationModal
 *   selectedResults={selectedItems}
 *   onConfirm={handleBatchValidation}
 *   onClose={() => setModalOpen(false)}
 *   isOpen={isModalOpen}
 * />
 * ```
 */
const BatchValidationModal = ({
  selectedResults,
  onConfirm,
  onClose,
  isOpen,
}: BatchValidationModalProps) => {
  const [progress, setProgress] = useState<BatchProgress>({
    total: 0,
    completed: 0,
    status: 'idle',
  });

  /**
   * Handle batch action selection
   * Requirements: 2.2 - Display modal with bulk action options
   */
  const handleAction = useCallback(async (action: BatchAction) => {
    setProgress({
      total: selectedResults.length,
      completed: 0,
      status: 'processing',
    });

    try {
      await onConfirm(action);
      setProgress(prev => ({
        ...prev,
        completed: prev.total,
        status: 'completed',
      }));
      
      // Auto-close after success
      setTimeout(() => {
        onClose();
        setProgress({ total: 0, completed: 0, status: 'idle' });
      }, 1500);
    } catch (error) {
      setProgress(prev => ({
        ...prev,
        status: 'error',
        error: error instanceof Error ? error.message : 'Batch validation failed',
      }));
    }
  }, [selectedResults.length, onConfirm, onClose]);

  /**
   * Handle modal close
   */
  const handleClose = useCallback(() => {
    if (progress.status !== 'processing') {
      setProgress({ total: 0, completed: 0, status: 'idle' });
      onClose();
    }
  }, [progress.status, onClose]);

  if (!isOpen) return null;

  const gamblingCount = selectedResults.filter(r => r.is_gambling).length;
  const cleanCount = selectedResults.length - gamblingCount;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-md mx-4 bg-white dark:bg-navy-800 rounded-2xl shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-navy-600">
          <h3 className="text-lg font-semibold text-navy-700 dark:text-white">
            Batch Validation
          </h3>
          <button
            onClick={handleClose}
            disabled={progress.status === 'processing'}
            className="p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-navy-600 transition-colors disabled:opacity-50"
          >
            <MdClose className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Selection Summary */}
          <div className="mb-4 p-3 bg-gray-50 dark:bg-navy-700 rounded-xl">
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
              <span className="font-semibold">{selectedResults.length}</span> comments selected
            </p>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1 text-red-500">
                <MdCasino className="h-4 w-4" />
                {gamblingCount} gambling
              </span>
              <span className="flex items-center gap-1 text-green-500">
                <MdCleaningServices className="h-4 w-4" />
                {cleanCount} clean
              </span>
            </div>
          </div>

          {/* Progress Indicator */}
          {progress.status === 'processing' && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  Processing...
                </span>
                <span className="text-sm font-medium text-brand-500">
                  {Math.round((progress.completed / progress.total) * 100)}%
                </span>
              </div>
              <div className="h-2 bg-gray-200 dark:bg-navy-600 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-brand-500 rounded-full transition-all duration-300"
                  style={{ width: `${(progress.completed / progress.total) * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Success Message */}
          {progress.status === 'completed' && (
            <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-xl flex items-center gap-2">
              <MdCheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-sm text-green-600 dark:text-green-400">
                Successfully validated {progress.total} comments!
              </span>
            </div>
          )}

          {/* Error Message */}
          {progress.status === 'error' && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-xl flex items-center gap-2">
              <MdWarning className="h-5 w-5 text-red-500" />
              <span className="text-sm text-red-600 dark:text-red-400">
                {progress.error}
              </span>
            </div>
          )}

          {/* Action Buttons */}
          {progress.status === 'idle' && (
            <div className="space-y-2">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                Choose an action for all selected comments:
              </p>
              
              {/* Confirm All Correct */}
              <button
                onClick={() => handleAction('confirm_all')}
                className="w-full flex items-center gap-3 p-3 rounded-xl bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
              >
                <MdCheckCircle className="h-5 w-5" />
                <div className="text-left">
                  <p className="font-medium">Confirm All Correct</p>
                  <p className="text-xs opacity-75">Mark all predictions as accurate</p>
                </div>
              </button>

              {/* Mark All as Gambling */}
              <button
                onClick={() => handleAction('mark_gambling')}
                className="w-full flex items-center gap-3 p-3 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
              >
                <MdCasino className="h-5 w-5" />
                <div className="text-left">
                  <p className="font-medium">Mark All as Gambling</p>
                  <p className="text-xs opacity-75">Override all to gambling label</p>
                </div>
              </button>

              {/* Mark All as Clean */}
              <button
                onClick={() => handleAction('mark_clean')}
                className="w-full flex items-center gap-3 p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
              >
                <MdCleaningServices className="h-5 w-5" />
                <div className="text-left">
                  <p className="font-medium">Mark All as Clean</p>
                  <p className="text-xs opacity-75">Override all to clean label</p>
                </div>
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t border-gray-200 dark:border-navy-600">
          <button
            onClick={handleClose}
            disabled={progress.status === 'processing'}
            className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-navy-600 rounded-lg transition-colors disabled:opacity-50"
          >
            {progress.status === 'completed' ? 'Close' : 'Cancel'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BatchValidationModal;
