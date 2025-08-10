// Configuration settings for the application
const isDevelopment = process.env.NODE_ENV === 'development';

// Use environment-specific API URLs
const getApiUrl = () => {
  // Check for environment variable first
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  if (isDevelopment) {
    return 'http://localhost:5000';
  }
  
  // Production URL - use your domain
  return 'https://wdyautomation.shop';
};

const apiUrl = getApiUrl();

export const config = {
  API_BASE_URL: `${apiUrl}/api`,
  isDevelopment,
  environment: process.env.NODE_ENV || 'development',
};

export default config;
