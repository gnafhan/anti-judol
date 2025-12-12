'use client';

/**
 * ModelMetricsCard Component
 * 
 * Displays model accuracy metrics and version information on the dashboard.
 * Shows current model version, accuracy before/after retraining, and other metrics.
 * 
 * Requirements: 10.1
 */

import { useEffect, useState } from 'react';
import { MdAutorenew, MdTrendingUp, MdInfo } from 'react-icons/md';
import Card from 'components/card';
import { api } from 'lib/api';
import type { ModelMetricsDisplay, ModelImprovementDisplay } from 'lib/types';

interface ModelMetricsCardProps {
  className?: string;
}

const ModelMetricsCard = ({ className = '' }: ModelMetricsCardProps) => {
  const [metrics, setMetrics] = useState<ModelMetricsDisplay | null>(null);
  const [improvement, setImprovement] = useState<ModelImprovementDisplay | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [metricsData, improvementData] = await Promise.all([
          api.dashboard.modelMetrics(),
          api.dashboard.modelImprovement(),
        ]);
        setMetrics(metricsData);
        setImprovement(improvementData);
      } catch (err) {
        console.error('Failed to fetch model metrics:', err);
        setError('Failed to load model metrics');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatPercent = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatDate = (dateStr: string | null | undefined): string => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <Card extra={`!p-5 animate-pulse ${className}`}>
        <div className="h-6 w-32 bg-gray-200 dark:bg-navy-700 rounded mb-4" />
        <div className="space-y-3">
          <div className="h-4 w-full bg-gray-200 dark:bg-navy-700 rounded" />
          <div className="h-4 w-3/4 bg-gray-200 dark:bg-navy-700 rounded" />
          <div className="h-4 w-1/2 bg-gray-200 dark:bg-navy-700 rounded" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card extra={`!p-5 ${className}`}>
        <p className="text-red-500 text-sm">{error}</p>
      </Card>
    );
  }

  return (
    <Card extra={`!p-5 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MdAutorenew className="h-5 w-5 text-brand-500" />
          <h4 className="text-lg font-bold text-navy-700 dark:text-white">
            ML Model
          </h4>
        </div>
        {metrics?.current_version && (
          <span className="px-2 py-1 text-xs font-medium bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 rounded-full">
            {metrics.current_version}
          </span>
        )}
      </div>

      {!metrics?.current_version ? (
        <div className="text-center py-4">
          <MdInfo className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            No model version available
          </p>
        </div>
      ) : (
        <>
          {/* Accuracy Display */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-gray-600 dark:text-gray-400">Accuracy</span>
              <span className="text-lg font-bold text-navy-700 dark:text-white">
                {formatPercent(metrics.accuracy)}
              </span>
            </div>
            {metrics.accuracy !== null && (
              <div className="w-full bg-gray-200 dark:bg-navy-700 rounded-full h-2">
                <div
                  className="bg-brand-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${(metrics.accuracy || 0) * 100}%` }}
                />
              </div>
            )}
          </div>

          {/* Improvement Badge */}
          {improvement?.has_improvement && improvement.improvement_percent !== null && (
            <div className="flex items-center gap-2 mb-4 p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <MdTrendingUp className="h-5 w-5 text-green-500" />
              <span className="text-sm text-green-700 dark:text-green-400">
                +{improvement.improvement_percent.toFixed(1)}% improvement from {improvement.previous_version}
              </span>
            </div>
          )}

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="p-2 bg-gray-50 dark:bg-navy-700 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">Precision</p>
              <p className="text-sm font-semibold text-navy-700 dark:text-white">
                {formatPercent(metrics.precision)}
              </p>
            </div>
            <div className="p-2 bg-gray-50 dark:bg-navy-700 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">Recall</p>
              <p className="text-sm font-semibold text-navy-700 dark:text-white">
                {formatPercent(metrics.recall)}
              </p>
            </div>
            <div className="p-2 bg-gray-50 dark:bg-navy-700 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">F1 Score</p>
              <p className="text-sm font-semibold text-navy-700 dark:text-white">
                {formatPercent(metrics.f1_score)}
              </p>
            </div>
            <div className="p-2 bg-gray-50 dark:bg-navy-700 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">Training Samples</p>
              <p className="text-sm font-semibold text-navy-700 dark:text-white">
                {metrics.training_samples?.toLocaleString() || 'N/A'}
              </p>
            </div>
          </div>

          {/* Footer Info */}
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-100 dark:border-navy-600">
            <span>Last trained: {formatDate(metrics.last_trained)}</span>
            {metrics.validation_samples !== null && metrics.validation_samples > 0 && (
              <span>+{metrics.validation_samples} validations</span>
            )}
          </div>
        </>
      )}
    </Card>
  );
};

export default ModelMetricsCard;
