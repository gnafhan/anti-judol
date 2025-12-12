'use client';

/**
 * Browse/Search Page - Gambling Comment Detector
 * 
 * Allows users to search and browse public YouTube videos.
 * Requirements: 5.1, 5.2
 */

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { 
  MdSearch, 
  MdPlayCircle, 
  MdVisibility, 
  MdComment, 
  MdChevronLeft, 
  MdChevronRight, 
  MdVideoLibrary,
  MdRefresh,
  MdClose
} from 'react-icons/md';

import Card from 'components/card';
import { api } from 'lib/api';
import type { VideoInfo, VideoListResponse } from 'lib/types';

/**
 * Loading skeleton for video cards
 */
const VideoCardSkeleton = () => (
  <Card extra="flex flex-col w-full h-full !p-4 animate-pulse">
    <div className="relative w-full h-40 bg-gray-200 dark:bg-navy-700 rounded-xl" />
    <div className="mt-3 space-y-2">
      <div className="h-5 w-3/4 bg-gray-200 dark:bg-navy-700 rounded" />
      <div className="h-4 w-1/2 bg-gray-200 dark:bg-navy-700 rounded" />
      <div className="flex gap-4 mt-2">
        <div className="h-4 w-16 bg-gray-200 dark:bg-navy-700 rounded" />
        <div className="h-4 w-16 bg-gray-200 dark:bg-navy-700 rounded" />
      </div>
    </div>
  </Card>
);

/**
 * Video card component for search results
 */
const VideoCard = ({ video, onClick }: { video: VideoInfo; onClick: () => void }) => {
  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <Card 
      extra="flex flex-col w-full h-full !p-4 cursor-pointer hover:shadow-lg transition-shadow duration-200"
      onClick={onClick}
    >
      {/* Thumbnail */}
      <div className="relative w-full h-40 rounded-xl overflow-hidden group">
        <Image
          src={video.thumbnail_url}
          alt={video.title}
          fill
          className="object-cover group-hover:scale-105 transition-transform duration-200"
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        />
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200 flex items-center justify-center">
          <MdPlayCircle className="h-12 w-12 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
        </div>
      </div>

      {/* Video Info */}
      <div className="mt-3 flex flex-col flex-grow">
        <h3 className="text-base font-bold text-navy-700 dark:text-white line-clamp-2 mb-1">
          {video.title}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          {video.channel_name}
        </p>
        
        {/* Stats */}
        <div className="flex items-center gap-4 mt-auto text-sm text-gray-500 dark:text-gray-400">
          <div className="flex items-center gap-1">
            <MdVisibility className="h-4 w-4" />
            <span>{formatNumber(video.view_count)}</span>
          </div>
          <div className="flex items-center gap-1">
            <MdComment className="h-4 w-4" />
            <span>{formatNumber(video.comment_count)}</span>
          </div>
        </div>
        
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
          {formatDate(video.published_at)}
        </p>
      </div>
    </Card>
  );
};


/**
 * Empty state component - shown before search or when no results
 */
const EmptyState = ({ hasSearched, searchQuery }: { hasSearched: boolean; searchQuery: string }) => (
  <Card extra="!p-8 text-center col-span-full">
    <div className="flex flex-col items-center justify-center py-8">
      <MdVideoLibrary className="h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" />
      <h4 className="text-lg font-bold text-navy-700 dark:text-white mb-2">
        {hasSearched ? 'No Videos Found' : 'Search for Videos'}
      </h4>
      <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md">
        {hasSearched 
          ? `No videos found for "${searchQuery}". Try a different search term.`
          : 'Enter a search term above to find public YouTube videos and scan them for gambling comments.'
        }
      </p>
    </div>
  </Card>
);

/**
 * Error display component
 */
