'use client';

/**
 * Scan History Page - Gambling Comment Detector
 * 
 * Displays paginated scan history with summary for each scan.
 * Links to scan details page.
 * Requirements: 7.3
 */

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { 
  MdHistory, 
  MdChevronLeft, 
  MdChevronRight, 
  MdWarning,
  MdCheckCircle,
  MdPending,
  MdError,
  MdRefresh,
  MdSearch,
  MdPlayCircle,
  MdDelete
} from 'react-icons/md';

import Card from 'components/card';
import { api } from 'lib/api';
import type { ScanResponse, ScanListResponse, ScanStatus } from 'lib/types';

/**
 * Loading skeleton for scan history items
 */
const ScanHistorySkeleton = () => (
  <Card extra="!p-4 animate-pulse">
    <div className="flex flex-col sm:flex-row gap-4">
      <div className="w-full sm:w-32 h-20 bg-gray-200 dark:bg-navy-700 rounded-lg flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-5 w-3/4 bg-gray-200 dark:bg-navy-700 rounded" />
        <div className="h-4 w-1/2 bg-gray-200 dark:bg-navy-700 rounded" />
        <div className="flex gap-2 mt-2">
          <div className="h-6 w-20 bg-gray-200 dark:bg-navy-700 rounded-full" />
          <div className="h-6 w-24 bg-gray-200 dark:bg-navy-700 rounded-full" />
        </div>
      </div>
    </div>
  </Card>
);

/**
 * Status badge component
 */
