'use client';

/**
 * ValidationContributionCard Component
 * 
 * Displays user's validation contribution statistics including:
 * - Total validations submitted
 * - Validations that contributed to model training
 * - Corrections made (where user disagreed with model)
 * - Number of model versions the user contributed to
 * 
 * Requirements: 10.3
 */

import { useEffect, useState } from 'react';
import { MdVerified, MdEdit, MdAutorenew, MdStar } from 'react-icons/md';
import Card from 'components/card';
import { api } from 'lib/api';
import type { ValidationContributionDisplay } from 'lib/types';

interface ValidationContributionCardProps {
  className?: string;
}

const ValidationContributionCard = ({ className = '' }: ValidationContributionCardProps) => {
  const [contributions, setContributions] = useState<ValidationContributionDisplay | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContributions = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await api.dashboard.validationContributions();
        setContributions(data);
      } catch (err) {
        console.error('Failed to fetch validation contributions:', err);
        setError('Failed to load contributions');
      } finally {
        setIsLoading(false);
      }
    };

    fetchContributions();
  }, []);

  if (isLoading) {
    return (
      <Card extra={`!p-5 animate-pulse ${className}`}>
        <div className="h-6 w-40 bg-gray-200 dark:bg-navy-700 rounded mb-4" />
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-gray-200 dark:bg-navy-700 rounded" />
          ))}
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

  if (!contributions) {
    return null;
  }

  const contributionRate = contributions.total_validations > 0
    ? Math.round((contributions.contributed_to_training / contributions.total_validations) * 100)
    : 0;

  return (
    <Card extra={`!p-5 ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <MdStar className="h-5 w-5 text-amber-500" />
        <h4 className="text-lg font-bold text-navy-700 dark:text-white">
          Your Contributions
        </h4>
      </div>

      {contributions.total_validations === 0 ? (
        <div className="text-center py-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            You haven't validated any predictions yet.
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
            Start validating to help improve the model!
          </p>
        </div>
      ) : (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <MdVerified className="h-4 w-4 text-blue-500" />
                <span className="text-xs text-gray-600 dark:text-gray-400">Total Validated</span>
              </div>
              <p className="text-xl font-bold text-navy-700 dark:text-white">
                {contributions.total_validations.toLocaleString()}
              </p>
            </div>

            <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <MdAutorenew className="h-4 w-4 text-green-500" />
                <span className="text-xs text-gray-600 dark:text-gray-400">Used in Training</span>
              </div>
              <p className="text-xl font-bold text-navy-700 dark:text-white">
                {contributions.contributed_to_training.toLocaleString()}
              </p>
            </div>

            <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <MdEdit className="h-4 w-4 text-amber-500" />
                <span className="text-xs text-gray-600 dark:text-gray-400">Corrections Made</span>
              </div>
              <p className="text-xl font-bold text-navy-700 dark:text-white">
                {contributions.corrections_made.toLocaleString()}
              </p>
            </div>

            <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <MdStar className="h-4 w-4 text-purple-500" />
                <span className="text-xs text-gray-600 dark:text-gray-400">Models Improved</span>
              </div>
              <p className="text-xl font-bold text-navy-700 dark:text-white">
                {contributions.model_versions_contributed}
              </p>
            </div>
          </div>

          {/* Contribution Progress */}
          {contributions.contributed_to_training > 0 && (
            <div className="pt-3 border-t border-gray-100 dark:border-navy-600">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  Contribution Rate
                </span>
                <span className="text-sm font-semibold text-navy-700 dark:text-white">
                  {contributionRate}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-navy-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-green-400 to-emerald-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${contributionRate}%` }}
                />
              </div>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 text-center">
                {contributions.contributed_to_training} of your validations helped improve the model
              </p>
            </div>
          )}
        </>
      )}
    </Card>
  );
};

export default ValidationContributionCard;
