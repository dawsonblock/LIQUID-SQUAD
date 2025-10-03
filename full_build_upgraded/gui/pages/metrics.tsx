import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { toast } from 'react-hot-toast';
import { RefreshCw, Activity, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import Layout from '@/components/Layout';
import MetricsChart from '@/components/MetricsChart';
import { getAPI, parsePrometheusMetrics } from '@/lib/api';
import { formatDuration } from '@/lib/utils';

interface MetricsSummary {
  totalRequests: number;
  successRate: number;
  averageLatency: number;
  errorRate: number;
}

export default function Metrics() {
  const [modelTier, setModelTier] = useState('auto');
  const [retrievalMode, setRetrievalMode] = useState('disabled');
  const [criticEnabled, setCriticEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [summary, setSummary] = useState<MetricsSummary>({
    totalRequests: 0,
    successRate: 0,
    averageLatency: 0,
    errorRate: 0,
  });
  const [chartData, setChartData] = useState({
    requests: {
      labels: [],
      datasets: [],
    },
    latency: {
      labels: [],
      datasets: [],
    },
    errors: {
      labels: [],
      datasets: [],
    },
    modelTiers: {
      labels: [],
      datasets: [],
    },
  });

  const fetchMetrics = async () => {
    setIsLoading(true);
    try {
      const api = getAPI();
      const metricsText = await api.metrics();
      const metrics = parsePrometheusMetrics(metricsText);
      
      // Process metrics and update state
      processMetrics(metrics);
      setLastUpdated(new Date());
      
    } catch (error: any) {
      console.error('Error fetching metrics:', error);
      toast.error('Failed to fetch metrics');
    } finally {
      setIsLoading(false);
    }
  };

  const processMetrics = (metrics: Record<string, any>) => {
    // Generate mock data for demonstration
    // In a real implementation, this would process actual Prometheus metrics
    
    const now = new Date();
    const labels = Array.from({ length: 12 }, (_, i) => {
      const date = new Date(now.getTime() - (11 - i) * 5 * 60 * 1000);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });

    const requestCounts = Array.from({ length: 12 }, () => Math.floor(Math.random() * 50) + 10);
    const latencies = Array.from({ length: 12 }, () => Math.floor(Math.random() * 2000) + 100);
    const errorCounts = Array.from({ length: 12 }, () => Math.floor(Math.random() * 5));

    // Update summary
    const totalRequests = requestCounts.reduce((sum, count) => sum + count, 0);
    const totalErrors = errorCounts.reduce((sum, count) => sum + count, 0);
    const avgLatency = latencies.reduce((sum, lat) => sum + lat, 0) / latencies.length;

    setSummary({
      totalRequests,
      successRate: totalRequests > 0 ? ((totalRequests - totalErrors) / totalRequests) * 100 : 0,
      averageLatency: avgLatency,
      errorRate: totalRequests > 0 ? (totalErrors / totalRequests) * 100 : 0,
    });

    // Update chart data
    setChartData({
      requests: {
        labels,
        datasets: [
          {
            label: 'Requests per 5min',
            data: requestCounts,
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4,
          },
        ],
      },
      latency: {
        labels,
        datasets: [
          {
            label: 'Average Latency (ms)',
            data: latencies,
            backgroundColor: 'rgba(16, 185, 129, 0.8)',
            borderColor: 'rgb(16, 185, 129)',
            borderWidth: 1,
          },
        ],
      },
      errors: {
        labels: ['Success', 'Client Error', 'Server Error', 'Timeout'],
        datasets: [
          {
            data: [totalRequests - totalErrors, Math.floor(totalErrors * 0.6), Math.floor(totalErrors * 0.3), Math.floor(totalErrors * 0.1)],
            backgroundColor: [
              'rgba(16, 185, 129, 0.8)',
              'rgba(245, 158, 11, 0.8)',
              'rgba(239, 68, 68, 0.8)',
              'rgba(107, 114, 128, 0.8)',
            ],
            borderWidth: 0,
          },
        ],
      },
      modelTiers: {
        labels: ['Small', 'Medium', 'Large', 'Auto'],
        datasets: [
          {
            data: [30, 25, 20, 25],
            backgroundColor: [
              'rgba(59, 130, 246, 0.8)',
              'rgba(16, 185, 129, 0.8)',
              'rgba(245, 158, 11, 0.8)',
              'rgba(139, 92, 246, 0.8)',
            ],
            borderWidth: 0,
          },
        ],
      },
    });
  };

  useEffect(() => {
    fetchMetrics();
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  const summaryCards = [
    {
      title: 'Total Requests',
      value: summary.totalRequests.toLocaleString(),
      icon: Activity,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    },
    {
      title: 'Success Rate',
      value: `${summary.successRate.toFixed(1)}%`,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
    },
    {
      title: 'Avg Latency',
      value: formatDuration(summary.averageLatency),
      icon: Clock,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
    },
    {
      title: 'Error Rate',
      value: `${summary.errorRate.toFixed(1)}%`,
      icon: AlertTriangle,
      color: 'text-red-600',
      bgColor: 'bg-red-50 dark:bg-red-900/20',
    },
  ];

  return (
    <>
      <Head>
        <title>Metrics Dashboard - LIQUID-SQUAD</title>
        <meta name="description" content="Real-time metrics and monitoring for LIQUID-SQUAD" />
      </Head>

      <Layout
        modelTier={modelTier}
        onModelTierChange={setModelTier}
        retrievalMode={retrievalMode}
        onRetrievalModeChange={setRetrievalMode}
        criticEnabled={criticEnabled}
        onCriticToggle={setCriticEnabled}
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Metrics Dashboard
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Real-time system performance and usage statistics
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {lastUpdated && (
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
              <button
                onClick={fetchMetrics}
                disabled={isLoading}
                className="btn-primary flex items-center space-x-2 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {summaryCards.map((card) => (
              <div
                key={card.title}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6"
              >
                <div className="flex items-center">
                  <div className={`p-3 rounded-lg ${card.bgColor}`}>
                    <card.icon className={`h-6 w-6 ${card.color}`} />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      {card.title}
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {card.value}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <MetricsChart
              title="Request Volume Over Time"
              type="line"
              data={chartData.requests}
            />
            
            <MetricsChart
              title="Response Latency"
              type="bar"
              data={chartData.latency}
            />
            
            <MetricsChart
              title="Response Status Distribution"
              type="doughnut"
              data={chartData.errors}
            />
            
            <MetricsChart
              title="Model Tier Usage"
              type="doughnut"
              data={chartData.modelTiers}
            />
          </div>
        </div>
      </Layout>
    </>
  );
}