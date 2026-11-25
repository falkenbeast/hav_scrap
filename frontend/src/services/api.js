import axios from 'axios';

// Resolve API base URL via environment variable with fallback
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://127.0.0.1:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Response Interceptor for centralized telemetry & error capture
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorDetails = {
      message:
        error.response?.data?.message ||
        error.response?.data?.detail ||
        error.message ||
        'API Communication Fault',
      status: error.response?.status,
      endpoint: error.config?.url,
      isNetworkError: !error.response,
    };
    console.warn('Backend API Telemetry Warning:', errorDetails);
    return Promise.reject(errorDetails);
  }
);

export const api = {
  // 1. Health Probe
  getHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // 2. Dashboard Statistics & Recent Activity
  getDashboardStats: async () => {
    const res = await apiClient.get('/dashboard/stats');
    return res.data;
  },
  getDashboardActivity: async (limit = 10) => {
    const res = await apiClient.get('/dashboard/activity', { params: { limit } });
    return res.data;
  },

  // 3. Companies Operations
  getCompanies: async (params = {}) => {
    const res = await apiClient.get('/companies', { params });
    return res.data;
  },
  getCompanyById: async (id) => {
    const res = await apiClient.get(`/companies/${id}`);
    return res.data;
  },

  // 4. Job Opportunities Operations
  getJobs: async (params = {}) => {
    const res = await apiClient.get('/jobs', { params });
    return res.data;
  },
  getJobById: async (id) => {
    const res = await apiClient.get(`/jobs/${id}`);
    return res.data;
  },

  // 5. Scraping Sessions History
  getSessions: async (params = {}) => {
    const res = await apiClient.get('/sessions', { params });
    return res.data;
  },
  getSessionById: async (sessionId) => {
    const res = await apiClient.get(`/sessions/${sessionId}`);
    return res.data;
  },

  // 6. System Status & Database Backups (Phase 11)
  getSystemStatus: async () => {
    const res = await apiClient.get('/system/status');
    return res.data;
  },
  triggerDatabaseBackup: async (tag = null) => {
    const res = await apiClient.post('/system/backup', null, { params: tag ? { tag } : {} });
    return res.data;
  },
  getDatabaseBackups: async () => {
    const res = await apiClient.get('/system/backups');
    return res.data;
  },

  // 7. Scraper Control Operations (Phase 4)
  startScraper: async () => {
    const res = await apiClient.post('/scraper/start');
    return res.data;
  },
  pauseScraper: async () => {
    const res = await apiClient.post('/scraper/pause');
    return res.data;
  },
  resumeScraper: async () => {
    const res = await apiClient.post('/scraper/resume');
    return res.data;
  },
  stopScraper: async () => {
    const res = await apiClient.post('/scraper/stop');
    return res.data;
  },
  getScraperStatus: async () => {
    const res = await apiClient.get('/scraper/status');
    return res.data;
  },
  getScraperLogs: async (limit = 50) => {
    const res = await apiClient.get('/scraper/logs', { params: { limit } });
    return res.data;
  },

  // EventSource URL for Server-Sent Events (SSE)
  getScraperEventsUrl: () => `${API_BASE_URL}/scraper/events`,

  // 8. Analytics & Salary Intelligence Endpoints (Phase 10)
  getAnalyticsOverview: async (params = {}) => {
    const res = await apiClient.get('/analytics/overview', { params });
    return res.data;
  },
  getCompanyRankings: async (params = {}) => {
    const res = await apiClient.get('/analytics/company-rankings', { params });
    return res.data;
  },
  getSalaryDistribution: async (params = {}) => {
    const res = await apiClient.get('/analytics/salary-distribution', { params });
    return res.data;
  },
  getOpportunityTrends: async (params = {}) => {
    const res = await apiClient.get('/analytics/opportunity-trends', { params });
    return res.data;
  },
  getLocationDistribution: async (params = {}) => {
    const res = await apiClient.get('/analytics/location-distribution', { params });
    return res.data;
  },
  getJobTypeDistribution: async (params = {}) => {
    const res = await apiClient.get('/analytics/job-type-distribution', { params });
    return res.data;
  },
  getEligibilityInsights: async (params = {}) => {
    const res = await apiClient.get('/analytics/eligibility-insights', { params });
    return res.data;
  },
  getSalaryIntelligence: async (params = {}) => {
    const res = await apiClient.get('/analytics/salary-intelligence', { params });
    return res.data;
  },
  getAnalyticsFilters: async () => {
    const res = await apiClient.get('/analytics/filters');
    return res.data;
  },
  getTopCompanies: async (limit = 8) => {
    const res = await apiClient.get('/analytics/top-companies', { params: { limit } });
    return res.data;
  },

  // 9. Haveloc Portal & Authentication Operations (Phase 5)
  getPortalStatus: async () => {
    const res = await apiClient.get('/portal/status');
    return res.data;
  },
  getPortalInfo: async () => {
    const res = await apiClient.get('/portal/info');
    return res.data;
  },
  connectPortal: async () => {
    const res = await apiClient.post('/portal/connect');
    return res.data;
  },
  reconnectPortal: async () => {
    const res = await apiClient.post('/portal/reconnect');
    return res.data;
  },
  disconnectPortal: async () => {
    const res = await apiClient.post('/portal/disconnect');
    return res.data;
  },

  // 10. Haveloc Listing Discovery Operations (Phase 6)
  startDiscovery: async () => {
    const res = await apiClient.post('/discovery/start');
    return res.data;
  },
  stopDiscovery: async () => {
    const res = await apiClient.post('/discovery/stop');
    return res.data;
  },
  getDiscoveryStatus: async () => {
    const res = await apiClient.get('/discovery/status');
    return res.data;
  },
  getDiscoveryStats: async () => {
    const res = await apiClient.get('/discovery/statistics');
    return res.data;
  },
  getDiscoveryResults: async (params = {}) => {
    const res = await apiClient.get('/discovery/results', { params });
    return res.data;
  },

  // 11. Deep Job Details & Salary Extraction Operations (Phase 7)
  startDetailExtraction: async (params = {}) => {
    const res = await apiClient.post('/extraction/details/start', null, { params });
    return res.data;
  },
  stopDetailExtraction: async () => {
    const res = await apiClient.post('/extraction/details/stop');
    return res.data;
  },
  getDetailExtractionStatus: async () => {
    const res = await apiClient.get('/extraction/details/status');
    return res.data;
  },
  getDetailExtractionResults: async (params = {}) => {
    const res = await apiClient.get('/extraction/details/results', { params });
    return res.data;
  },
  getJobSalaryDetails: async (jobId) => {
    const res = await apiClient.get(`/jobs/${jobId}/salary`);
    return res.data;
  },

  // 12. Data Cleaning, Normalization & Quality Pipeline (Phase 8)
  startProcessing: async () => {
    const res = await apiClient.post('/processing/start');
    return res.data;
  },
  getProcessingStatus: async () => {
    const res = await apiClient.get('/processing/status');
    return res.data;
  },
  getQualityReport: async () => {
    const res = await apiClient.get('/processing/quality-report');
    return res.data;
  },
  getReviewRecords: async (params = {}) => {
    const res = await apiClient.get('/processing/review-records', { params });
    return res.data;
  },
  getProcessingStatistics: async () => {
    const res = await apiClient.get('/processing/statistics');
    return res.data;
  },

  // 13. Excel Placement Deliverables & Export Center (Phase 9)
  generateExport: async (payload = {}) => {
    const res = await apiClient.post('/exports/generate', payload);
    return res.data;
  },
  getExports: async (params = {}) => {
    const res = await apiClient.get('/exports', { params });
    return res.data;
  },
  getExportById: async (exportId) => {
    const res = await apiClient.get(`/exports/${exportId}`);
    return res.data;
  },
  deleteExport: async (exportId) => {
    const res = await apiClient.delete(`/exports/${exportId}`);
    return res.data;
  },
  getExportDownloadUrl: (exportId) => `${API_BASE_URL}/exports/${exportId}/download`,
};

export default apiClient;
