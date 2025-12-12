'use client';

/**
 * Browse Video Detail Page - Gambling Comment Detector
 * 
 * Shows public video info, comments, and scan functionality.
 * Delete functionality is disabled for public videos (not owned by user).
 * Requirements: 5.3
 */

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import { 
  MdArrowBack, 
  MdPlayCircle, 
  MdVisibility, 
  MdComment, 
  MdSearch,
  MdWarning,
  MdCheckCircle,
  MdRefresh,
  MdDownload,
  MdClose,
  MdInfo
} from 'react-icons/md';

import Card from 'components/card';
import { ScanFlow } from 'components/scan';
import { api } from 'lib/api';
import type { VideoInfo, CommentInfo, ScanDetailResponse, ScanResultResponse } from 'lib/types';

/**
 * Loading skeleton for video info
 */
const VideoInfoSkeleton = () => (
  <Card extra="!p-6 animate-pulse">
    <div className="flex flex-col md:flex-row gap-6">
      <div className="w-full md:w-80 h-48 bg-gray-200 dark:bg-navy-700 rounded-xl" />
      <div className="flex-1 space-y-3">
        <div className="h-8 w-3/4 bg-gray-200 dark:bg-navy-700 rounded" />
        <div className="h-5 w-1/2 bg-gray-200 dark:bg-navy-700 rounded" />
        <div className="h-4 w-full bg-gray-200 dark:bg-navy-700 rounded" />
        <div className="h-4 w-2/3 bg-gray-200 dark:bg-navy-700 rounded" />
        <div className="flex gap-4 mt-4">
          <div className="h-10 w-32 bg-gray-200 dark:bg-navy-700 rounded-lg" />
        </div>
      </div>
    </div>
  </Card>
);

/**
 * Comment card component (read-only for public videos)
 */
