import React, { useState, useEffect } from 'react';
import supabaseAuthService from '../services/supabaseAuthService';

const AuthTest = () => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    // Check current session
    const checkSession = async () => {
      const currentSession = await supabaseAuthService.getSession();
      if (currentSession) {
        setSession(currentSession);
        const userData = await supabaseAuthService.getCurrentUserData();
        setUser(userData);
      }
      setLoading(false);
    };

    checkSession();

    // Listen to auth changes
    const { data: { subscription } } = supabaseAuthService.onAuthStateChange(
      async (event, session, userData) => {
        console.log('Auth state changed:', event, session, userData);
        setSession(session);
        setUser(userData);
        setLoading(false);
      }
    );

    return () => subscription?.unsubscribe();
  }, []);

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    
    const result = await supabaseAuthService.signUp(email, password, {
      name,
      role: 'sales_rep'
    });

    if (result.success) {
      setMessage(result.message);
    } else {
      setError(result.error);
    }
  };

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    
    const result = await supabaseAuthService.signIn(email, password);

    if (result.success) {
      setMessage('Signed in successfully!');
    } else {
      setError(result.error);
    }
  };

  const handleSignOut = async () => {
    const result = await supabaseAuthService.signOut();
    if (result.success) {
      setMessage('Signed out successfully!');
    }
  };

  const handleResetPassword = async () => {
    if (!email) {
      setError('Please enter email first');
      return;
    }

    const result = await supabaseAuthService.resetPassword(email);
    if (result.success) {
      setMessage(result.message);
    } else {
      setError(result.error);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div style={{ padding: '20px', maxWidth: '500px', margin: '0 auto' }}>
      <h2>Authentication Test</h2>
      
      {message && (
        <div style={{ padding: '10px', backgroundColor: '#d4edda', color: '#155724', marginBottom: '10px', borderRadius: '4px' }}>
          {message}
        </div>
      )}
      
      {error && (
        <div style={{ padding: '10px', backgroundColor: '#f8d7da', color: '#721c24', marginBottom: '10px', borderRadius: '4px' }}>
          {error}
        </div>
      )}

      {session && user ? (
        <div>
          <h3>Welcome, {user.full_name || user.email}!</h3>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Role:</strong> {user.role}</p>
          <p><strong>Status:</strong> {user.status}</p>
          <p><strong>User ID:</strong> {user.id}</p>
          <p><strong>Last Login:</strong> {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</p>
          
          <button onClick={handleSignOut} style={{ padding: '10px 20px', marginTop: '10px' }}>
            Sign Out
          </button>
        </div>
      ) : (
        <div>
          <form style={{ marginBottom: '20px' }}>
            <div style={{ marginBottom: '10px' }}>
              <label>Name:</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              />
            </div>
            
            <div style={{ marginBottom: '10px' }}>
              <label>Email:</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              />
            </div>
            
            <div style={{ marginBottom: '10px' }}>
              <label>Password:</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              />
            </div>
            
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button onClick={handleSignUp} type="button" style={{ padding: '10px 20px' }}>
                Sign Up
              </button>
              <button onClick={handleSignIn} type="button" style={{ padding: '10px 20px' }}>
                Sign In
              </button>
              <button onClick={handleResetPassword} type="button" style={{ padding: '10px 20px' }}>
                Reset Password
              </button>
            </div>
          </form>
        </div>
      )}

      <div style={{ marginTop: '30px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
        <h4>Current Session Info:</h4>
        <pre style={{ fontSize: '12px', overflow: 'auto' }}>
          {JSON.stringify({ session: !!session, user: !!user, userData: user }, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default AuthTest;