import axios from 'axios';

// Get API URL based on environment
const getApiUrl = () => {
  const environment = process.env.REACT_APP_ENVIRONMENT || 'development';
  // Prefer explicit env variables if set
  let url = environment === 'production'
    ? process.env.REACT_APP_API_URL_PROD 
    : process.env.REACT_APP_API_URL_DEV || 'http://localhost:8000';

  // Fallback for empty string
  if (!url) {
    url = 'http://localhost:8000';
  }

  // Force HTTPS for Railway production URLs
  if (url.includes('railway.app') && url.startsWith('http://')) {
    url = url.replace('http://', 'https://');
  }

  // Ensure the URL ends with /api/v1
  if (!url.endsWith('/api/v1')) {
    // Remove trailing slash if present
    if (url.endsWith('/')) {
      url = url.slice(0, -1);
    }
    url = `${url}/api/v1`;
  }
  return url;
};

// Create axios instance
const api = axios.create({
  baseURL: getApiUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const response = await axios.post(`${getApiUrl()}/auth/refresh`, {
            refresh_token: refreshToken
          });
          
          const { access_token } = response.data;
          localStorage.setItem('accessToken', access_token);
          
          // Retry original request
          original.headers.Authorization = `Bearer ${access_token}`;
          return api(original);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      } else {
        // No refresh token, redirect to login
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;