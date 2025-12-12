'use client';

/**
 * My Videos List Page - Gambling Comment Detector
 * 
 * Displays the authenticated user's YouTube videos with pagination.
 * Requirements: 4.1, 4.4
 */

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { MdPlayCircle, MdVisibility, MdComment, MdChevronLeft, MdChevronRight, MdVideoLibrary, MdRefresh } from 'react-icons/md';

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
 * Video card component
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
 * Empty state component
 */
const EmptyState = () => (
  <Card extra="!p-8 text-center col-span-full">
    <div className="flex flex-col items-center justify-center py-8">
      <MdVideoLibrary className="h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" />
      <h4 className="text-lg font-bold text-navy-700 dark:text-white mb-2">
        No Videos Found
      </h4>
      <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md">
        You don&apos;t have any videos on your YouTube channel yet, or we couldn&apos;t access them.
        Make sure you&apos;ve granted the necessary permissions.
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
        Failed to Load Videos
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

const MyVideosPage = () => {
  const router = useRouter();
  const [videos, setVideos] = useState<VideoInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextPageToken, setNextPageToken] = useState<string | null>(null);
  const [prevPageTokens, setPrevPageTokens] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);

  /**
   * Fetch user's videos from YouTube API
   * Requirements: 4.1, 4.4
   */
  const fetchVideos = useCallback(async (pageToken?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response: VideoListResponse = await api.youtube.myVideos(pageToken);
      setVideos(response.items);
      setNextPageToken(response.next_page_token);
      setTotalResults(response.total_results);
    } catch (err) {
      console.error('Failed to fetch videos:', err);
      setError('Failed to load your videos. Please check your YouTube permissions and try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  /**
   * Handle next page navigation
   */
  const handleNextPage = () => {
    if (nextPageToken) {
      // Store current state for going back
      setPrevPageTokens(prev => [...prev, videos.length > 0 ? (nextPageToken || '') : '']);
      setCurrentPage(prev => prev + 1);
      fetchVideos(nextPageToken);
    }
  };

  /**
   * Handle previous page navigation
   */
  const handlePrevPage = () => {
    if (prevPageTokens.length > 0) {
      const newPrevTokens = [...prevPageTokens];
      const prevToken = newPrevTokens.pop();
      setPrevPageTokens(newPrevTokens);
      setCurrentPage(prev => prev - 1);
      fetchVideos(prevToken === '' ? undefined : prevToken);
    }
  };

  /**
   * Navigate to video detail page
   */
  const handleVideoClick = (videoId: string) => {
    router.push(`/admin/my-videos/${videoId}`);
  };

  return (
    <div className="mt-3">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-navy-700 dark:text-white">
            My Videos
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Select a video to scan for gambling comments
          </p>
        </div>
        {!isLoading && !error && totalResults > 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {totalResults} video{totalResults !== 1 ? 's' : ''} found
          </p>
        )}
      </div>

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
          <ErrorDisplay message={error} onRetry={() => fetchVideos()} />
        ) : videos.length === 0 ? (
          <EmptyState />
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

export default MyVideosPage;
