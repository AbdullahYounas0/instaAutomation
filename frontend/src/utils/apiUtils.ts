// API utility functions
import { config } from '../config/config';
import { authService } from '../services/authService';

export const getApiHeaders = () => {
  const token = authService.getToken();
  return {
    'Authorization': token ? `Bearer ${token}` : '',
    'Content-Type': 'application/json',
  };
};

export const getApiUrl = (endpoint: string) => {
  return `${config.API_BASE_URL}${endpoint}`;
};

export const getMultipartHeaders = () => {
  const token = authService.getToken();
  return {
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

const apiUtils = {
  getApiHeaders,
  getApiUrl,
  getMultipartHeaders,
};

export default apiUtils;
