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
  async (config) => {
    // First try to get token from localStorage (for custom auth)
    let token = localStorage.getItem('accessToken');
    
    // If no custom token, try to get Supabase token
    if (!token) {
      try {
        // Import Supabase client dynamically to avoid circular dependencies
        const { createClient } = await import('@supabase/supabase-js');
        const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
        const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
        
        if (supabaseUrl && supabaseAnonKey) {
          const supabase = createClient(supabaseUrl, supabaseAnonKey);
          const { data: { session } } = await supabase.auth.getSession();
          if (session?.access_token) {
            token = session.access_token;
          }
        }
      } catch (error) {
        console.error('Error getting Supabase token:', error);
      }
    }
    
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
      
      // First try custom auth refresh
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
          // Custom auth refresh failed, try Supabase refresh
          try {
            const { createClient } = await import('@supabase/supabase-js');
            const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
            const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
            
            if (supabaseUrl && supabaseAnonKey) {
              const supabase = createClient(supabaseUrl, supabaseAnonKey);
              const { data, error: refreshError } = await supabase.auth.refreshSession();
              
              if (!refreshError && data.session?.access_token) {
                // Retry original request with new token
                original.headers.Authorization = `Bearer ${data.session.access_token}`;
                return api(original);
              }
            }
          } catch (supabaseError) {
            console.error('Supabase refresh error:', supabaseError);
          }
          
          // Both refresh methods failed, redirect to login
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      } else {
        // Try Supabase refresh directly
        try {
          const { createClient } = await import('@supabase/supabase-js');
          const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
          const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
          
          if (supabaseUrl && supabaseAnonKey) {
            const supabase = createClient(supabaseUrl, supabaseAnonKey);
            const { data, error: refreshError } = await supabase.auth.refreshSession();
            
            if (!refreshError && data.session?.access_token) {
              // Retry original request with new token
              original.headers.Authorization = `Bearer ${data.session.access_token}`;
              return api(original);
            }
          }
        } catch (supabaseError) {
          console.error('Supabase refresh error:', supabaseError);
        }
        
        // No refresh token available, redirect to login
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;