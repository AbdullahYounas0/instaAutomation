import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import './LoginPage.css';

interface LoginPageProps {}

const LoginPage: React.FC<LoginPageProps> = () => {
  const [showLogin, setShowLogin] = useState(false);
  const [loginType, setLoginType] = useState<'admin' | 'va'>('admin');
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('auth_token');
    if (token) {
      authService.verifyToken(token).then(result => {
        if (result.success) {
          const user = JSON.parse(localStorage.getItem('user') || '{}');
          if (user.role === 'admin') {
            navigate('/admin');
          } else {
            navigate('/home');
          }
        } else {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
        }
      });
    }
  }, [navigate]);

  const handleRoleSelection = (role: 'admin' | 'va') => {
    setLoginType(role);
    setShowLogin(true);
    setError('');
    setCredentials({ username: '', password: '' });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await authService.login(credentials.username, credentials.password);
      
      if (result.success && result.token && result.user) {
        // Store token and user info
        localStorage.setItem('auth_token', result.token);
        localStorage.setItem('user', JSON.stringify(result.user));
        
        // Redirect based on role
        if (result.user.role === 'admin') {
          navigate('/admin');
        } else {
          navigate('/home');
        }
      } else {
        setError(result.message || 'Login failed');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setShowLogin(false);
    setError('');
    setCredentials({ username: '', password: '' });
  };

  if (!showLogin) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <h1>Instagram Automation System</h1>
            <p>Select your login type to continue</p>
          </div>
          
          <div className="login-options">
            <button 
              className="login-option admin-option"
              onClick={() => handleRoleSelection('admin')}
            >
              <div className="option-icon">👑</div>
              <h3>Admin Login</h3>
              <p>Manage users, track activities, and oversee operations</p>
            </button>
            
            <button 
              className="login-option va-option"
              onClick={() => handleRoleSelection('va')}
            >
              <div className="option-icon">🤖</div>
              <h3>VA Login</h3>
              <p>Access automation tools and manage campaigns</p>
            </button>
          </div>
          
          <div className="login-footer">
            <p>© 2025 Instagram Automation System</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-form-card">
        <div className="login-form-header">
          <button className="back-button" onClick={handleBack}>
            ← Back
          </button>
          <h2>{loginType === 'admin' ? 'Admin' : 'VA'} Login</h2>
          <div className="role-indicator">
            <span className={`role-badge ${loginType}`}>
              {loginType === 'admin' ? '👑 Admin' : '🤖 VA'}
            </span>
          </div>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          {error && (
            <div className="error-message">
              <span>⚠️ {error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={credentials.username}
              onChange={handleInputChange}
              placeholder={`Enter your ${loginType} username`}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={credentials.password}
              onChange={handleInputChange}
              placeholder="Enter your password"
              required
              disabled={loading}
            />
          </div>

          <button 
            type="submit" 
            className={`login-submit ${loginType}`}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Logging in...
              </>
            ) : (
              `Login as ${loginType === 'admin' ? 'Admin' : 'VA'}`
            )}
          </button>

          {loginType === 'admin' && (
            <div className="admin-hint">
              {/* <small>Default admin credentials: admin / admin123</small> */}
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
