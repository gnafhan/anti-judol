'use client';

/**
 * Dashboard Page - Gambling Comment Detector
 * 
 * Displays statistics, charts, and filters for scan data.
 * Requirements: 7.1, 7.2
 */

import { useEffect, useState, useCallback, useMemo } from 'react';
import { MdBarChart, MdOutlineSearch, MdWarning, MdCheckCircle, MdFilterList, MdClose, MdSearch, MdChevronLeft, MdChevronRight } from 'react-icons/md';
import { IoDocuments } from 'react-icons/io5';
import Image from 'next/image';

import Widget from 'components/widget/Widget';
import Card from 'components/card';
import LineChart from 'components/charts/LineChart';
import PieChart from 'components/charts/PieChart';
import BarChart from 'components/charts/BarChart';
import ModelMetricsCard from 'components/dashboard/ModelMetricsCard';
import ModelImprovementNotification from 'components/dashboard/ModelImprovementNotification';
import ValidationContributionCard from 'components/dashboard/ValidationContributionCard';
import { api } from 'lib/api';
import type { DashboardStats, ChartData, ChartDataPoint } from 'lib/types';

interface ScannedVideo {
  video_id: string;
  video_title: string | null;
  video_thumbnail: string | null;
  channel_name: string | null;
  scan_count: number;
  last_scanned: string | null;
  is_own_video?: boolean;
}

interface TopVideo {
  video_id: string;
  video_title: string | null;
  video_thumbnail: string | null;
  channel_name: string | null;
  gambling_count: number;
  clean_count: number;
  total_comments: number;
  detection_rate: number;
}

const WidgetSkeleton = () => (
  <Card extra="!flex-row flex-grow items-center rounded-[20px] animate-pulse">
    <div className="ml-[18px] flex h-[90px] w-auto flex-row items-center">
      <div className="rounded-full bg-gray-200 dark:bg-navy-700 p-3 h-12 w-12" />
    </div>
    <div className="h-50 ml-4 flex w-auto flex-col justify-center gap-2">
      <div className="h-4 w-24 bg-gray-200 dark:bg-navy-700 rounded" />
      <div className="h-6 w-16 bg-gray-200 dark:bg-navy-700 rounded" />
    </div>
  </Card>
);

const ChartSkeleton = () => (
  <Card extra="!p-[20px] text-center animate-pulse">
    <div className="flex justify-between mb-4">
      <div className="h-8 w-32 bg-gray-200 dark:bg-navy-700 rounded" />
    </div>
    <div className="h-[300px] w-full bg-gray-200 dark:bg-navy-700 rounded" />
  </Card>
);

