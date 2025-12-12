'use client';

/**
 * Scan Results Page - Gambling Comment Detector
 * 
 * Displays detailed scan results with gambling vs clean comments,
 * confidence scores, and export functionality.
 * Requirements: 7.4, 8.1, 8.2
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { 
  MdArrowBack, 
  MdPlayCircle, 
  MdWarning,
  MdCheckCircle,
  MdDownload,
  MdClose,
  MdFilterList,
  MdSort,
  MdSearch
} from 'react-icons/md';

import Card from 'components/card';
import { ScanProgress } from 'components/scan';
import { 
  ValidationToggle, 
  KeyboardShortcutsHelp, 
  ValidationProgressBar,
  BatchValidationModal,
  ValidationToast,
} from 'components/validation';
import { api, getAccessToken } from 'lib/api';
import { useKeyboardNavigation, useValidationShortcuts, useValidation } from 'hooks';
import type { ScanDetailResponse, ScanResultResponse, ScanStatus, BatchAction } from 'lib/types';
import { isLowConfidenceResult } from 'utils/confidence';

type FilterType = 'all' | 'gambling' | 'clean' | 'low-confidence';
type SortType = 'confidence-desc' | 'confidence-asc' | 'author';

/**
 * Loading skeleton for scan details
 */
const ScanDetailSkeleton = () => (
  <div className="space-y-6">
    <Card extra="!p-6 animate-pulse">
      <div className="flex flex-col md:flex-row gap-6">
        <div className="w-full md:w-64 h-36 bg-gray-200 dark:bg-navy-700 rounded-xl" />
        <div className="flex-1 space-y-3">
          <div className="h-6 w-3/4 bg-gray-200 dark:bg-navy-700 rounded" />
          <div className="h-4 w-1/2 bg-gray-200 dark:bg-navy-700 rounded" />
          <div className="flex gap-4 mt-4">
            <div className="h-8 w-24 bg-gray-200 dark:bg-navy-700 rounded-lg" />
            <div className="h-8 w-24 bg-gray-200 dark:bg-navy-700 rounded-lg" />
          </div>
        </div>
      </div>
    </Card>
    <Card extra="!p-6 animate-pulse">
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-start gap-3 p-4 bg-gray-50 dark:bg-navy-800 rounded-lg">
            <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-navy-700" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-32 bg-gray-200 dark:bg-navy-700 rounded" />
              <div className="h-4 w-full bg-gray-200 dark:bg-navy-700 rounded" />
            </div>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

/**
 * Comment result card with confidence score
 * Requirements: 7.4 - Display all detected comments with confidence scores
 * Requirements: 8.2 - Keyboard navigation support with focus management
 */
const CommentResultCard = ({ 
  result,
  showConfidenceBar = true,
  isFocused = false,
  onValidate,
  isValidated,
  validationState,
  isCorrectionMode = false,
  isSelected = false,
  onSelect,
  batchMode = false,
  itemProps,
}: { 
  result: ScanResultResponse;
  showConfidenceBar?: boolean;
  isFocused?: boolean;
  onValidate?: (isCorrect: boolean, correctedLabel?: boolean) => void;
  isValidated?: boolean;
  validationState?: 'confirmed' | 'corrected';
  isCorrectionMode?: boolean;
  isSelected?: boolean;
  onSelect?: (selected: boolean) => void;
  batchMode?: boolean;
  itemProps?: {
    tabIndex: number;
    'data-focused': boolean;
    'aria-selected': boolean;
    ref: (el: HTMLElement | null) => void;
  };
}) => {
  const confidencePercent = Math.round(result.confidence * 100);
  const isLowConfidence = isLowConfidenceResult(result.confidence);
  
  return (
    <div 
      {...itemProps}
      className={`p-4 rounded-lg border-l-4 transition-all duration-150 outline-none ${
        result.is_gambling 
          ? 'border-red-500 bg-red-50 dark:bg-red-900/10' 
          : 'border-green-500 bg-green-50 dark:bg-green-900/10'
      } ${
        isFocused 
          ? 'ring-2 ring-brand-500 ring-offset-2 dark:ring-offset-navy-900 shadow-lg' 
          : ''
      } ${
        isLowConfidence && !isFocused
          ? 'border-l-amber-500 ring-1 ring-amber-200 dark:ring-amber-800'
          : ''
      } ${
        isSelected
          ? 'ring-2 ring-brand-400 bg-brand-50 dark:bg-brand-900/20'
          : ''
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Batch Mode Checkbox */}
        {batchMode && (
          <div className="flex-shrink-0 pt-1">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => onSelect?.(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 dark:border-navy-600 text-brand-500 focus:ring-brand-500 cursor-pointer"
              aria-label={`Select comment by ${result.author_name || 'Unknown'}`}
            />
          </div>
        )}

        {/* Author Avatar */}
        <div className="flex-shrink-0">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
            isFocused 
              ? 'bg-brand-100 dark:bg-brand-900/30' 
              : isLowConfidence
                ? 'bg-amber-100 dark:bg-amber-900/30'
                : 'bg-gray-200 dark:bg-navy-700'
          }`}>
            <span className={`text-sm font-bold ${
              isFocused 
                ? 'text-brand-600 dark:text-brand-400' 
                : isLowConfidence
                  ? 'text-amber-600 dark:text-amber-400'
                  : 'text-gray-500 dark:text-gray-400'
            }`}>
              {(result.author_name || 'U').charAt(0).toUpperCase()}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center flex-wrap gap-2 mb-2">
            <span className="font-semibold text-navy-700 dark:text-white text-sm">
              {result.author_name || 'Unknown Author'}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              result.is_gambling 
                ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' 
                : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
            }`}>
              {result.is_gambling ? 'Gambling' : 'Clean'}
            </span>
            {isLowConfidence && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                Low Confidence
              </span>
            )}
          </div>
          
          <p className="text-black dark:text-gray-300 text-sm whitespace-pre-wrap break-words mb-3">
            {result.comment_text}
          </p>

          {/* Confidence Score and Validation */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            {/* Confidence Score */}
            {showConfidenceBar && (
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <span className="text-xs text-gray-500 dark:text-gray-400 w-20 flex-shrink-0">
                  Confidence:
                </span>
                <div className="flex-1 max-w-xs">
                  <div className="h-2 bg-gray-200 dark:bg-navy-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-300 ${
                        result.is_gambling 
                          ? 'bg-red-500' 
                          : 'bg-green-500'
                      }`}
                      style={{ width: `${confidencePercent}%` }}
                    />
                  </div>
                </div>
                <span className={`text-xs font-semibold w-12 text-right flex-shrink-0 ${
                  result.is_gambling 
                    ? 'text-red-600 dark:text-red-400' 
                    : 'text-green-600 dark:text-green-400'
                }`}>
                  {confidencePercent}%
                </span>
              </div>
            )}

            {/* Validation Toggle */}
            {onValidate && (
              <div className="flex-shrink-0">
                <ValidationToggle
                  resultId={result.id}
                  isGambling={result.is_gambling}
                  confidence={result.confidence}
                  onValidate={onValidate}
                  isValidated={isValidated}
                  validationState={validationState}
                  compact
                />
              </div>
            )}
          </div>

          {/* Keyboard hint when focused and in correction mode */}
          {isFocused && isCorrectionMode && (
            <div className="mt-2 p-2 bg-amber-50 dark:bg-amber-900/20 rounded-md">
              <p className="text-xs text-amber-700 dark:text-amber-400">
                Press <kbd className="px-1 py-0.5 bg-amber-100 dark:bg-amber-900/40 rounded text-xs font-mono">G</kbd> for Gambling, 
                <kbd className="px-1 py-0.5 bg-amber-100 dark:bg-amber-900/40 rounded text-xs font-mono ml-1">C</kbd> for Clean, 
                or <kbd className="px-1 py-0.5 bg-amber-100 dark:bg-amber-900/40 rounded text-xs font-mono ml-1">Esc</kbd> to cancel
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ScanResultsPage = () => {
  const params = useParams();
  const router = useRouter();
  const scanId = params.scanId as string;

  const [scanDetail, setScanDetail] = useState<ScanDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterType>('all');
  const [sort, setSort] = useState<SortType>('confidence-desc');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  
  // Batch mode state
  const [batchMode, setBatchMode] = useState(false);
  const [selectedResults, setSelectedResults] = useState<Set<string>>(new Set());
  const [showBatchModal, setShowBatchModal] = useState(false);
  
  // Validation state tracking
  const [validatedResults, setValidatedResults] = useState<Map<string, { isValidated: boolean; state: 'confirmed' | 'corrected' }>>(new Map());
  
  const resultsContainerRef = useRef<HTMLDivElement>(null);

  // Validation hook for API integration
  const {
    submitValidation,
    batchValidate,
    validationStats,
    refreshStats,
    isLoading: isValidationLoading,
    isBatchLoading,
    toastProps,
  } = useValidation({
    autoFetchStats: true,
    onValidationSuccess: (validation) => {
      // Update local validation state
      setValidatedResults(prev => {
        const newMap = new Map(prev);
        newMap.set(validation.scan_result_id, {
          isValidated: true,
          state: validation.is_correction ? 'corrected' : 'confirmed',
        });
        return newMap;
      });
    },
    onBatchComplete: (result) => {
      // Update local validation state for all batch items
      setValidatedResults(prev => {
        const newMap = new Map(prev);
        result.validations.forEach(v => {
          newMap.set(v.scan_result_id, {
            isValidated: true,
            state: v.is_correction ? 'corrected' : 'confirmed',
          });
        });
        return newMap;
      });
      // Clear selection after batch
      setSelectedResults(new Set());
      setBatchMode(false);
    },
  });

  /**
   * Fetch scan details with results
   * Requirements: 7.4 - Display all detected comments with confidence scores
   */
  const fetchScanDetail = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.scan.get(scanId);
      setScanDetail(data);
      
      // Load existing validations for this scan
      try {
        const existingValidations = await api.validation.forScan(scanId);
        if (existingValidations && existingValidations.length > 0) {
          const validationMap = new Map<string, { isValidated: boolean; state: 'confirmed' | 'corrected' }>();
          existingValidations.forEach(v => {
            validationMap.set(v.scan_result_id, {
              isValidated: true,
              state: v.is_correction ? 'corrected' : 'confirmed',
            });
          });
          setValidatedResults(validationMap);
        }
      } catch (validationErr) {
        console.error('Failed to load existing validations:', validationErr);
        // Don't fail the whole page load if validations fail
      }
    } catch (err) {
      console.error('Failed to fetch scan details:', err);
      setError('Failed to load scan results. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [scanId]);

  useEffect(() => {
    fetchScanDetail();
  }, [fetchScanDetail]);

  /**
   * Handle scan completion from progress component
   */
  const handleScanComplete = useCallback(() => {
    fetchScanDetail();
  }, [fetchScanDetail]);

  /**
   * Export scan results
   * Requirements: 8.1, 8.2 - CSV and JSON export
   */
  const handleExport = async (format: 'csv' | 'json') => {
    if (!scanDetail) return;
    
    const token = getAccessToken();
    const baseUrl = typeof window !== 'undefined' 
      ? (window as unknown as { ENV?: { NEXT_PUBLIC_API_URL?: string } }).ENV?.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      : 'http://localhost:8000';
    
    const url = `${baseUrl}/api/dashboard/export/${scanDetail.id}?format=${format}`;
    
    // Open in new tab with auth header via fetch and blob
    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `scan-${scanDetail.id}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Export failed:', err);
      setError('Failed to export results. Please try again.');
    }
  };

  /**
   * Filter results based on confidence threshold
   * Requirements: 3.2 - Filter comments with confidence < 70%
   * **Feature: auto-ml-retraining, Property 3: Filter Correctness**
   */
  const filterByConfidence = useCallback((results: ScanResultResponse[], filterType: FilterType): ScanResultResponse[] => {
    if (filterType === 'low-confidence') {
      return results.filter(r => isLowConfidenceResult(r.confidence));
    }
    return results;
  }, []);

  /**
   * Filter and sort results
   */
  const getFilteredResults = useCallback((): ScanResultResponse[] => {
    if (!scanDetail) return [];
    
    let results = [...scanDetail.results];
    
    // Apply type filter
    if (filter === 'gambling') {
      results = results.filter(r => r.is_gambling);
    } else if (filter === 'clean') {
      results = results.filter(r => !r.is_gambling);
    } else if (filter === 'low-confidence') {
      // Requirements: 3.2 - Low confidence filter
      results = filterByConfidence(results, filter);
    }
    
    // Apply search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      results = results.filter(r => 
        r.comment_text.toLowerCase().includes(query) ||
        (r.author_name?.toLowerCase().includes(query) ?? false)
      );
    }
    
    // Apply sort
    switch (sort) {
      case 'confidence-desc':
        results.sort((a, b) => b.confidence - a.confidence);
        break;
      case 'confidence-asc':
        results.sort((a, b) => a.confidence - b.confidence);
        break;
      case 'author':
        results.sort((a, b) => (a.author_name || '').localeCompare(b.author_name || ''));
        break;
    }
    
    return results;
  }, [scanDetail, filter, sort, searchQuery, filterByConfidence]);

  const filteredResults = getFilteredResults();

  /**
   * Handle validation for a result
   * Requirements: 1.2 - Mark prediction as confirmed/corrected
   */
  const handleValidation = useCallback(async (resultId: string, isCorrect: boolean, correctedLabel?: boolean) => {
    // Optimistic update
    setValidatedResults(prev => {
      const newMap = new Map(prev);
      newMap.set(resultId, {
        isValidated: true,
        state: isCorrect ? 'confirmed' : 'corrected',
      });
      return newMap;
    });
    
    // Call API to persist validation
    await submitValidation(resultId, isCorrect, correctedLabel);
  }, [submitValidation]);

  /**
   * Handle batch validation
   * Requirements: 2.2, 2.3 - Batch validation with bulk actions
   */
  const handleBatchValidation = useCallback(async (action: BatchAction) => {
    const resultIds = Array.from(selectedResults);
    await batchValidate(resultIds, action);
    setShowBatchModal(false);
  }, [selectedResults, batchValidate]);

  /**
   * Toggle result selection for batch mode
   */
  const handleResultSelect = useCallback((resultId: string, selected: boolean) => {
    setSelectedResults(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(resultId);
      } else {
        newSet.delete(resultId);
      }
      return newSet;
    });
  }, []);

  /**
   * Select all visible results
   */
  const handleSelectAll = useCallback(() => {
    const allIds = new Set(filteredResults.map(r => r.id));
    setSelectedResults(allIds);
  }, [filteredResults]);

  /**
   * Deselect all results
   */
  const handleDeselectAll = useCallback(() => {
    setSelectedResults(new Set());
  }, []);

  /**
   * Keyboard navigation hook
   * Requirements: 8.2 - Arrow key navigation between comments
   */
  const {
    focusedIndex,
    getItemProps,
    isFocused,
  } = useKeyboardNavigation({
    itemCount: filteredResults.length,
    enabled: !isLoading && filteredResults.length > 0,
  });

  /**
   * Validation keyboard shortcuts
   * Requirements: 8.1 - Keyboard shortcuts for quick validation
   */
  const { isCorrectionMode } = useValidationShortcuts({
    enabled: !isLoading && filteredResults.length > 0,
    focusedIndex,
    onValidateCorrect: (index) => {
      const result = filteredResults[index];
      if (result) {
        handleValidation(result.id, true);
      }
    },
    onMarkIncorrect: (index) => {
      // Just enters correction mode, actual correction handled by G/C keys
    },
    onCorrectToGambling: (index) => {
      const result = filteredResults[index];
      if (result) {
        handleValidation(result.id, false, true);
      }
    },
    onCorrectToClean: (index) => {
      const result = filteredResults[index];
      if (result) {
        handleValidation(result.id, false, false);
      }
    },
    onShowHelp: () => {
      // KeyboardShortcutsHelp component handles its own state
    },
  });

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Show progress if scan is still running
  if (scanDetail && (scanDetail.status === 'pending' || scanDetail.status === 'processing')) {
    return (
      <div className="mt-3">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-navy-700 dark:hover:text-white mb-4 transition-colors"
        >
          <MdArrowBack className="h-5 w-5" />
          Back
        </button>

        <Card extra="!p-6">
          <h1 className="text-xl font-bold text-navy-700 dark:text-white mb-4">
            Scan in Progress
          </h1>
          <ScanProgress 
            scanId={scanId}
            initialStatus={scanDetail.status as ScanStatus}
            onComplete={handleScanComplete}
            onFailed={(_, errorMsg) => setError(errorMsg || 'Scan failed')}
          />
        </Card>
      </div>
    );
  }

  return (
    <div className="mt-3">
      {/* Back Button */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-navy-700 dark:hover:text-white mb-4 transition-colors"
      >
        <MdArrowBack className="h-5 w-5" />
        Back
      </button>

      {/* Error Alert */}
      {error && (
        <Card extra="!p-4 mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
              <MdWarning className="h-5 w-5" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
              <MdClose className="h-5 w-5" />
            </button>
          </div>
        </Card>
      )}

      {isLoading ? (
        <ScanDetailSkeleton />
      ) : scanDetail ? (
        <div className="space-y-6">
          {/* Scan Overview Card */}
          <Card extra="!p-6">
            <div className="flex flex-col md:flex-row gap-6">
              {/* Video Thumbnail */}
              {scanDetail.video_thumbnail && (
                <div className="relative w-full md:w-64 h-36 rounded-xl overflow-hidden flex-shrink-0">
                  <Image
                    src={scanDetail.video_thumbnail}
                    alt={scanDetail.video_title || 'Video thumbnail'}
                    fill
                    className="object-cover"
                    sizes="(max-width: 768px) 100vw, 256px"
                  />
                  <Link 
                    href={`https://youtube.com/watch?v=${scanDetail.video_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 hover:opacity-100 transition-opacity"
                  >
                    <MdPlayCircle className="h-12 w-12 text-white" />
                  </Link>
                </div>
              )}

              {/* Scan Info */}
              <div className="flex-1">
                <h1 className="text-xl font-bold text-navy-700 dark:text-white mb-1">
                  {scanDetail.video_title || 'Untitled Video'}
                </h1>
                {scanDetail.channel_name && (
                  <p className="text-gray-600 dark:text-gray-400 mb-3">
                    {scanDetail.channel_name}
                  </p>
                )}
                
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                  Scanned on {formatDate(scanDetail.scanned_at)}
                </p>

                {/* Stats Summary */}
                <div className="flex flex-wrap gap-3 mb-4">
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-navy-700 rounded-lg">
                    <span className="text-sm text-gray-600 dark:text-gray-300">
                      Total: <span className="font-semibold">{scanDetail.total_comments}</span>
                    </span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-red-100 dark:bg-red-900/30 rounded-lg">
                    <MdWarning className="h-4 w-4 text-red-500" />
                    <span className="text-sm text-red-700 dark:text-red-400">
                      Gambling: <span className="font-semibold">{scanDetail.gambling_count}</span>
                    </span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-green-100 dark:bg-green-900/30 rounded-lg">
                    <MdCheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm text-green-700 dark:text-green-400">
                      Clean: <span className="font-semibold">{scanDetail.clean_count}</span>
                    </span>
                  </div>
                </div>

                {/* Export Buttons */}
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => handleExport('csv')}
                    className="flex items-center gap-2 px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors"
                  >
                    <MdDownload className="h-5 w-5" />
                    Export CSV
                  </button>
                  <button
                    onClick={() => handleExport('json')}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-navy-700 text-navy-700 dark:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-navy-600 transition-colors"
                  >
                    <MdDownload className="h-5 w-5" />
                    Export JSON
                  </button>
                </div>
              </div>
            </div>
          </Card>

          {/* Validation Progress Bar */}
          {scanDetail && (
            <ValidationProgressBar
              totalComments={scanDetail.total_comments}
              validatedCount={validatedResults.size}
              correctionsCount={Array.from(validatedResults.values()).filter(v => v.state === 'corrected').length}
              thresholdProgress={validationStats?.progress_percent ?? 0}
              threshold={validationStats?.threshold ?? 100}
            />
          )}

          {/* Results Card */}
          <Card extra="!p-6">
            {/* Header with Filters */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-bold text-navy-700 dark:text-white">
                  Scan Results ({filteredResults.length})
                </h2>
                {/* Keyboard navigation hint */}
                {focusedIndex >= 0 && (
                  <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-navy-700 px-2 py-1 rounded">
                    {focusedIndex + 1} of {filteredResults.length}
                  </span>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                {/* Batch Mode Toggle */}
                <button
                  onClick={() => {
                    setBatchMode(!batchMode);
                    if (batchMode) {
                      setSelectedResults(new Set());
                    }
                  }}
                  className={`px-3 py-2 text-sm rounded-lg transition-colors flex items-center gap-1.5 ${
                    batchMode 
                      ? 'bg-brand-500 text-white' 
                      : 'bg-gray-100 dark:bg-navy-700 text-black dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-navy-600'
                  }`}
                >
                  <MdCheckCircle className="h-4 w-4" />
                  {batchMode ? 'Exit Batch' : 'Batch Mode'}
                </button>

                {/* Search */}
                <div className="relative">
                  <MdSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search comments..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 pr-4 py-2 text-sm border border-gray-200 dark:border-navy-600 rounded-lg bg-white dark:bg-navy-800 text-navy-700 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                
                {/* Filter Toggle */}
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={`p-2 rounded-lg transition-colors ${
                    showFilters 
                      ? 'bg-brand-500 text-white' 
                      : 'bg-gray-100 dark:bg-navy-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-navy-600'
                  }`}
                >
                  <MdFilterList className="h-5 w-5" />
                </button>

                {/* Keyboard Shortcuts Help */}
                <KeyboardShortcutsHelp compact />
              </div>
            </div>

            {/* Batch Mode Controls */}
            {batchMode && (
              <div className="flex items-center justify-between gap-4 mb-4 p-3 bg-brand-50 dark:bg-brand-900/20 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-brand-700 dark:text-brand-300">
                    {selectedResults.size} selected
                  </span>
                  <button
                    onClick={handleSelectAll}
                    className="text-xs text-brand-600 dark:text-brand-400 hover:underline"
                  >
                    Select All
                  </button>
                  <button
                    onClick={handleDeselectAll}
                    className="text-xs text-brand-600 dark:text-brand-400 hover:underline"
                  >
                    Deselect All
                  </button>
                </div>
                <button
                  onClick={() => setShowBatchModal(true)}
                  disabled={selectedResults.size === 0}
                  className="px-4 py-2 text-sm font-medium bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Validate Selected ({selectedResults.size})
                </button>
              </div>
            )}

            {/* Filter Options */}
            {showFilters && (
              <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 dark:bg-navy-800 rounded-lg">
                {/* Filter by Type */}
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                    Filter by
                  </label>
                  <div className="flex gap-1 flex-wrap">
                    {(['all', 'gambling', 'clean', 'low-confidence'] as FilterType[]).map((f) => (
                      <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                          filter === f
                            ? f === 'low-confidence' 
                              ? 'bg-amber-500 text-white'
                              : 'bg-brand-500 text-white'
                            : 'bg-white dark:bg-navy-700 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-navy-600'
                        }`}
                      >
                        {f === 'low-confidence' ? 'Low Confidence' : f.charAt(0).toUpperCase() + f.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Sort by */}
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                    Sort by
                  </label>
                  <div className="flex items-center gap-1">
                    <MdSort className="h-4 w-4 text-gray-400" />
                    <select
                      value={sort}
                      onChange={(e) => setSort(e.target.value as SortType)}
                      className="px-3 py-1.5 text-sm border border-gray-200 dark:border-navy-600 rounded-lg bg-white dark:bg-navy-700 text-navy-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="confidence-desc">Confidence (High to Low)</option>
                      <option value="confidence-asc">Confidence (Low to High)</option>
                      <option value="author">Author Name</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Results List */}
            {filteredResults.length === 0 ? (
              <div className="text-center py-12">
                <MdSearch className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400">
                  {searchQuery || filter !== 'all' 
                    ? 'No comments match your filters' 
                    : 'No comments found in this scan'}
                </p>
              </div>
            ) : (
              <div 
                ref={resultsContainerRef}
                className="space-y-3 max-h-[600px] overflow-y-auto"
                role="listbox"
                aria-label="Scan results"
                aria-activedescendant={focusedIndex >= 0 ? `result-${filteredResults[focusedIndex]?.id}` : undefined}
              >
                {filteredResults.map((result, index) => {
                  const validation = validatedResults.get(result.id);
                  return (
                    <CommentResultCard 
                      key={result.id} 
                      result={result}
                      isFocused={isFocused(index)}
                      onValidate={(isCorrect, correctedLabel) => handleValidation(result.id, isCorrect, correctedLabel)}
                      isValidated={validation?.isValidated}
                      validationState={validation?.state}
                      isCorrectionMode={isFocused(index) && isCorrectionMode}
                      batchMode={batchMode}
                      isSelected={selectedResults.has(result.id)}
                      onSelect={(selected) => handleResultSelect(result.id, selected)}
                      itemProps={{
                        ...getItemProps(index),
                        id: `result-${result.id}`,
                      } as any}
                    />
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      ) : (
        <Card extra="!p-6">
          <div className="text-center py-12">
            <MdWarning className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">Scan not found</p>
            <button
              onClick={() => router.push('/admin/my-videos')}
              className="mt-4 px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors"
            >
              Go to My Videos
            </button>
          </div>
        </Card>
      )}

      {/* Batch Validation Modal */}
      <BatchValidationModal
        selectedResults={filteredResults.filter(r => selectedResults.has(r.id))}
        onConfirm={handleBatchValidation}
        onClose={() => setShowBatchModal(false)}
        isOpen={showBatchModal}
      />

      {/* Validation Toast with Undo */}
      <ValidationToast {...toastProps} />
    </div>
  );
};

export default ScanResultsPage;
