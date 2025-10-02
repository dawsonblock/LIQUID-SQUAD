import React, { useState, useEffect } from 'react';
import { Search, Filter, ChevronLeft, ChevronRight, Clock, CheckCircle, XCircle } from 'lucide-react';
import { TraceEntry } from '@/lib/api';
import { formatTimestamp, formatDuration, truncateText, cn } from '@/lib/utils';

interface TraceTableProps {
  traces: TraceEntry[];
  isLoading: boolean;
  onRefresh: () => void;
}

export default function TraceTable({ traces, isLoading, onRefresh }: TraceTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'success' | 'error'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedTrace, setSelectedTrace] = useState<TraceEntry | null>(null);
  
  const itemsPerPage = 10;

  // Filter traces based on search and status
  const filteredTraces = traces.filter(trace => {
    const matchesSearch = trace.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         trace.answer.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || trace.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Paginate filtered traces
  const totalPages = Math.ceil(filteredTraces.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedTraces = filteredTraces.slice(startIndex, startIndex + itemsPerPage);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-700 bg-green-50 dark:text-green-400 dark:bg-green-900/20';
      case 'error':
        return 'text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-900/20';
      default:
        return 'text-gray-700 bg-gray-50 dark:text-gray-400 dark:bg-gray-900/20';
    }
  };

  const getModelTierColor = (tier: string) => {
    switch (tier) {
      case 'small':
        return 'text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20';
      case 'medium':
        return 'text-green-700 bg-green-50 dark:text-green-400 dark:bg-green-900/20';
      case 'large':
        return 'text-yellow-700 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20';
      case 'auto':
        return 'text-purple-700 bg-purple-50 dark:text-purple-400 dark:bg-purple-900/20';
      default:
        return 'text-gray-700 bg-gray-50 dark:text-gray-400 dark:bg-gray-900/20';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      {/* Header with filters */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Request Traces ({filteredTraces.length})
          </h3>
          
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search questions or answers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            
            {/* Status filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="pl-10 pr-8 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="all">All Status</option>
                <option value="success">Success</option>
                <option value="error">Error</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Question
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Model
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Retrieval
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Latency
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Time
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center">
                  <div className="flex items-center justify-center space-x-2">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
                    <span className="text-gray-500 dark:text-gray-400">Loading traces...</span>
                  </div>
                </td>
              </tr>
            ) : paginatedTraces.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                  No traces found matching your criteria.
                </td>
              </tr>
            ) : (
              paginatedTraces.map((trace) => (
                <tr
                  key={trace.id}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                  onClick={() => setSelectedTrace(trace)}
                >
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 dark:text-gray-100">
                      {truncateText(trace.question, 60)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(trace.status)}
                      <span className={cn(
                        'inline-flex px-2 py-1 text-xs font-medium rounded-full',
                        getStatusColor(trace.status)
                      )}>
                        {trace.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn(
                      'inline-flex px-2 py-1 text-xs font-medium rounded-full',
                      getModelTierColor(trace.model_tier)
                    )}>
                      {trace.model_tier}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-900 dark:text-gray-100">
                      {trace.retrieval_mode}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-900 dark:text-gray-100">
                      {formatDuration(trace.latency_ms)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {formatTimestamp(trace.timestamp)}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, filteredTraces.length)} of {filteredTraces.length} results
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Page {currentPage} of {totalPages}
            </span>
            
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Trace Detail Modal */}
      {selectedTrace && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={() => setSelectedTrace(null)}
            />
            
            <div className="inline-block w-full max-w-2xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white dark:bg-gray-800 shadow-xl rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Trace Details
                </h3>
                <button
                  onClick={() => setSelectedTrace(null)}
                  className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                >
                  <XCircle className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Question
                  </label>
                  <p className="text-sm text-gray-900 dark:text-gray-100 bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                    {selectedTrace.question}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Answer
                  </label>
                  <p className="text-sm text-gray-900 dark:text-gray-100 bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                    {selectedTrace.answer}
                  </p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Status
                    </label>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(selectedTrace.status)}
                      <span className={cn(
                        'inline-flex px-2 py-1 text-xs font-medium rounded-full',
                        getStatusColor(selectedTrace.status)
                      )}>
                        {selectedTrace.status}
                      </span>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Model Tier
                    </label>
                    <span className={cn(
                      'inline-flex px-2 py-1 text-xs font-medium rounded-full',
                      getModelTierColor(selectedTrace.model_tier)
                    )}>
                      {selectedTrace.model_tier}
                    </span>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Retrieval Mode
                    </label>
                    <span className="text-sm text-gray-900 dark:text-gray-100">
                      {selectedTrace.retrieval_mode}
                    </span>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Latency
                    </label>
                    <span className="text-sm text-gray-900 dark:text-gray-100">
                      {formatDuration(selectedTrace.latency_ms)}
                    </span>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Timestamp
                  </label>
                  <span className="text-sm text-gray-900 dark:text-gray-100">
                    {formatTimestamp(selectedTrace.timestamp)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}