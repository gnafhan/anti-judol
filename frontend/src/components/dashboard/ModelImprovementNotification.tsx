'use client';

/**
 * ModelImprovementNotification Component
 * 
 * Shows a notification banner when a new model is deployed with improvement percentage.
 * Displays improvement details and can be dismissed by the user.
 * 
 * Requirements: 10.2
 */

import { useEffect, useState } from 'react';
import { MdTrendingUp, MdClose, MdCelebration } from 'react-icons/md';
import { api } from 'lib/api';
import type { ModelImprovementDisplay } from 'lib/types';

interface ModelImprovementNotificationProps {
  className?: string;
  onDismiss?: () => void;
}

// Key for localStorage to track dismissed notifications
const DISMISSED_KEY = 'model_improvement_dismissed';

const ModelImprovementNotification = ({ 
  className = '',
  onDismiss,
}: ModelImprovementNotificationProps) => {
  const [improvement, setImprovement] = useState<ModelImprovementDisplay | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchImprovement = async () => {
      setIsLoading(true);
      try {
        const data = await api.dashboard.modelImprovement();
        setImprovement(data);
        
        // Check if this notification was already dismissed
        if (data.has_improvement && data.deployed_at) {
          const dismissedVersion = localStorage.getItem(DISMISSED_KEY);
          if (dismissedVersion !== data.new_version) {
            setIsVisible(true);
          }
        }
      } catch (err) {
        console.error('Failed to fetch model improvement:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchImprovement();
  }, []);

  const handleDismiss = () => {
    if (improvement?.new_version) {
      localStorage.setItem(DISMISSED_KEY, improvement.new_version);
    }
    setIsVisible(false);
    onDismiss?.();
  };

  // Don't render if loading, no improvement, or dismissed
  if (isLoading || !improvement?.has_improvement || !isVisible) {
    return null;
  }

  const formatPercent = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '';
    return value > 0 ? `+${value.toFixed(1)}%` : `${value.toFixed(1)}%`;
  };

  const formatDate = (dateStr: string | null | undefined): string => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffHours < 1) return 'just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div 
      className={`relative overflow-hidden rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 p-4 text-white shadow-lg ${className}`}
    >
      {/* Background decoration */}
      <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-white/10" />
      <div className="absolute -right-8 -bottom-8 h-32 w-32 rounded-full bg-white/5" />
      
      <div className="relative flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20">
            <MdCelebration className="h-5 w-5" />
          </div>
          
          <div>
            <h4 className="font-bold text-white">
              Model Improved! 🎉
            </h4>
            <p className="mt-1 text-sm text-white/90">
              New model <span className="font-semibold">{improvement.new_version}</span> deployed{' '}
              {improvement.deployed_at && (
                <span className="text-white/70">{formatDate(improvement.deployed_at)}</span>
              )}
            </p>
            
            <div className="mt-2 flex items-center gap-4">
              {improvement.improvement_percent !== null && (
                <div className="flex items-center gap-1">
                  <MdTrendingUp className="h-4 w-4" />
                  <span className="text-sm font-semibold">
                    {formatPercent(improvement.improvement_percent)} accuracy
                  </span>
                </div>
              )}
              
              {improvement.previous_version && (
                <span className="text-xs text-white/70">
                  vs {improvement.previous_version}
                </span>
              )}
            </div>
          </div>
        </div>
        
        <button
          onClick={handleDismiss}
          className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition-colors"
          aria-label="Dismiss notification"
        >
          <MdClose className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default ModelImprovementNotification;
