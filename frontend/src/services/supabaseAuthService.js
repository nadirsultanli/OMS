import { createClient } from '@supabase/supabase-js';

// Supabase configuration
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseAnonKey);

class SupabaseAuthService {
  
  // Sign up new user (creates both auth and database records via triggers)
  async signUp(email, password, userData = {}) {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            name: userData.name || '',
            role: userData.role || 'sales_rep',
            full_name: userData.full_name || userData.name || '',
          }
        }
      });

      if (error) throw error;

      return {
        success: true,
        user: data.user,
        session: data.session,
        message: 'Sign up successful! Please check your email to confirm your account.'
      };
    } catch (error) {
      console.error('Sign up error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Sign in existing user
  async signIn(email, password) {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (error) throw error;

      // Get user data from our database
      const userData = await this.getCurrentUserData();
      
      // Update last login
      if (userData) {
        await this.updateLastLogin(data.user.id);
      }

      // Store user data in localStorage for compatibility
      this.storeUserData(data.session, userData);

      return {
        success: true,
        user: userData,
        session: data.session
      };
    } catch (error) {
      console.error('Sign in error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Sign out user
  async signOut() {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;

      // Clear local storage
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');

      return {
        success: true
      };
    } catch (error) {
      console.error('Sign out error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Get current session
  async getSession() {
    try {
      const { data, error } = await supabase.auth.getSession();
      if (error) throw error;
      return data.session;
    } catch (error) {
      console.error('Get session error:', error);
      return null;
    }
  }

  // Get current user data from our database
  async getCurrentUserData() {
    try {
      const session = await this.getSession();
      if (!session) return null;

      const { data, error } = await supabase
        .rpc('get_user_by_auth_id', { auth_id: session.user.id });

      if (error) throw error;
      return data[0] || null;
    } catch (error) {
      console.error('Get current user data error:', error);
      return null;
    }
  }

  // Update last login timestamp
  async updateLastLogin(authUserId) {
    try {
      const { error } = await supabase
        .rpc('update_user_last_login', { auth_id: authUserId });
      
      if (error) throw error;
    } catch (error) {
      console.error('Update last login error:', error);
    }
  }

  // Store user data in localStorage for backward compatibility
  storeUserData(session, userData) {
    if (session) {
      localStorage.setItem('accessToken', session.access_token);
      localStorage.setItem('refreshToken', session.refresh_token);
    }
    
    if (userData) {
      localStorage.setItem('user', JSON.stringify({
        id: userData.id,
        email: userData.email,
        role: userData.role,
        name: userData.full_name
      }));
    }
  }

  // Check if user is authenticated
  isAuthenticated() {
    const token = localStorage.getItem('accessToken');
    return !!token;
  }

  // Get current user from localStorage
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  // Send password reset email
  async resetPassword(email) {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`
      });

      if (error) throw error;

      return {
        success: true,
        message: 'Password reset instructions sent to your email.'
      };
    } catch (error) {
      console.error('Reset password error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Update password with recovery token
  async updatePassword(password) {
    try {
      const { error } = await supabase.auth.updateUser({ password });
      
      if (error) throw error;

      return {
        success: true,
        message: 'Password updated successfully!'
      };
    } catch (error) {
      console.error('Update password error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Listen to auth state changes
  onAuthStateChange(callback) {
    return supabase.auth.onAuthStateChange(async (event, session) => {
      let userData = null;
      
      if (session) {
        userData = await this.getCurrentUserData();
        this.storeUserData(session, userData);
      } else {
        // Clear local storage on sign out
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
      }

      callback(event, session, userData);
    });
  }

  // Refresh the current session
  async refreshSession() {
    try {
      const { data, error } = await supabase.auth.refreshSession();
      if (error) throw error;
      return { success: true, session: data.session };
    } catch (error) {
      console.error('Session refresh error:', error);
      return { success: false, error: error.message };
    }
  }

  // Get Supabase client for direct access if needed
  getClient() {
    return supabase;
  }
}

export default new SupabaseAuthService();