const StatusBadge = ({ status }: { status: ScanStatus }) => {
  const statusConfig = {
    pending: {
      icon: MdPending,
      text: 'Pending',
      className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
    },
    processing: {
      icon: MdRefresh,
      text: 'Processing',
      className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
    },
    completed: {
      icon: MdCheckCircle,
      text: 'Completed',
      className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
    },
    failed: {
      icon: MdError,
      text: 'Failed',
      className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
    }
  };

  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.className}`}>
      <Icon className={`h-3 w-3 ${status === 'processing' ? 'animate-spin' : ''}`} />
      {config.text}
    </span>
  );
};


/**
 * Scan history item card
 * Requirements: 7.3 - Show summary for each scan
 */
const ScanHistoryCard = ({ 
  scan, 
  onClick,
  onDelete
}: { 
  scan: ScanResponse;
  onClick: () => void;
  onDelete: (e: React.MouseEvent) => void;
}) => {
  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card 
      extra="!p-4 cursor-pointer hover:shadow-lg transition-shadow duration-200 group"
      onClick={onClick}
    >
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Video Thumbnail Placeholder */}
        <div className="relative w-full sm:w-32 h-20 rounded-lg overflow-hidden flex-shrink-0 bg-gray-100 dark:bg-navy-700">
          <div className="absolute inset-0 flex items-center justify-center">
            <MdPlayCircle className="h-8 w-8 text-gray-400 dark:text-gray-500" />
          </div>
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200" />
        </div>

        {/* Scan Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-base font-bold text-navy-700 dark:text-white line-clamp-1">
              {scan.video_title || `Video: ${scan.video_id}`}
            </h3>
            <button
              onClick={onDelete}
              className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors opacity-0 group-hover:opacity-100"
              title="Delete scan"
            >
              <MdDelete className="h-4 w-4" />
            </button>
          </div>
          
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {formatDate(scan.created_at)}
          </p>

          {/* Status and Summary */}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <StatusBadge status={scan.status} />
            
            <span className="text-xs text-gray-400 dark:text-gray-500">
              ID: {scan.video_id}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};

/**
 * Empty state component
 */
const EmptyState = () => (
  <Card extra="!p-8 text-center">
    <div className="flex flex-col items-center justify-center py-8">
      <MdHistory className="h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" />
      <h4 className="text-lg font-bold text-navy-700 dark:text-white mb-2">
        No Scan History
      </h4>
      <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md">
        You haven&apos;t scanned any videos yet. Go to My Videos or Browse Videos to start scanning for gambling comments.
      </p>
    </div>
  </Card>
);

/**
 * Error display component
 */
const ErrorDisplay = ({ message, onRetry }: { message: string; onRetry: () => void }) => (
  <Card extra="!p-8 text-center">
    <div className="flex flex-col items-center justify-center py-8">
      <div className="h-16 w-16 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center mb-4">
        <MdWarning className="h-8 w-8 text-red-500" />
      </div>
      <h4 className="text-lg font-bold text-navy-700 dark:text-white mb-2">
        Failed to Load History
      </h4>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 max-w-md">
        {message}
      </p>
      <button
        onClick={onRetry}
        className="px-6 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors flex items-center gap-2"
      >
        <MdRefresh className="h-5 w-5" />
        Try Again
      </button>
    </div>
  </Card>
);


/**
 * Delete confirmation modal
 */
const DeleteConfirmModal = ({ 
  isOpen, 
  onClose, 
  onConfirm,
  isDeleting
}: { 
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isDeleting: boolean;
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="absolute inset-0 bg-black/50" 
        onClick={onClose}
      />
      <Card extra="!p-6 relative z-10 max-w-md mx-4">
        <h3 className="text-lg font-bold text-navy-700 dark:text-white mb-2">
          Delete Scan?
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          Are you sure you want to delete this scan? This action cannot be undone and all scan results will be permanently removed.
        </p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-navy-700 rounded-lg hover:bg-gray-200 dark:hover:bg-navy-600 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {isDeleting ? (
              <>
                <MdRefresh className="h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <MdDelete className="h-4 w-4" />
                Delete
              </>
            )}
          </button>
        </div>
      </Card>
    </div>
  );
};

/**
 * Main Scan History Page Component
 * Requirements: 7.3 - Display paginated scan history
 */
const ScanHistoryPage = () => {
  const router = useRouter();
  const [scans, setScans] = useState<ScanResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalScans, setTotalScans] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [scanToDelete, setScanToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const ITEMS_PER_PAGE = 10;

  /**
   * Fetch scan history from API
   * Requirements: 7.3 - Return paginated list of past scans with summary statistics
   */
  const fetchHistory = useCallback(async (page: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const response: ScanListResponse = await api.scan.history(page, ITEMS_PER_PAGE);
      setScans(response.items);
      setTotalPages(response.pages);
      setTotalScans(response.total);
      setCurrentPage(response.page);
    } catch (err) {
      console.error('Failed to fetch scan history:', err);
      setError('Failed to load scan history. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory(currentPage);
  }, [fetchHistory, currentPage]);

  /**
   * Handle page navigation
   */
  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  /**
   * Navigate to scan detail page
   * Requirements: 7.3 - Link to scan details
   */
  const handleScanClick = (scanId: string) => {
    router.push(`/admin/scan/${scanId}`);
  };

  /**
   * Handle delete button click
   */
  const handleDeleteClick = (e: React.MouseEvent, scanId: string) => {
    e.stopPropagation();
    setScanToDelete(scanId);
    setDeleteModalOpen(true);
  };

  /**
   * Confirm and execute delete
   */
  const handleConfirmDelete = async () => {
    if (!scanToDelete) return;
    
    setIsDeleting(true);
    try {
      await api.scan.delete(scanToDelete);
      // Refresh the list
      await fetchHistory(currentPage);
      setDeleteModalOpen(false);
      setScanToDelete(null);
    } catch (err) {
      console.error('Failed to delete scan:', err);
      setError('Failed to delete scan. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  /**
   * Filter scans by search query
   */
  const filteredScans = scans.filter(scan => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      scan.video_id.toLowerCase().includes(query) ||
      (scan.video_title?.toLowerCase().includes(query) ?? false)
    );
  });

  return (
    <div className="mt-3">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-700 dark:text-white">
          Scan History
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          View and manage your past video scans
        </p>
      </div>

      {/* Search and Stats Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        {/* Search */}
        <div className="relative max-w-md w-full">
          <MdSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by video title or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 text-sm border border-gray-200 dark:border-navy-600 rounded-xl bg-white dark:bg-navy-800 text-navy-700 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Stats */}
        {!isLoading && !error && totalScans > 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {totalScans} scan{totalScans !== 1 ? 's' : ''} total
          </p>
        )}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-4">
          <ScanHistorySkeleton />
          <ScanHistorySkeleton />
          <ScanHistorySkeleton />
          <ScanHistorySkeleton />
          <ScanHistorySkeleton />
        </div>
      ) : error ? (
        <ErrorDisplay message={error} onRetry={() => fetchHistory(currentPage)} />
      ) : filteredScans.length === 0 ? (
        searchQuery ? (
          <Card extra="!p-8 text-center">
            <div className="flex flex-col items-center justify-center py-8">
              <MdSearch className="h-12 w-12 text-gray-300 dark:text-gray-600 mb-4" />
              <h4 className="text-lg font-bold text-navy-700 dark:text-white mb-2">
                No Results Found
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                No scans match your search query. Try a different search term.
              </p>
            </div>
          </Card>
        ) : (
          <EmptyState />
        )
      ) : (
        <div className="space-y-4">
          {filteredScans.map((scan) => (
            <ScanHistoryCard
              key={scan.id}
              scan={scan}
              onClick={() => handleScanClick(scan.id)}
              onDelete={(e) => handleDeleteClick(e, scan.id)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!isLoading && !error && totalPages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="flex items-center gap-1 px-3 py-2 rounded-lg bg-white dark:bg-navy-800 text-navy-700 dark:text-white border border-gray-200 dark:border-navy-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-navy-700 transition-colors"
          >
            <MdChevronLeft className="h-5 w-5" />
            <span className="hidden sm:inline">Previous</span>
          </button>
          
          {/* Page Numbers */}
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum: number;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }
              
              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === pageNum
                      ? 'bg-brand-500 text-white'
                      : 'bg-white dark:bg-navy-800 text-navy-700 dark:text-white border border-gray-200 dark:border-navy-600 hover:bg-gray-50 dark:hover:bg-navy-700'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>
          
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="flex items-center gap-1 px-3 py-2 rounded-lg bg-white dark:bg-navy-800 text-navy-700 dark:text-white border border-gray-200 dark:border-navy-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-navy-700 transition-colors"
          >
            <span className="hidden sm:inline">Next</span>
            <MdChevronRight className="h-5 w-5" />
          </button>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setScanToDelete(null);
        }}
        onConfirm={handleConfirmDelete}
        isDeleting={isDeleting}
      />
    </div>
  );
};

export default ScanHistoryPage;
