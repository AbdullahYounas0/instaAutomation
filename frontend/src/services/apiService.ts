import axios, { AxiosRequestConfig } from 'axios';
import { authService } from './authService';
import { config } from '../config/config';

const API_BASE_URL = config.API_BASE_URL;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = authService.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Script management
  async startDailyPost(formData: FormData) {
    const response = await apiClient.post('/daily-post/start', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async startDMAutomation(formData: FormData) {
    const response = await apiClient.post('/dm-automation/start', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async startWarmup(formData: FormData) {
    const response = await apiClient.post('/warmup/start', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getScriptStatus(scriptId: string) {
    const response = await apiClient.get(`/script/${scriptId}/status`);
    return response.data;
  },

  async getScriptLogs(scriptId: string) {
    const response = await apiClient.get(`/script/${scriptId}/logs`);
    return response.data;
  },

  async stopScript(scriptId: string) {
    const response = await apiClient.post(`/script/${scriptId}/stop`);
    return response.data;
  },

  async listScripts() {
    const response = await apiClient.get('/scripts');
    return response.data;
  },

  async clearScriptLogs(scriptId: string) {
    const response = await apiClient.post(`/script/${scriptId}/clear-logs`);
    return response.data;
  },

  async downloadScriptLogs(scriptId: string) {
    const response = await apiClient.get(`/script/${scriptId}/download-logs`, {
      responseType: 'blob',
    });
    return response;
  },

  // Validation endpoints
  async validateDailyPostFiles(formData: FormData) {
    const response = await apiClient.post('/daily-post/validate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async validateDMAutomationFiles(formData: FormData) {
    const response = await apiClient.post('/dm-automation/validate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async validateWarmupFiles(formData: FormData) {
    const response = await apiClient.post('/warmup/validate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export default apiClient;