const ErrorDisplay = ({ message, onRetry }: { message: string; onRetry: () => void }) => (
  <Card extra="!p-8 text-center col-span-full">
    <div className="flex flex-col items-center justify-center py-8">
      <div className="h-16 w-16 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center mb-4">
        <MdRefresh className="h-8 w-8 text-red-500" />
      </div>
      <h4 className="text-lg font-bold text-navy-700 dark:text-white mb-2">
        Search Failed
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

const BrowsePage = () => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [videos, setVideos] = useState<VideoInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [nextPageToken, setNextPageToken] = useState<string | null>(null);
  const [prevPageTokens, setPrevPageTokens] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);

  /**
   * Search for public videos
   * Requirements: 5.1, 5.2
   */
  const searchVideos = useCallback(async (query: string, pageToken?: string) => {
    if (!query.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response: VideoListResponse = await api.youtube.search(query, pageToken);
      setVideos(response.items);
      setNextPageToken(response.next_page_token);
      setTotalResults(response.total_results);
      setHasSearched(true);
    } catch (err) {
      console.error('Failed to search videos:', err);
      setError('Failed to search videos. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Handle search form submission
   */
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    // Reset pagination state for new search
    setPrevPageTokens([]);
    setCurrentPage(1);
    setSubmittedQuery(searchQuery);
    searchVideos(searchQuery);
  };

  /**
   * Handle next page navigation
   */
  const handleNextPage = () => {
    if (nextPageToken && submittedQuery) {
      setPrevPageTokens(prev => [...prev, nextPageToken || '']);
      setCurrentPage(prev => prev + 1);
      searchVideos(submittedQuery, nextPageToken);
    }
  };

  /**
   * Handle previous page navigation
   */
  const handlePrevPage = () => {
    if (prevPageTokens.length > 0 && submittedQuery) {
      const newPrevTokens = [...prevPageTokens];
      const prevToken = newPrevTokens.pop();
      setPrevPageTokens(newPrevTokens);
      setCurrentPage(prev => prev - 1);
      searchVideos(submittedQuery, prevToken === '' ? undefined : prevToken);
    }
  };

  /**
   * Clear search and reset state
   */
  const handleClearSearch = () => {
    setSearchQuery('');
    setSubmittedQuery('');
    setVideos([]);
    setHasSearched(false);
    setNextPageToken(null);
    setPrevPageTokens([]);
    setCurrentPage(1);
    setTotalResults(0);
    setError(null);
  };

  /**
   * Navigate to video detail page
   */
  const handleVideoClick = (videoId: string) => {
    router.push(`/admin/browse/${videoId}`);
  };

  return (
    <div className="mt-3">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-700 dark:text-white">
          Browse Videos
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Search for public YouTube videos to scan for gambling comments
        </p>
      </div>

      {/* Search Form */}
      <Card extra="!p-4 mb-6">
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="relative flex-1">
            <MdSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for YouTube videos..."
              className="w-full pl-10 pr-10 py-3 rounded-lg border border-gray-200 dark:border-navy-600 bg-white dark:bg-navy-800 text-navy-700 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <MdClose className="h-5 w-5" />
              </button>
            )}
          </div>
          <button
            type="submit"
            disabled={isLoading || !searchQuery.trim()}
            className="px-6 py-3 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Searching...
              </>
            ) : (
              <>
                <MdSearch className="h-5 w-5" />
                Search
              </>
            )}
          </button>
        </form>
      </Card>

      {/* Results Count */}
      {hasSearched && !isLoading && !error && totalResults > 0 && (
        <div className="mb-4 flex items-center justify-between">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Found {totalResults} video{totalResults !== 1 ? 's' : ''} for &quot;{submittedQuery}&quot;
          </p>
        </div>
      )}

      {/* Video Grid */}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {isLoading ? (
          <>
            <VideoCardSkeleton />
            <VideoCardSkeleton />
            <VideoCardSkeleton />
            <VideoCardSkeleton />
            <VideoCardSkeleton />
            <VideoCardSkeleton />
            <VideoCardSkeleton />
            <VideoCardSkeleton />
          </>
        ) : error ? (
          <ErrorDisplay message={error} onRetry={() => searchVideos(submittedQuery)} />
        ) : videos.length === 0 ? (
          <EmptyState hasSearched={hasSearched} searchQuery={submittedQuery} />
        ) : (
          videos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              onClick={() => handleVideoClick(video.id)}
            />
          ))
        )}
      </div>

      {/* Pagination */}
      {!isLoading && !error && videos.length > 0 && (nextPageToken || prevPageTokens.length > 0) && (
        <div className="mt-6 flex items-center justify-center gap-4">
          <button
            onClick={handlePrevPage}
            disabled={prevPageTokens.length === 0}
            className="flex items-center gap-1 px-4 py-2 rounded-lg bg-white dark:bg-navy-800 text-navy-700 dark:text-white border border-gray-200 dark:border-navy-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-navy-700 transition-colors"
          >
            <MdChevronLeft className="h-5 w-5" />
            Previous
          </button>
          
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {currentPage}
          </span>
          
          <button
            onClick={handleNextPage}
            disabled={!nextPageToken}
            className="flex items-center gap-1 px-4 py-2 rounded-lg bg-white dark:bg-navy-800 text-navy-700 dark:text-white border border-gray-200 dark:border-navy-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-navy-700 transition-colors"
          >
            Next
            <MdChevronRight className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  );
};

export default BrowsePage;