const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [scannedVideos, setScannedVideos] = useState<ScannedVideo[]>([]);
  const [topVideos, setTopVideos] = useState<TopVideo[]>([]);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [isLoadingChart, setIsLoadingChart] = useState(true);
  const [isLoadingVideos, setIsLoadingVideos] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [chartError, setChartError] = useState<string | null>(null);
  
  // Filter state
  const [selectedVideoIds, setSelectedVideoIds] = useState<string[]>([]);
  const [chartDays, setChartDays] = useState(30);
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [sourceFilter, setSourceFilter] = useState<'all' | 'my_videos' | 'public'>('all');
  const [videoSearch, setVideoSearch] = useState('');
  const [videoPage, setVideoPage] = useState(1);
  const videosPerPage = 3;

  const fetchScannedVideos = useCallback(async () => {
    setIsLoadingVideos(true);
    try {
      const data = await api.dashboard.scannedVideos(sourceFilter);
      setScannedVideos(data.videos);
    } catch (error) {
      console.error('Failed to fetch scanned videos:', error);
    } finally {
      setIsLoadingVideos(false);
    }
  }, [sourceFilter]);

  const fetchStats = useCallback(async () => {
    setIsLoadingStats(true);
    setStatsError(null);
    try {
      const data = await api.dashboard.stats(
        selectedVideoIds.length > 0 ? selectedVideoIds : undefined,
        sourceFilter
      );
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      setStatsError('Failed to load statistics.');
    } finally {
      setIsLoadingStats(false);
    }
  }, [selectedVideoIds, sourceFilter]);

  const fetchChartData = useCallback(async () => {
    setIsLoadingChart(true);
    setChartError(null);
    try {
      const data = await api.dashboard.chartData(
        selectedVideoIds.length > 0 ? selectedVideoIds : undefined,
        sourceFilter,
        chartDays
      );
      setChartData(data);
    } catch (error) {
      console.error('Failed to fetch chart data:', error);
      setChartError('Failed to load chart data.');
    } finally {
      setIsLoadingChart(false);
    }
  }, [selectedVideoIds, sourceFilter, chartDays]);

  const fetchTopVideos = useCallback(async () => {
    try {
      const data = await api.dashboard.topVideos(
        selectedVideoIds.length > 0 ? selectedVideoIds : undefined,
        sourceFilter,
        10
      );
      setTopVideos(data.videos);
    } catch (error) {
      console.error('Failed to fetch top videos:', error);
    }
  }, [selectedVideoIds, sourceFilter]);

  useEffect(() => {
    fetchScannedVideos();
  }, [fetchScannedVideos]);

  useEffect(() => {
    fetchStats();
    fetchChartData();
    fetchTopVideos();
  }, [fetchStats, fetchChartData, fetchTopVideos]);

  const formatDetectionRate = (rate: number | undefined | null): string => {
    if (rate === undefined || rate === null) return '0%';
    return `${(rate * 100).toFixed(1)}%`;
  };

  const formatNumber = (num: number | undefined | null): string => {
    if (num === undefined || num === null) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const toggleVideoFilter = (videoId: string) => {
    setSelectedVideoIds(prev => 
      prev.includes(videoId) 
        ? prev.filter(id => id !== videoId)
        : [...prev, videoId]
    );
  };

  const clearFilters = () => {
    setSelectedVideoIds([]);
    setSourceFilter('all');
  };

  // Clear selected videos when source filter changes
  useEffect(() => {
    setSelectedVideoIds([]);
    setVideoPage(1);
  }, [sourceFilter]);

  // Filter videos based on source and search
  const filteredVideos = useMemo(() => {
    let videos = scannedVideos;
    
    // Filter by source (for now using is_own_video flag if available)
    if (sourceFilter === 'my_videos') {
      videos = videos.filter(v => v.is_own_video === true);
    } else if (sourceFilter === 'public') {
      videos = videos.filter(v => v.is_own_video === false || v.is_own_video === undefined);
    }
    
    // Filter by search
    if (videoSearch.trim()) {
      const search = videoSearch.toLowerCase();
      videos = videos.filter(v => 
        v.video_title?.toLowerCase().includes(search) ||
        v.channel_name?.toLowerCase().includes(search) ||
        v.video_id.toLowerCase().includes(search)
      );
    }
    
    return videos;
  }, [scannedVideos, sourceFilter, videoSearch]);

  // Paginated videos
  const paginatedVideos = useMemo(() => {
    const start = (videoPage - 1) * videosPerPage;
    return filteredVideos.slice(start, start + videosPerPage);
  }, [filteredVideos, videoPage]);

  const totalVideoPages = Math.ceil(filteredVideos.length / videosPerPage);

  // Reset page when filters change
  useEffect(() => {
    setVideoPage(1);
  }, [videoSearch, sourceFilter]);

  // Filter chart data to only show from first day with activity
  const getFilteredChartData = (data: ChartDataPoint[]): ChartDataPoint[] => {
    // Find first index with any activity
    const firstActiveIndex = data.findIndex(d => d.gambling_count > 0 || d.clean_count > 0 || d.scans > 0);
    if (firstActiveIndex === -1) return [];
    // Return data from first active day onwards
    return data.slice(firstActiveIndex);
  };

  const prepareLineChartData = (data: ChartDataPoint[]) => {
    const filtered = getFilteredChartData(data);
    return [
      { name: 'Gambling', data: filtered.map(d => d.gambling_count), color: '#F56565' },
      { name: 'Clean', data: filtered.map(d => d.clean_count), color: '#48BB78' },
    ];
  };

  const prepareLineChartOptions = (data: ChartDataPoint[]) => {
    const filtered = getFilteredChartData(data);
    return {
      legend: { show: true, position: 'top' as const, horizontalAlign: 'right' as const },
      chart: { type: 'line' as const, toolbar: { show: false } },
      dataLabels: { enabled: false },
      stroke: { curve: 'smooth' as const, width: 3 },
      tooltip: { style: { fontSize: '12px' }, theme: 'dark' },
      grid: { show: true, borderColor: '#E2E8F0', strokeDashArray: 5 },
      xaxis: {
        labels: { style: { colors: '#A3AED0', fontSize: '12px' }, rotate: -45 },
        categories: filtered.map(d => {
          const date = new Date(d.date);
          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }),
      },
      yaxis: { labels: { style: { colors: '#A3AED0', fontSize: '12px' } } },
    };
  };

  const preparePieChartData = () => {
    if (!stats) return [0, 0];
    return [stats.gambling_comments || 0, stats.clean_comments || 0];
  };

  const pieChartOptions = {
    labels: ['Gambling', 'Clean'],
    colors: ['#F56565', '#48BB78'],
    chart: { type: 'donut' as const },
    legend: { position: 'bottom' as const },
    dataLabels: { enabled: true },
    plotOptions: { pie: { donut: { size: '65%' } } },
  };

  const prepareBarChartData = () => [{
    name: 'Gambling Comments',
    data: topVideos.slice(0, 5).map(v => v.gambling_count),
    color: '#F56565',
  }];

  const barChartOptions = {
    chart: { type: 'bar' as const, toolbar: { show: false } },
    plotOptions: { bar: { horizontal: true, borderRadius: 4 } },
    dataLabels: { enabled: false },
    xaxis: {
      categories: topVideos.slice(0, 5).map(v => 
        (v.video_title || 'Unknown').substring(0, 20) + ((v.video_title?.length || 0) > 20 ? '...' : '')
      ),
      labels: { style: { colors: '#A3AED0', fontSize: '12px' } },
    },
    yaxis: { labels: { style: { colors: '#A3AED0', fontSize: '12px' } } },
    grid: { borderColor: '#E2E8F0' },
  };

  return (
    <div>
      {/* Model Improvement Notification - Requirements: 10.2 */}
      {/* <ModelImprovementNotification className="mb-4" /> */}

      {/* Source Switch */}
      <Card extra="!p-4 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-navy-700 dark:text-white mr-2">Source:</span>
            <div className="flex bg-gray-100 dark:bg-navy-700 rounded-lg p-1">
              <button
                onClick={() => setSourceFilter('all')}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  sourceFilter === 'all'
                    ? 'bg-white dark:bg-navy-600 text-brand-500 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-navy-700 dark:hover:text-white'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setSourceFilter('my_videos')}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  sourceFilter === 'my_videos'
                    ? 'bg-white dark:bg-navy-600 text-brand-500 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-navy-700 dark:hover:text-white'
                }`}
              >
                My Videos
              </button>
              <button
                onClick={() => setSourceFilter('public')}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  sourceFilter === 'public'
                    ? 'bg-white dark:bg-navy-600 text-brand-500 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-navy-700 dark:hover:text-white'
                }`}
              >
                Public
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* Filter Bar */}
      <Card extra="!p-4 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFilterPanel(!showFilterPanel)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                showFilterPanel || selectedVideoIds.length > 0
                  ? 'bg-brand-500 text-white'
                  : 'bg-gray-100 dark:bg-navy-700 text-navy-700 dark:text-white'
              }`}
            >
              <MdFilterList className="h-5 w-5" />
              Filter Videos
              {selectedVideoIds.length > 0 && (
                <span className="ml-1 px-2 py-0.5 bg-white/20 rounded-full text-xs">
                  {selectedVideoIds.length}
                </span>
              )}
            </button>
            
            {(selectedVideoIds.length > 0 || sourceFilter !== 'all') && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 px-3 py-2 text-sm text-gray-500 hover:text-red-500 transition-colors"
              >
                <MdClose className="h-4 w-4" />
                Clear All
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">Period:</span>
            <select
              value={chartDays}
              onChange={(e) => setChartDays(Number(e.target.value))}
              className="px-3 py-2 bg-gray-100 dark:bg-navy-700 rounded-lg text-sm text-navy-700 dark:text-white border-none focus:ring-2 focus:ring-brand-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
              <option value={60}>Last 60 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Filter Panel */}
      {showFilterPanel && (
        <Card extra="!p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-navy-700 dark:text-white">
              Filter by Scanned Videos
            </h3>
            <span className="text-xs text-gray-500">
              {filteredVideos.length} video{filteredVideos.length !== 1 ? 's' : ''} found
            </span>
          </div>
          
          {/* Search Box */}
          <div className="relative mb-4">
            <MdSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search videos by title, channel, or ID..."
              value={videoSearch}
              onChange={(e) => setVideoSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-navy-700 rounded-lg text-sm text-navy-700 dark:text-white placeholder-gray-400 border-none focus:ring-2 focus:ring-brand-500"
            />
            {videoSearch && (
              <button
                onClick={() => setVideoSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <MdClose className="h-4 w-4" />
              </button>
            )}
          </div>

          {isLoadingVideos ? (
            <div className="flex items-center gap-2 text-gray-500">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
              Loading videos...
            </div>
          ) : filteredVideos.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">
              {scannedVideos.length === 0 ? 'No scanned videos yet.' : 'No videos match your search.'}
            </p>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {paginatedVideos.map((video) => (
                  <button
                    key={video.video_id}
                    onClick={() => toggleVideoFilter(video.video_id)}
                    className={`flex items-center gap-3 p-3 rounded-lg border-2 transition-all text-left ${
                      selectedVideoIds.includes(video.video_id)
                        ? 'border-brand-500 bg-brand-50 dark:bg-brand-900/20'
                        : 'border-gray-200 dark:border-navy-600 hover:border-brand-300'
                    }`}
                  >
                    {video.video_thumbnail && (
                      <Image
                        src={video.video_thumbnail}
                        alt={video.video_title || 'Video'}
                        width={60}
                        height={40}
                        className="rounded object-cover"
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-navy-700 dark:text-white truncate">
                        {video.video_title || 'Unknown Video'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {video.channel_name} • {video.scan_count} scan{video.scan_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                    {selectedVideoIds.includes(video.video_id) && (
                      <MdCheckCircle className="h-5 w-5 text-brand-500 flex-shrink-0" />
                    )}
                  </button>
                ))}
              </div>

              {/* Pagination */}
              {totalVideoPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-4">
                  <button
                    onClick={() => setVideoPage(p => Math.max(1, p - 1))}
                    disabled={videoPage === 1}
                    className="p-1.5 rounded-lg bg-gray-100 dark:bg-navy-700 text-gray-600 dark:text-gray-400 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-navy-600 transition-colors"
                  >
                    <MdChevronLeft className="h-5 w-5" />
                  </button>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Page {videoPage} of {totalVideoPages}
                  </span>
                  <button
                    onClick={() => setVideoPage(p => Math.min(totalVideoPages, p + 1))}
                    disabled={videoPage === totalVideoPages}
                    className="p-1.5 rounded-lg bg-gray-100 dark:bg-navy-700 text-gray-600 dark:text-gray-400 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-navy-600 transition-colors"
                  >
                    <MdChevronRight className="h-5 w-5" />
                  </button>
                </div>
              )}
            </>
          )}
        </Card>
      )}

      {/* Stats Widgets */}
      <div className="mt-3 grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-4">
        {isLoadingStats ? (
          <>
            <WidgetSkeleton />
            <WidgetSkeleton />
            <WidgetSkeleton />
            <WidgetSkeleton />
          </>
        ) : statsError ? (
          <Card extra="col-span-full !p-4 text-center">
            <p className="text-red-500">{statsError}</p>
          </Card>
        ) : stats ? (
          <>
            <Widget
              icon={<IoDocuments className="h-6 w-6" />}
              title="Total Scans"
              subtitle={formatNumber(stats.total_scans)}
            />
            <Widget
              icon={<MdOutlineSearch className="h-7 w-7" />}
              title="Comments Analyzed"
              subtitle={formatNumber(stats.total_comments)}
            />
            <Widget
              icon={<MdWarning className="h-6 w-6" />}
              title="Gambling Comments"
              subtitle={formatNumber(stats.gambling_comments)}
            />
            <Widget
              icon={<MdCheckCircle className="h-6 w-6" />}
              title="Detection Rate"
              subtitle={formatDetectionRate(stats.detection_rate)}
            />
          </>
        ) : null}
      </div>

      {/* Charts Row */}
      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-3">
        {/* Line Chart - Trend over time */}
        <div className="lg:col-span-2">
          {isLoadingChart ? (
            <ChartSkeleton />
          ) : chartError ? (
            <Card extra="!p-[20px] text-center">
              <p className="text-red-500">{chartError}</p>
            </Card>
          ) : chartData && chartData.data && getFilteredChartData(chartData.data).length > 0 ? (
            <Card extra="!p-[20px]">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h4 className="text-lg font-bold text-navy-700 dark:text-white">
                    Comment Trend
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Gambling vs Clean comments over time
                  </p>
                </div>
              </div>
              <div className="h-[300px] w-full">
                <LineChart
                  chartOptions={prepareLineChartOptions(chartData.data)}
                  chartData={prepareLineChartData(chartData.data)}
                />
              </div>
            </Card>
          ) : (
            <Card extra="!p-[20px] text-center">
              <div className="flex flex-col items-center justify-center py-12">
                <MdBarChart className="h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" />
                <h4 className="text-lg font-bold text-navy-700 dark:text-white mb-2">
                  No Scan Data Yet
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Start scanning YouTube videos to see your statistics here.
                </p>
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: Pie Chart + Model Metrics */}
        <div className="flex flex-col gap-5 ">
          {/* Pie Chart - Distribution */}
          <div>
            {isLoadingStats ? (
              <ChartSkeleton />
            ) : stats && (stats.gambling_comments > 0 || stats.clean_comments > 0) ? (
              <Card extra="!p-[20px]">
                <h4 className="text-lg font-bold text-navy-700 dark:text-white mb-4">
                  Comment Distribution
                </h4>
                <div className="h-[200px] w-full flex items-center justify-center">
                  <PieChart
                    chartOptions={pieChartOptions}
                    chartData={preparePieChartData()}
                  />
                </div>
              </Card>
            ) : (
              <Card extra="!p-[20px] text-center">
                <div className="flex flex-col items-center justify-center py-8">
                  <MdBarChart className="h-12 w-12 text-gray-300 dark:text-gray-600 mb-4" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    No data to display
                  </p>
                </div>
              </Card>
            )}
          </div>

          {/* Model Metrics Card - Requirements: 10.1 */}
          {/* <ModelMetricsCard /> */}
        </div>
      </div>

      {/* Validation Contributions Card - Requirements: 10.3 */}
      <div className="mt-5">
        {/* <ValidationContributionCard /> */}
      </div>

      {/* Top Videos Bar Chart */}
      {topVideos.length > 0 && (
        <div className="mt-5">
          <Card extra="!p-[20px]">
            <h4 className="text-lg font-bold text-navy-700 dark:text-white mb-4">
              Top Videos by Gambling Comments
            </h4>
            <div className="h-[300px] w-full">
              <BarChart
                chartOptions={barChartOptions}
                chartData={prepareBarChartData()}
              />
            </div>
          </Card>
        </div>
      )}

      {/* Top Videos Table */}
      {topVideos.length > 0 && (
        <div className="mt-5">
          <Card extra="!p-[20px]">
            <h4 className="text-lg font-bold text-navy-700 dark:text-white mb-4">
              Video Statistics
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-navy-600">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600 dark:text-gray-400">Video</th>
                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-600 dark:text-gray-400">Total</th>
                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-600 dark:text-gray-400">Gambling</th>
                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-600 dark:text-gray-400">Clean</th>
                    <th className="text-right py-3 px-4 text-sm font-semibold text-gray-600 dark:text-gray-400">Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {topVideos.map((video) => (
                    <tr key={video.video_id} className="border-b border-gray-100 dark:border-navy-700 hover:bg-gray-50 dark:hover:bg-navy-700/50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          {video.video_thumbnail && (
                            <Image
                              src={video.video_thumbnail}
                              alt={video.video_title || 'Video'}
                              width={48}
                              height={32}
                              className="rounded object-cover"
                            />
                          )}
                          <div>
                            <p className="text-sm font-medium text-navy-700 dark:text-white truncate max-w-[200px]">
                              {video.video_title || 'Unknown'}
                            </p>
                            <p className="text-xs text-gray-500">{video.channel_name}</p>
                          </div>
                        </div>
                      </td>
                      <td className="text-right py-3 px-4 text-sm text-navy-700 dark:text-white">
                        {formatNumber(video.total_comments)}
                      </td>
                      <td className="text-right py-3 px-4">
                        <span className="text-sm font-medium text-red-500">
                          {formatNumber(video.gambling_count)}
                        </span>
                      </td>
                      <td className="text-right py-3 px-4">
                        <span className="text-sm font-medium text-green-500">
                          {formatNumber(video.clean_count)}
                        </span>
                      </td>
                      <td className="text-right py-3 px-4">
                        <span className={`text-sm font-medium ${
                          video.detection_rate > 0.1 ? 'text-red-500' : 'text-green-500'
                        }`}>
                          {formatDetectionRate(video.detection_rate)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
