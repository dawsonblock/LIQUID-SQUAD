import React, { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import { toast } from 'react-hot-toast';
import { 
  Save, 
  RefreshCw, 
  Server, 
  Shield, 
  Palette, 
  Database,
  Activity,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import Layout from '@/components/Layout';
import TraceTable from '@/components/TraceTable';
import { createAPI, getAPI, TraceEntry } from '@/lib/api';
import { 
  getStoredSettings, 
  setStoredSettings, 
  getStoredAuthToken, 
  setStoredAuthToken,
  toggleDarkMode,
  isDarkMode
} from '@/lib/utils';

interface Settings {
  apiUrl: string;
  authToken: string;
  autoRefresh: boolean;
  refreshInterval: number;
  theme: 'light' | 'dark' | 'system';
}

export default function Settings() {
  const [modelTier, setModelTier] = useState('auto');
  const [retrievalMode, setRetrievalMode] = useState('disabled');
  const [criticEnabled, setCriticEnabled] = useState(true);
  const [settings, setSettings] = useState<Settings>({
    apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    authToken: '',
    autoRefresh: true,
    refreshInterval: 10,
    theme: 'system',
  });
  const [connectionStatus, setConnectionStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [traces, setTraces] = useState<TraceEntry[]>([]);
  const [isLoadingTraces, setIsLoadingTraces] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    // Load saved settings
    const savedSettings = getStoredSettings();
    const savedToken = getStoredAuthToken();
    
    setSettings(prev => ({
      ...prev,
      ...savedSettings,
      authToken: savedToken || prev.authToken,
      theme: isDarkMode() ? 'dark' : 'light',
    }));
  }, []);

  const checkConnection = useCallback(async (): Promise<'connected' | 'error'> => {
    setConnectionStatus('checking');
    try {
      const baseURL = settings.apiUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      createAPI({
        baseURL,
        authToken: settings.authToken || undefined,
      });
      const api = getAPI();
      await api.health();
      setConnectionStatus('connected');
      return 'connected';
    } catch (error) {
      console.error('Connection check failed:', error);
      setConnectionStatus('error');
      return 'error';
    }
  }, [settings.apiUrl, settings.authToken]);

  useEffect(() => {
    checkConnection();
  }, [checkConnection]);

  const handleSettingChange = (key: keyof Settings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setHasUnsavedChanges(true);
  };

  const handleSaveSettings = () => {
    // Save to localStorage
    const { authToken, ...otherSettings } = settings;
    setStoredSettings(otherSettings);
    setStoredAuthToken(authToken);
    
    // Apply theme
    if (settings.theme === 'dark' && !isDarkMode()) {
      toggleDarkMode();
    } else if (settings.theme === 'light' && isDarkMode()) {
      toggleDarkMode();
    }
    
    setHasUnsavedChanges(false);
    toast.success('Settings saved successfully!');
  };

  const handleTestConnection = async () => {
    const status = await checkConnection();
    if (status === 'connected') {
      toast.success('Connection successful!');
    } else {
      toast.error('Connection failed. Please check your settings.');
    }
  };

  const fetchTraces = async () => {
    setIsLoadingTraces(true);
    try {
      const api = getAPI();
      const traceData = await api.getTraces();
      setTraces(traceData);
    } catch (error) {
      console.error('Error fetching traces:', error);
      toast.error('Failed to fetch traces');
    } finally {
      setIsLoadingTraces(false);
    }
  };

  useEffect(() => {
    fetchTraces();
  }, []);

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'checking':
        return <RefreshCw className="h-4 w-4 animate-spin text-yellow-500" />;
      case 'connected':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'checking':
        return 'Checking connection...';
      case 'connected':
        return 'Connected';
      case 'error':
        return 'Connection failed';
    }
  };

  return (
    <>
      <Head>
        <title>Settings - LIQUID-SQUAD</title>
        <meta name="description" content="Configure LIQUID-SQUAD settings and view system traces" />
      </Head>

      <Layout
        modelTier={modelTier}
        onModelTierChange={setModelTier}
        retrievalMode={retrievalMode}
        onRetrievalModeChange={setRetrievalMode}
        criticEnabled={criticEnabled}
        onCriticToggle={setCriticEnabled}
      >
        <div className="p-6 max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Settings
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Configure your LIQUID-SQUAD instance and view system traces
              </p>
            </div>
            
            {hasUnsavedChanges && (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-yellow-600 dark:text-yellow-400">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm">Unsaved changes</span>
                </div>
                <button
                  onClick={handleSaveSettings}
                  className="btn-primary flex items-center space-x-2"
                >
                  <Save className="h-4 w-4" />
                  <span>Save Settings</span>
                </button>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Settings Panel */}
            <div className="lg:col-span-1 space-y-6">
              {/* Connection Settings */}
              <div className="card">
                <div className="flex items-center space-x-2 mb-4">
                  <Server className="h-5 w-5 text-primary-600" />
                  <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                    Connection
                  </h2>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      API URL
                    </label>
                    <input
                      type="url"
                      value={settings.apiUrl}
                      onChange={(e) => handleSettingChange('apiUrl', e.target.value)}
                      className="input-field"
                      placeholder="http://localhost:8000"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Auth Token
                    </label>
                    <input
                      type="password"
                      value={settings.authToken}
                      onChange={(e) => handleSettingChange('authToken', e.target.value)}
                      className="input-field"
                      placeholder="Enter your auth token..."
                    />
                  </div>
                  
                  <div className="flex items-center justify-between pt-2">
                    <div className="flex items-center space-x-2">
                      {getConnectionStatusIcon()}
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {getConnectionStatusText()}
                      </span>
                    </div>
                    <button
                      onClick={handleTestConnection}
                      className="btn-secondary text-sm"
                    >
                      Test Connection
                    </button>
                  </div>
                </div>
              </div>

              {/* Authentication Settings */}
              <div className="card">
                <div className="flex items-center space-x-2 mb-4">
                  <Shield className="h-5 w-5 text-primary-600" />
                  <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                    Security
                  </h2>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Auto-refresh metrics
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Automatically refresh dashboard data
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.autoRefresh}
                        onChange={(e) => handleSettingChange('autoRefresh', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                  
                  {settings.autoRefresh && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Refresh Interval (seconds)
                      </label>
                      <input
                        type="number"
                        min="5"
                        max="300"
                        value={settings.refreshInterval}
                        onChange={(e) => handleSettingChange('refreshInterval', parseInt(e.target.value))}
                        className="input-field"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Appearance Settings */}
              <div className="card">
                <div className="flex items-center space-x-2 mb-4">
                  <Palette className="h-5 w-5 text-primary-600" />
                  <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                    Appearance
                  </h2>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Theme
                    </label>
                    <select
                      value={settings.theme}
                      onChange={(e) => handleSettingChange('theme', e.target.value)}
                      className="input-field"
                    >
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                      <option value="system">System</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Traces Panel */}
            <div className="lg:col-span-2">
              <div className="flex items-center space-x-2 mb-6">
                <Activity className="h-5 w-5 text-primary-600" />
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                  Recent Traces
                </h2>
              </div>
              
              <TraceTable
                traces={traces}
                isLoading={isLoadingTraces}
                onRefresh={fetchTraces}
              />
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
