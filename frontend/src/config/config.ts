// Configuration settings for the application
const isDevelopment = process.env.NODE_ENV === 'development';
// Force localhost for development - override any environment variables
const apiUrl = 'http://localhost:5000';

export const config = {
  API_BASE_URL: `${apiUrl}/api`,
  isDevelopment,
  environment: process.env.NODE_ENV || 'development',
};

export default config;
