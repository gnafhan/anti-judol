'use client';

/**
 * Model Management Page
 * 
 * Displays ML model metrics, version history, training progress,
 * and allows manual retraining and rollback operations.
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  MdRefresh,
  MdHistory,
  MdTrendingUp,
  MdTrendingDown,
  MdCheckCircle,
  MdWarning,
  MdPlayArrow,
  MdUndo,
  MdInfo,
} from 'react-icons/md';

import Card from 'components/card';
import LineChart from 'components/charts/LineChart';
import { api } from 'lib/api';
import type {
  ModelVersionFull,
  ModelMetricsAdmin,
  MetricsTrendResponse,
  RetrainingProgressResponse,
} from 'lib/types';

/**
 * Format percentage with sign
 */
const formatPercent = (value: number | null | undefined, showSign = true): string => {
  if (value === null || value === undefined) return 'N/A';
  const formatted = (value * 100).toFixed(2);
  if (showSign && value > 0) return `+${formatted}%`;
  return `${formatted}%`;
};

/**
 * Format date string
 */
const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('id-ID', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Metric Card Component
 */
const MetricCard = ({
  title,
  value,
  subtitle,
  trend,
  icon: Icon,
  color = 'brand',
}: {
  title: string;
  value: string;
  subtitle?: string;
  trend?: number | null;
  icon: React.ElementType;
  color?: 'brand' | 'green' | 'amber' | 'red';
}) => {
  const colorClasses = {
    brand: 'bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
    amber: 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
    red: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
  };

  return (
    <Card extra="!p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-navy-700 dark:text-white mt-1">
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
              {subtitle}
            </p>
          )}
          {trend !== null && trend !== undefined && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${
              trend >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            }`}>
              {trend >= 0 ? <MdTrendingUp /> : <MdTrendingDown />}
              <span>{formatPercent(trend / 100, true)}</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-xl ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </Card>
  );
};


/**
 * Training Progress Component
 */
const TrainingProgress = ({
  progress,
  onRefresh,
}: {
  progress: RetrainingProgressResponse | null;
  onRefresh: () => void;
}) => {
  if (!progress?.is_training) return null;

  return (
    <Card extra="!p-4 bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-brand-500 rounded-full animate-pulse" />
          <span className="font-semibold text-brand-700 dark:text-brand-300">
            Training in Progress
          </span>
        </div>
        <button
          onClick={onRefresh}
          className="p-1 text-brand-600 dark:text-brand-400 hover:bg-brand-100 dark:hover:bg-brand-900/40 rounded"
        >
          <MdRefresh className="h-5 w-5" />
        </button>
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            {progress.current_step || 'Processing...'}
          </span>
          <span className="font-medium text-brand-600 dark:text-brand-400">
            {progress.progress_percent.toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-brand-100 dark:bg-brand-900/40 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all duration-500"
            style={{ width: `${progress.progress_percent}%` }}
          />
        </div>
        {progress.started_at && (
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Started: {formatDate(progress.started_at)}
          </p>
        )}
      </div>
    </Card>
  );
};

/**
 * Version History Table
 */
const VersionHistoryTable = ({
  versions,
  onRollback,
  isRollingBack,
}: {
  versions: ModelVersionFull[];
  onRollback: (versionId: string) => void;
  isRollingBack: boolean;
}) => {
  return (
    <Card extra="!p-0 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-navy-600">
        <h3 className="text-lg font-bold text-navy-700 dark:text-white flex items-center gap-2">
          <MdHistory className="h-5 w-5" />
          Version History
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-navy-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                Version
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                Accuracy
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                F1 Score
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                Samples
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                Created
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-navy-600">
            {versions.map((version) => (
              <tr key={version.id} className="hover:bg-gray-50 dark:hover:bg-navy-800">
                <td className="px-4 py-3">
                  <span className="font-medium text-navy-700 dark:text-white">
                    {version.version}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                  {version.accuracy !== null ? `${(version.accuracy * 100).toFixed(2)}%` : 'N/A'}
                </td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                  {version.f1_score !== null ? `${(version.f1_score * 100).toFixed(2)}%` : 'N/A'}
                </td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                  {version.training_samples.toLocaleString()}
                  {version.validation_samples > 0 && (
                    <span className="text-xs text-gray-400 ml-1">
                      (+{version.validation_samples})
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  {formatDate(version.created_at)}
                </td>
                <td className="px-4 py-3">
                  {version.is_active ? (
                    <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                      <MdCheckCircle className="h-3 w-3" />
                      Active
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-navy-700 dark:text-gray-400">
                      Inactive
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {!version.is_active && (
                    <button
                      onClick={() => onRollback(version.id)}
                      disabled={isRollingBack}
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg transition-colors disabled:opacity-50"
                    >
                      <MdUndo className="h-4 w-4" />
                      Rollback
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};


/**
 * Retraining Confirmation Modal
 */
const RetrainingConfirmModal = ({
  isOpen,
  onClose,
  onConfirm,
  isLoading,
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}) => {
  const [preview, setPreview] = useState<{
    original_dataset_samples: number;
    total_validations: number;
    pending_validations: number;
    total_samples_after_training: number;
    corrections_count: number;
    confirmations_count: number;
    current_model_version: string | null;
    current_model_accuracy: number | null;
    can_retrain: boolean;
    message: string | null;
  } | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  // Fetch preview when modal opens
  useEffect(() => {
    if (isOpen) {
      setPreviewLoading(true);
      setPreviewError(null);
      api.model.retrainPreview()
        .then(setPreview)
        .catch((err) => {
          console.error('Failed to fetch preview:', err);
          setPreviewError('Gagal memuat preview data.');
        })
        .finally(() => setPreviewLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50" 
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-white dark:bg-navy-800 rounded-xl shadow-xl max-w-lg w-full mx-4 p-6">
        <h3 className="text-xl font-bold text-navy-700 dark:text-white mb-4">
          Konfirmasi Retraining Model
        </h3>
        
        {previewLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : previewError ? (
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 mb-4">
            <p className="text-red-700 dark:text-red-300">{previewError}</p>
          </div>
        ) : preview && (
          <div className="space-y-4 mb-6">
            <p className="text-gray-600 dark:text-gray-300">
              Anda akan melatih ulang model ML dengan data berikut:
            </p>
            
            {/* Data Summary */}
            <div className="bg-gray-50 dark:bg-navy-700 rounded-lg p-4 space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Dataset Original:</span>
                <span className="font-semibold text-navy-700 dark:text-white">
                  {preview.original_dataset_samples.toLocaleString()} samples
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Total Validasi (semua):</span>
                <span className="font-semibold text-blue-600 dark:text-blue-400">
                  +{preview.total_validations.toLocaleString()} samples
                </span>
              </div>
              {preview.pending_validations > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400 dark:text-gray-500 pl-4">• Validasi baru:</span>
                  <span className="text-green-600 dark:text-green-400">
                    +{preview.pending_validations.toLocaleString()}
                  </span>
                </div>
              )}
              {(preview.total_validations - preview.pending_validations) > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400 dark:text-gray-500 pl-4">• Validasi sebelumnya:</span>
                  <span className="text-gray-500 dark:text-gray-400">
                    {(preview.total_validations - preview.pending_validations).toLocaleString()}
                  </span>
                </div>
              )}
              {preview.total_validations > 0 && (
                <div className="pl-4 text-sm space-y-1">
                  <div className="flex justify-between text-gray-400 dark:text-gray-500">
                    <span>• Koreksi (label diperbaiki):</span>
                    <span className="text-amber-600 dark:text-amber-400">
                      {preview.corrections_count}
                    </span>
                  </div>
                  <div className="flex justify-between text-gray-400 dark:text-gray-500">
                    <span>• Konfirmasi (label benar):</span>
                    <span className="text-green-600 dark:text-green-400">
                      {preview.confirmations_count}
                    </span>
                  </div>
                </div>
              )}
              <div className="border-t border-gray-200 dark:border-navy-600 pt-3 flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Total Training Data:</span>
                <span className="font-bold text-navy-700 dark:text-white">
                  {preview.total_samples_after_training.toLocaleString()} samples
                </span>
              </div>
            </div>

            {/* Current Model Info */}
            {preview.current_model_version && (
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  <strong>Model Saat Ini:</strong> {preview.current_model_version}
                  {preview.current_model_accuracy !== null && (
                    <span className="ml-2">
                      (Accuracy: {(preview.current_model_accuracy * 100).toFixed(2)}%)
                    </span>
                  )}
                </p>
              </div>
            )}

            {/* Warning/Info messages */}
            {preview.message && (
              <div className={`rounded-lg p-4 flex items-start gap-2 ${
                preview.can_retrain 
                  ? 'bg-amber-50 dark:bg-amber-900/20' 
                  : 'bg-red-50 dark:bg-red-900/20'
              }`}>
                <MdWarning className={`h-5 w-5 flex-shrink-0 mt-0.5 ${
                  preview.can_retrain ? 'text-amber-500' : 'text-red-500'
                }`} />
                <p className={`text-sm ${
                  preview.can_retrain 
                    ? 'text-amber-700 dark:text-amber-300' 
                    : 'text-red-700 dark:text-red-300'
                }`}>
                  {preview.message}
                </p>
              </div>
            )}

            <p className="text-sm text-gray-500 dark:text-gray-400">
              Proses retraining akan memakan waktu beberapa menit. Model saat ini akan tetap aktif selama proses berlangsung.
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-navy-700 rounded-lg transition-colors disabled:opacity-50"
          >
            Batal
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading || previewLoading || !preview?.can_retrain}
            className="flex items-center gap-2 px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Memproses...
              </>
            ) : (
              <>
                <MdPlayArrow className="h-5 w-5" />
                Mulai Retraining
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Async Training Progress Component (for Celery task)
 */
const AsyncTrainingProgress = ({
  taskId,
  onComplete,
  onError,
}: {
  taskId: string;
  onComplete: () => void;
  onError: (message: string) => void;
}) => {
  const [taskStatus, setTaskStatus] = useState<{
    status: string;
    progress: number;
    stage: string;
    message: string;
  }>({
    status: 'PENDING',
    progress: 0,
    stage: 'pending',
    message: 'Menunggu task dimulai...',
  });

  // Use refs to avoid re-creating polling function on callback changes
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  
  useEffect(() => {
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onComplete, onError]);

  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout | null = null;
    
    const pollStatus = async () => {
      try {
        const status = await api.model.taskStatus(taskId);
        
        if (!isMounted) return;
        
        console.log('Task status:', status); // Debug log
        
        setTaskStatus({
          status: status.status,
          progress: status.progress || 0,
          stage: status.stage || 'processing',
          message: status.message || 'Processing...',
        });
        
        if (status.status === 'SUCCESS') {
          onCompleteRef.current();
          return;
        }
        
        if (status.status === 'FAILURE') {
          onErrorRef.current(status.message || 'Retraining gagal');
          return;
        }
        
        // Continue polling for PENDING, STARTED, PROGRESS, RETRY states
        if (isMounted && ['PENDING', 'STARTED', 'PROGRESS', 'RETRY'].includes(status.status)) {
          timeoutId = setTimeout(pollStatus, 2000);
        }
      } catch (err) {
        console.error('Failed to poll task status:', err);
        if (isMounted) {
          timeoutId = setTimeout(pollStatus, 3000);
        }
      }
    };
    
    // Start polling immediately
    pollStatus();
    
    return () => {
      isMounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [taskId]);

  const stageLabels: Record<string, string> = {
    pending: 'Menunggu...',
    started: 'Memulai task...',
    initializing: 'Inisialisasi...',
    checking_data: 'Memeriksa data...',
    loading_data: 'Memuat data training...',
    training: 'Melatih model...',
    deploying: 'Deploy model baru...',
    finalizing: 'Finalisasi...',
    completed: 'Selesai!',
    failed: 'Gagal',
    retry: 'Mencoba ulang...',
  };

  return (
    <Card extra="!p-4 bg-brand-50 dark:bg-brand-900/20 border border-brand-200 dark:border-brand-800">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-brand-500 rounded-full animate-pulse" />
          <span className="font-semibold text-brand-700 dark:text-brand-300">
            Training in Progress
          </span>
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          Task: {taskId.slice(0, 8)}...
        </span>
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            {stageLabels[taskStatus.stage] || taskStatus.message}
          </span>
          <span className="font-medium text-brand-600 dark:text-brand-400">
            {taskStatus.progress}%
          </span>
        </div>
        <div className="h-2 bg-brand-100 dark:bg-brand-900/40 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all duration-500"
            style={{ width: `${taskStatus.progress}%` }}
          />
        </div>
      </div>
    </Card>
  );
};

/**
 * Main Model Management Page
 */
const ModelManagementPage = () => {
  // State
  const [metrics, setMetrics] = useState<ModelMetricsAdmin | null>(null);
  const [versions, setVersions] = useState<ModelVersionFull[]>([]);
  const [trend, setTrend] = useState<MetricsTrendResponse | null>(null);
  const [progress, setProgress] = useState<RetrainingProgressResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetraining, setIsRetraining] = useState(false);
  const [isRollingBack, setIsRollingBack] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showRetrainModal, setShowRetrainModal] = useState(false);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);

  /**
   * Fetch all data
   */
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const [metricsData, versionsData, trendData, progressData] = await Promise.all([
        api.model.metrics(),
        api.model.versions(20),
        api.model.metricsTrend(10),
        api.model.trainingProgress(),
      ]);
      
      setMetrics(metricsData);
      setVersions(versionsData);
      setTrend(trendData);
      setProgress(progressData);
    } catch (err) {
      console.error('Failed to fetch model data:', err);
      setError('Failed to load model data. You may not have admin access.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Poll for progress if training is in progress
  useEffect(() => {
    if (progress?.is_training) {
      const interval = setInterval(async () => {
        try {
          const progressData = await api.model.trainingProgress();
          setProgress(progressData);
          
          // If training completed, refresh all data
          if (!progressData.is_training) {
            fetchData();
          }
        } catch (err) {
          console.error('Failed to fetch progress:', err);
        }
      }, 3000);
      
      return () => clearInterval(interval);
    }
  }, [progress?.is_training, fetchData]);

  /**
   * Open retraining confirmation modal
   */
  const openRetrainModal = () => {
    setShowRetrainModal(true);
  };

  /**
   * Handle manual retraining (async via Celery)
   */
  const handleRetrain = async () => {
    if (isRetraining || activeTaskId) return;
    
    setIsRetraining(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      const result = await api.model.retrain();
      
      if (result.success && result.task_id) {
        // Start polling the task
        setActiveTaskId(result.task_id);
        setShowRetrainModal(false);
        setSuccessMessage('Retraining dimulai. Proses berjalan di background...');
      } else {
        setError(result.message || 'Gagal memulai retraining');
        setShowRetrainModal(false);
      }
    } catch (err: any) {
      console.error('Retraining failed:', err);
      let errorMessage = 'Retraining failed. ';
      if (err.message?.includes('Failed to fetch')) {
        errorMessage += 'Backend server tidak dapat dijangkau. Pastikan server berjalan.';
      } else if (err.data?.detail?.message) {
        errorMessage += err.data.detail.message;
      } else if (err.data?.message) {
        errorMessage += err.data.message;
      } else {
        errorMessage += 'Silakan coba lagi.';
      }
      setError(errorMessage);
      setShowRetrainModal(false);
    } finally {
      setIsRetraining(false);
    }
  };

  /**
   * Handle task completion
   */
  const handleTaskComplete = useCallback(() => {
    setActiveTaskId(null);
    setSuccessMessage('Model berhasil dilatih ulang!');
    fetchData();
  }, [fetchData]);

  /**
   * Handle task error
   */
  const handleTaskError = useCallback((message: string) => {
    setActiveTaskId(null);
    setError(`Retraining gagal: ${message}`);
  }, []);

  /**
   * Handle rollback
   */
  const handleRollback = async (versionId: string) => {
    if (isRollingBack) return;
    
    if (!confirm('Are you sure you want to rollback to this version?')) {
      return;
    }
    
    setIsRollingBack(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      const result = await api.model.rollback(versionId);
      
      if (result.success) {
        setSuccessMessage(result.message);
        fetchData();
      } else {
        setError(result.message);
      }
    } catch (err: any) {
      console.error('Rollback failed:', err);
      setError(err.data?.message || 'Rollback failed. Please try again.');
    } finally {
      setIsRollingBack(false);
    }
  };

  /**
   * Prepare chart data for metrics trend
   */
  const chartData = trend?.trend.map((point) => ({
    name: point.version,
    accuracy: point.accuracy !== null ? point.accuracy * 100 : null,
    f1: point.f1 !== null ? point.f1 * 100 : null,
    precision: point.precision !== null ? point.precision * 100 : null,
    recall: point.recall !== null ? point.recall * 100 : null,
  })) || [];

  const chartOptions = {
    chart: {
      toolbar: { show: false },
      zoom: { enabled: false },
    },
    colors: ['#4318FF', '#39B8FF', '#01B574', '#FFB547'],
    dataLabels: { enabled: false },
    stroke: { curve: 'smooth' as const, width: 2 },
    xaxis: {
      categories: chartData.map((d) => d.name),
      labels: {
        style: {
          colors: '#A3AED0',
          fontSize: '12px',
        },
      },
    },
    yaxis: {
      min: 0,
      max: 100,
      labels: {
        style: {
          colors: '#A3AED0',
          fontSize: '12px',
        },
        formatter: (val: number | null | undefined) => 
          val != null ? `${val.toFixed(0)}%` : '',
      },
    },
    legend: {
      show: true,
      position: 'top' as const,
      horizontalAlign: 'right' as const,
    },
    tooltip: {
      theme: 'dark',
      y: {
        formatter: (val: number | null | undefined) => 
          val != null ? `${val.toFixed(2)}%` : 'N/A',
      },
    },
    grid: {
      borderColor: '#E2E8F0',
      strokeDashArray: 5,
    },
  };

  const chartSeries = [
    { name: 'Accuracy', data: chartData.map((d) => d.accuracy) },
    { name: 'F1 Score', data: chartData.map((d) => d.f1) },
    { name: 'Precision', data: chartData.map((d) => d.precision) },
    { name: 'Recall', data: chartData.map((d) => d.recall) },
  ];

  if (isLoading) {
    return (
      <div className="mt-3 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} extra="!p-4 animate-pulse">
              <div className="h-20 bg-gray-200 dark:bg-navy-700 rounded" />
            </Card>
          ))}
        </div>
        <Card extra="!p-6 animate-pulse">
          <div className="h-64 bg-gray-200 dark:bg-navy-700 rounded" />
        </Card>
      </div>
    );
  }

  return (
    <div className="mt-3 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-700 dark:text-white">
            Model Management
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Monitor ML model performance and manage versions
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-navy-700 rounded-lg transition-colors"
          >
            <MdRefresh className="h-5 w-5" />
          </button>
          <button
            onClick={openRetrainModal}
            disabled={isRetraining || progress?.is_training || !!activeTaskId}
            className="flex items-center gap-2 px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {(progress?.is_training || activeTaskId) ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Training...
              </>
            ) : (
              <>
                <MdPlayArrow className="h-5 w-5" />
                Retrain Model
              </>
            )}
          </button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <Card extra="!p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
            <MdWarning className="h-5 w-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        </Card>
      )}
      
      {successMessage && (
        <Card extra="!p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
          <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
            <MdCheckCircle className="h-5 w-5 flex-shrink-0" />
            <span>{successMessage}</span>
          </div>
        </Card>
      )}

      {/* Training Progress (Celery Task) */}
      {activeTaskId && (
        <AsyncTrainingProgress
          taskId={activeTaskId}
          onComplete={handleTaskComplete}
          onError={handleTaskError}
        />
      )}

      {/* Training Progress (Legacy) */}
      {!activeTaskId && <TrainingProgress progress={progress} onRefresh={fetchData} />}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Current Version"
          value={metrics?.current_version || 'N/A'}
          subtitle={`${metrics?.total_versions || 0} total versions`}
          icon={MdCheckCircle}
          color="brand"
        />
        <MetricCard
          title="Accuracy"
          value={metrics?.accuracy !== null ? `${(metrics.accuracy * 100).toFixed(2)}%` : 'N/A'}
          trend={trend?.improvement_summary?.accuracy_percent}
          icon={MdTrendingUp}
          color="green"
        />
        <MetricCard
          title="F1 Score"
          value={metrics?.f1 !== null ? `${(metrics.f1 * 100).toFixed(2)}%` : 'N/A'}
          trend={trend?.improvement_summary?.f1_percent}
          icon={MdTrendingUp}
          color="green"
        />
        <MetricCard
          title="Pending Validations"
          value={metrics?.pending_validations?.toString() || '0'}
          subtitle="Ready for training"
          icon={MdInfo}
          color="amber"
        />
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card extra="!p-4">
          <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3">
            Precision
          </h4>
          <p className="text-3xl font-bold text-navy-700 dark:text-white">
            {metrics?.precision !== null ? `${(metrics.precision * 100).toFixed(2)}%` : 'N/A'}
          </p>
        </Card>
        <Card extra="!p-4">
          <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3">
            Recall
          </h4>
          <p className="text-3xl font-bold text-navy-700 dark:text-white">
            {metrics?.recall !== null ? `${(metrics.recall * 100).toFixed(2)}%` : 'N/A'}
          </p>
        </Card>
        <Card extra="!p-4">
          <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3">
            Training Samples
          </h4>
          <p className="text-3xl font-bold text-navy-700 dark:text-white">
            {metrics?.training_samples?.toLocaleString() || 'N/A'}
          </p>
          {metrics?.validation_samples && metrics.validation_samples > 0 && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              +{metrics.validation_samples} from validations
            </p>
          )}
        </Card>
      </div>

      {/* Metrics Trend Chart */}
      {chartData.length > 1 && (
        <Card extra="!p-6">
          <h3 className="text-lg font-bold text-navy-700 dark:text-white mb-4 flex items-center gap-2">
            <MdTrendingUp className="h-5 w-5" />
            Metrics Trend
          </h3>
          <div className="h-80">
            <LineChart chartData={chartSeries} chartOptions={chartOptions} />
          </div>
        </Card>
      )}

      {/* Version History */}
      <VersionHistoryTable
        versions={versions}
        onRollback={handleRollback}
        isRollingBack={isRollingBack}
      />

      {/* Retraining Confirmation Modal */}
      <RetrainingConfirmModal
        isOpen={showRetrainModal}
        onClose={() => setShowRetrainModal(false)}
        onConfirm={handleRetrain}
        isLoading={isRetraining}
      />
    </div>
  );
};

export default ModelManagementPage;