const CommentCard = ({ 
  comment, 
  scanResult
}: { 
  comment?: CommentInfo;
  scanResult?: ScanResultResponse;
}) => {
  const displayComment = comment || (scanResult ? {
    id: scanResult.comment_id,
    text: scanResult.comment_text,
    author_name: scanResult.author_name || 'Unknown',
    author_avatar: null,
    like_count: 0,
    published_at: ''
  } : null);

  if (!displayComment) return null;

  const isGambling = scanResult?.is_gambling ?? false;
  const confidence = scanResult?.confidence ?? 0;

  return (
    <Card extra={`!p-4 ${isGambling ? 'border-l-4 border-red-500' : ''}`}>
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {displayComment.author_avatar ? (
            <Image
              src={displayComment.author_avatar}
              alt={displayComment.author_name}
              width={40}
              height={40}
              className="rounded-full"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-navy-700 flex items-center justify-center">
              <span className="text-sm font-bold text-gray-500 dark:text-gray-400">
                {displayComment.author_name.charAt(0).toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-navy-700 dark:text-white text-sm">
              {displayComment.author_name}
            </span>
            {scanResult && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                isGambling 
                  ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' 
                  : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
              }`}>
                {isGambling ? 'Gambling' : 'Clean'} ({(confidence * 100).toFixed(0)}%)
              </span>
            )}
          </div>
          <p className="text-gray-600 dark:text-gray-300 text-sm whitespace-pre-wrap break-words">
            {displayComment.text}
          </p>
        </div>
      </div>
    </Card>
  );
};


const BrowseVideoDetailPage = () => {
  const params = useParams();
  const router = useRouter();
  const videoId = params.videoId as string;

  const [video, setVideo] = useState<VideoInfo | null>(null);
  const [comments, setComments] = useState<CommentInfo[]>([]);
  const [scanResult, setScanResult] = useState<ScanDetailResponse | null>(null);
  const [isLoadingVideo, setIsLoadingVideo] = useState(true);
  const [isLoadingComments, setIsLoadingComments] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showScanFlow, setShowScanFlow] = useState(false);

  /**
   * Fetch video details
   * Requirements: 5.2
   */
  const fetchVideo = useCallback(async () => {
    setIsLoadingVideo(true);
    setError(null);
    try {
      const data = await api.youtube.video(videoId);
      setVideo(data);
    } catch (err) {
      console.error('Failed to fetch video:', err);
      setError('Failed to load video details.');
    } finally {
      setIsLoadingVideo(false);
    }
  }, [videoId]);

  /**
   * Fetch video comments
   */
  const fetchComments = useCallback(async () => {
    setIsLoadingComments(true);
    try {
      const data = await api.youtube.comments(videoId);
      setComments(data.items);
    } catch (err) {
      console.error('Failed to fetch comments:', err);
    } finally {
      setIsLoadingComments(false);
    }
  }, [videoId]);

  useEffect(() => {
    fetchVideo();
    fetchComments();
  }, [fetchVideo, fetchComments]);

  /**
   * Handle scan completion
   */
  const handleScanComplete = (result: ScanDetailResponse) => {
    setScanResult(result);
  };

  /**
   * Handle scan error
   */
  const handleScanError = (errorMsg: string) => {
    setError(errorMsg);
  };

  /**
   * Export scan results
   */
  const handleExport = (format: 'csv' | 'json') => {
    if (!scanResult) return;
    
    const url = format === 'csv' 
      ? api.dashboard.exportCsv(scanResult.id)
      : api.dashboard.exportJson(scanResult.id);
    
    window.open(url, '_blank');
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  return (
    <div className="mt-3">
      {/* Back Button */}
      <button
        onClick={() => router.push('/admin/browse')}
        className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-navy-700 dark:hover:text-white mb-4 transition-colors"
      >
        <MdArrowBack className="h-5 w-5" />
        Back to Browse
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

      {/* Public Video Notice */}
      <Card extra="!p-4 mb-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
        <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400">
          <MdInfo className="h-5 w-5 flex-shrink-0" />
          <span className="text-sm">
            This is a public video. You can scan for gambling comments, but comment deletion is only available for videos on your own channel.
          </span>
        </div>
      </Card>

      {/* Video Info */}
      {isLoadingVideo ? (
        <VideoInfoSkeleton />
      ) : video ? (
        <Card extra="!p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* Thumbnail */}
            <div className="relative w-full md:w-80 h-48 rounded-xl overflow-hidden flex-shrink-0">
              <Image
                src={video.thumbnail_url}
                alt={video.title}
                fill
                className="object-cover"
                sizes="(max-width: 768px) 100vw, 320px"
              />
              <a 
                href={`https://youtube.com/watch?v=${video.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 hover:opacity-100 transition-opacity"
              >
                <MdPlayCircle className="h-16 w-16 text-white" />
              </a>
            </div>

            {/* Info */}
            <div className="flex-1">
              <h1 className="text-xl font-bold text-navy-700 dark:text-white mb-2">
                {video.title}
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                {video.channel_name}
              </p>
              
              {video.description && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4 line-clamp-3">
                  {video.description}
                </p>
              )}

              {/* Stats */}
              <div className="flex flex-wrap gap-4 text-sm text-gray-500 dark:text-gray-400 mb-4">
                <div className="flex items-center gap-1">
                  <MdVisibility className="h-4 w-4" />
                  <span>{formatNumber(video.view_count)} views</span>
                </div>
                <div className="flex items-center gap-1">
                  <MdComment className="h-4 w-4" />
                  <span>{formatNumber(video.comment_count)} comments</span>
                </div>
                <span>Published {formatDate(video.published_at)}</span>
              </div>

              {/* Actions */}
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => setShowScanFlow(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors"
                >
                  <MdSearch className="h-5 w-5" />
                  Scan for Gambling Comments
                </button>

                {scanResult && (
                  <>
                    <button
                      onClick={() => handleExport('csv')}
                      className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-navy-700 text-navy-700 dark:text-white rounded-lg hover:bg-gray-200 dark:hover:bg-navy-600 transition-colors"
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
                  </>
                )}
              </div>
            </div>
          </div>
        </Card>
      ) : null}

      {/* Scan Flow */}
      {showScanFlow && (
        <div className="mb-6">
          <ScanFlow
            videoId={videoId}
            videoTitle={video?.title}
            isOwnVideo={false}
            onComplete={handleScanComplete}
            onError={handleScanError}
          />
        </div>
      )}

      {/* Scan Results */}
      {scanResult && (
        <Card extra="!p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-navy-700 dark:text-white">
                Scan Results
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {scanResult.total_comments} comments analyzed
              </p>
            </div>
            
            {/* Stats */}
            <div className="flex gap-4">
              <div className="flex items-center gap-2 px-3 py-1 bg-red-100 dark:bg-red-900/30 rounded-lg">
                <MdWarning className="h-5 w-5 text-red-500" />
                <span className="text-red-700 dark:text-red-400 font-semibold">
                  {scanResult.gambling_count} Gambling
                </span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <MdCheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-green-700 dark:text-green-400 font-semibold">
                  {scanResult.clean_count} Clean
                </span>
              </div>
            </div>
          </div>

          {/* Info about no delete for public videos */}
          {scanResult.gambling_count > 0 && (
            <div className="mb-4 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
              <div className="flex items-start gap-2">
                <MdInfo className="h-5 w-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-amber-700 dark:text-amber-400">
                    {scanResult.gambling_count} gambling comment{scanResult.gambling_count !== 1 ? 's' : ''} detected
                  </p>
                  <p className="text-sm text-amber-600 dark:text-amber-400/80">
                    Comment deletion is only available for videos on your own channel. 
                    Visit &quot;My Videos&quot; to manage comments on your videos.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Results List */}
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {scanResult.results
              .sort((a, b) => (b.is_gambling ? 1 : 0) - (a.is_gambling ? 1 : 0))
              .map((result) => (
                <CommentCard
                  key={result.id}
                  scanResult={result}
                />
              ))}
          </div>
        </Card>
      )}

      {/* Comments Section (before scan) */}
      {!scanResult && (
        <Card extra="!p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-navy-700 dark:text-white">
              Comments
            </h2>
            <button
              onClick={fetchComments}
              disabled={isLoadingComments}
              className="flex items-center gap-1 text-sm text-gray-500 hover:text-navy-700 dark:hover:text-white transition-colors"
            >
              <MdRefresh className={`h-4 w-4 ${isLoadingComments ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {isLoadingComments ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Card key={i} extra="!p-4 animate-pulse">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-navy-700" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 w-24 bg-gray-200 dark:bg-navy-700 rounded" />
                      <div className="h-4 w-full bg-gray-200 dark:bg-navy-700 rounded" />
                      <div className="h-4 w-2/3 bg-gray-200 dark:bg-navy-700 rounded" />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : comments.length === 0 ? (
            <div className="text-center py-8">
              <MdComment className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
              <p className="text-gray-500 dark:text-gray-400">No comments found</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {comments.map((comment) => (
                <CommentCard key={comment.id} comment={comment} />
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default BrowseVideoDetailPage;
