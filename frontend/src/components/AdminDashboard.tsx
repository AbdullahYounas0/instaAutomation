import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  authService, 
  User, 
  ActivityLog, 
  AdminStats, 
  InstagramAccount, 
  ScriptLog,
  ProxyInfo,
  ProxyUsageStats,
  ProxyAssignments
} from '../services/authService';
import { getApiUrl } from '../utils/apiUtils';
import './AdminDashboard.css';

const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'logs' | 'session-logs' | 'accounts' | 'proxies'>('overview');
  const [users, setUsers] = useState<User[]>([]);
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [scriptLogs, setScriptLogs] = useState<ScriptLog[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [instagramAccounts, setInstagramAccounts] = useState<InstagramAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedUserId, setSelectedUserId] = useState<string>(''); // For filtering script logs
  
  // User management state
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUser, setNewUser] = useState({
    name: '',
    username: '',
    password: '',
    role: 'va' as 'admin' | 'va'
  });
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({
    name: '',
    password: '',
    is_active: true
  });
  
  // Logs modal state
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [selectedScriptId, setSelectedScriptId] = useState<string>('');
  const [scriptLogContent, setScriptLogContent] = useState<string>('');
  const [logsLoading, setLogsLoading] = useState(false);
  
  // Instagram Accounts management state
  const [showCreateAccount, setShowCreateAccount] = useState(false);
  const [newAccount, setNewAccount] = useState({
    username: '',
    password: '',
    email: '',
    phone: '',
    notes: '',
    totp_secret: ''
  });
  const [editingAccount, setEditingAccount] = useState<InstagramAccount | null>(null);
  const [editAccountForm, setEditAccountForm] = useState({
    username: '',
    password: '',
    email: '',
    phone: '',
    notes: '',
    totp_secret: '',
    is_active: true
  });
  const [showImportAccounts, setShowImportAccounts] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  
  // Proxy management state
  const [proxies, setProxies] = useState<ProxyInfo[]>([]);
  const [proxyUsageStats, setProxyUsageStats] = useState<ProxyUsageStats | null>(null);
  const [showProxyModal, setShowProxyModal] = useState(false);
  const [selectedAccountForProxy, setSelectedAccountForProxy] = useState<string>('');
  const [selectedProxyIndex, setSelectedProxyIndex] = useState<number | ''>('');
  
  const navigate = useNavigate();

  useEffect(() => {
    // Verify admin access
    const user = authService.getCurrentUser();
    if (!user || user.role !== 'admin') {
      navigate('/login');
      return;
    }

    loadData();
  }, [navigate]);

  // Reload script logs when selected user changes
  useEffect(() => {
    if (activeTab === 'logs') {
      loadScriptLogs();
    }
  }, [selectedUserId, activeTab]); // Remove loadScriptLogs from dependencies to avoid the issue

  const loadData = async () => {
    setLoading(true);
    try {
      const [usersRes, logsRes, statsRes, accountsRes, proxiesRes] = await Promise.all([
        authService.getUsers(),
        authService.getActivityLogs(),
        authService.getAdminStats(),
        authService.getInstagramAccounts(),
        authService.getAllProxies()
      ]);

      if (usersRes.success && usersRes.users) setUsers(usersRes.users);
      if (logsRes.success && logsRes.logs) {
        console.log('Received logs data:', logsRes.logs.slice(0, 3)); // Debug: check first 3 logs
        setLogs(logsRes.logs);
      }
      if (statsRes.success && statsRes.stats) setStats(statsRes.stats);
      if (accountsRes.success && accountsRes.accounts) setInstagramAccounts(accountsRes.accounts);
      if (proxiesRes.success) {
        if (proxiesRes.proxies) setProxies(proxiesRes.proxies);
        if (proxiesRes.usage_stats) setProxyUsageStats(proxiesRes.usage_stats);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadScriptLogs = async () => {
    try {
      const scriptLogsRes = await authService.getScriptLogs(selectedUserId || undefined, 100);
      if (scriptLogsRes.success && scriptLogsRes.script_logs) {
        setScriptLogs(scriptLogsRes.script_logs);
      } else {
        console.error('Failed to load script logs:', scriptLogsRes.message);
        setScriptLogs([]); // Set empty array on failure
      }
    } catch (error) {
      console.error('Error loading script logs:', error);
      setScriptLogs([]); // Set empty array on error
    }
  };

  const handleLogout = async () => {
    await authService.logout();
    navigate('/login');
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await authService.createUser(
        newUser.name,
        newUser.username,
        newUser.password,
        newUser.role
      );

      if (result.success) {
        setShowCreateUser(false);
        setNewUser({ name: '', username: '', password: '', role: 'va' });
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to create user');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;

    setLoading(true);
    try {
      const updates: any = { name: editForm.name, is_active: editForm.is_active };
      if (editForm.password) {
        updates.password = editForm.password;
      }

      const result = await authService.updateUser(editingUser.id, updates);

      if (result.success) {
        setEditingUser(null);
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to update user');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivateUser = async (userId: string) => {
    if (!window.confirm('Are you sure you want to deactivate this user?')) return;

    try {
      const result = await authService.deactivateUser(userId);
      if (result.success) {
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to deactivate user');
      }
    } catch (error) {
      setError('Network error');
    }
  };

  const handleDeleteUser = async (userId: string, username: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete user "${username}"? This action cannot be undone.`)) return;

    setLoading(true);
    try {
      const result = await authService.deleteUser(userId);
      if (result.success) {
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to delete user');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const startEditUser = (user: User) => {
    setEditingUser(user);
    setEditForm({
      name: user.name,
      password: '',
      is_active: user.is_active
    });
  };

  // Instagram Accounts Management Functions
  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await authService.addInstagramAccount(
        newAccount.username,
        newAccount.password,
        newAccount.email,
        newAccount.phone,
        newAccount.notes,
        newAccount.totp_secret
      );

      if (result.success) {
        setShowCreateAccount(false);
        setNewAccount({ username: '', password: '', email: '', phone: '', notes: '', totp_secret: '' });
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to create account');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleEditAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAccount) return;

    setLoading(true);
    try {
      const updates: any = {
        username: editAccountForm.username,
        email: editAccountForm.email,
        phone: editAccountForm.phone,
        notes: editAccountForm.notes,
        totp_secret: editAccountForm.totp_secret,
        is_active: editAccountForm.is_active
      };
      
      if (editAccountForm.password) {
        updates.password = editAccountForm.password;
      }

      const result = await authService.updateInstagramAccount(editingAccount.id, updates);

      if (result.success) {
        setEditingAccount(null);
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to update account');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async (accountId: string, username: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete Instagram account "${username}"? This action cannot be undone.`)) return;

    setLoading(true);
    try {
      const result = await authService.deleteInstagramAccount(accountId);
      if (result.success) {
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to delete account');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleImportAccounts = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) {
      setError('Please select a file to import');
      return;
    }

    setLoading(true);
    try {
      const result = await authService.importInstagramAccounts(importFile);
      
      if (result.success) {
        setShowImportAccounts(false);
        setImportFile(null);
        loadData(); // Refresh data
        
        let message = `Successfully imported ${result.added_count} accounts`;
        if (result.skipped_count && result.skipped_count > 0) {
          message += `, skipped ${result.skipped_count} accounts`;
        }
        alert(message);
      } else {
        setError(result.message || 'Failed to import accounts');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const startEditAccount = (account: InstagramAccount) => {
    setEditingAccount(account);
    setEditAccountForm({
      username: account.username,
      password: '',
      email: account.email,
      phone: account.phone,
      notes: account.notes,
      totp_secret: account.totp_secret || '',
      is_active: account.is_active
    });
  };

  // Proxy Management Functions
  const handleAssignProxy = (accountUsername: string) => {
    setSelectedAccountForProxy(accountUsername);
    setSelectedProxyIndex('');
    setShowProxyModal(true);
  };

  const handleProxyAssignment = async () => {
    if (!selectedAccountForProxy) return;

    setLoading(true);
    try {
      const proxyIndex = selectedProxyIndex === '' ? undefined : Number(selectedProxyIndex) - 1;
      console.log(`Attempting to assign proxy ${proxyIndex} to account ${selectedAccountForProxy}`);
      
      const result = await authService.assignProxy(selectedAccountForProxy, proxyIndex);
      
      console.log('Proxy assignment result:', result);
      
      if (result.success) {
        console.log('Proxy assignment successful, closing modal and refreshing data');
        setShowProxyModal(false);
        setSelectedAccountForProxy('');
        setSelectedProxyIndex('');
        await loadData(); // Refresh data to show updated proxy assignments
        setError(''); // Clear any previous errors
      } else {
        const errorMessage = result.message || 'Failed to assign proxy - unknown error';
        console.error('Proxy assignment failed:', errorMessage);
        setError(`Proxy Assignment Error: ${errorMessage}`);
      }
    } catch (error: any) {
      console.error('Assign proxy network/parse error:', error);
      let errorMessage = 'Network error occurred while assigning proxy';
      
      if (error.message) {
        errorMessage = `Network Error: ${error.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveProxyAssignment = async (accountUsername: string) => {
    if (!window.confirm(`Remove proxy assignment from ${accountUsername}?`)) return;

    setLoading(true);
    try {
      console.log(`Attempting to remove proxy from account ${accountUsername}`);
      const result = await authService.removeProxyAssignment(accountUsername);
      
      console.log('Remove proxy result:', result);
      
      if (result.success) {
        console.log('Proxy removal successful, refreshing data');
        await loadData(); // Refresh data to show updated proxy assignments
        setError(''); // Clear any previous errors
      } else {
        const errorMessage = result.message || 'Failed to remove proxy assignment - unknown error';
        console.error('Proxy removal failed:', errorMessage);
        setError(`Proxy Removal Error: ${errorMessage}`);
      }
    } catch (error: any) {
      console.error('Remove proxy network/parse error:', error);
      let errorMessage = 'Network error occurred while removing proxy assignment';
      
      if (error.message) {
        errorMessage = `Network Error: ${error.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getAvailableProxies = () => {
    return proxies.filter(proxy => !proxy.is_assigned);
  };

  // Logs modal functions
  const viewScriptLogs = async (scriptId: string) => {
    setSelectedScriptId(scriptId);
    setShowLogsModal(true);
    setLogsLoading(true);
    
    try {
      const token = authService.getToken();
      const response = await fetch(getApiUrl(`/script/${scriptId}/logs`), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setScriptLogContent(data.logs.join('\n'));
      } else {
        setScriptLogContent('Failed to load logs');
      }
    } catch (error) {
      console.error('Error loading logs:', error);
      setScriptLogContent('Error loading logs');
    } finally {
      setLogsLoading(false);
    }
  };

  const downloadScriptLogs = async () => {
    if (!selectedScriptId) return;
    
    try {
      const token = authService.getToken();
      const response = await fetch(getApiUrl(`/script/${selectedScriptId}/download-logs`), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `script_${selectedScriptId}_logs.txt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error downloading logs:', error);
      alert('Error downloading logs');
    }
  };

  return (
    <div className="admin-dashboard">
      {/* Header */}
      <div className="admin-header">
        <div className="header-left">
          <h1>Admin Dashboard</h1>
          <p>Instagram Automation System</p>
        </div>
        <div className="header-right">
          <span className="admin-user">👑 {authService.getCurrentUser()?.name}</span>
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="admin-tabs">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button
          className={`tab-button ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          👥 Users
        </button>
        <button
          className={`tab-button ${activeTab === 'accounts' ? 'active' : ''}`}
          onClick={() => setActiveTab('accounts')}
        >
          📱 Instagram Accounts
        </button>
        <button
          className={`tab-button ${activeTab === 'proxies' ? 'active' : ''}`}
          onClick={() => setActiveTab('proxies')}
        >
          🌐 Proxies
        </button>
        <button
          className={`tab-button ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          📋 Script Logs
        </button>
        <button
          className={`tab-button ${activeTab === 'session-logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('session-logs')}
        >
          📈 Session Logs
        </button>
      </div>

      {/* Content Area */}
      <div className="admin-content">
        {loading && <div className="loading-overlay">Loading...</div>}

        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
          <div className="overview-tab">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">👥</div>
                <div className="stat-content">
                  <h3>{stats.total_users}</h3>
                  <p>Total Users</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">✅</div>
                <div className="stat-content">
                  <h3>{stats.active_users}</h3>
                  <p>Active Users</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🤖</div>
                <div className="stat-content">
                  <h3>{stats.va_users}</h3>
                  <p>VA Users</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">👑</div>
                <div className="stat-content">
                  <h3>{stats.admin_users}</h3>
                  <p>Admin Users</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🔄</div>
                <div className="stat-content">
                  <h3>{stats.running_scripts}</h3>
                  <p>Running Scripts</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">📊</div>
                <div className="stat-content">
                  <h3>{stats.recent_logins}</h3>
                  <p>Recent Logins (24h)</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="users-tab">
            <div className="users-header">
              <h2>User Management</h2>
              <button
                className="create-user-btn"
                onClick={() => setShowCreateUser(true)}
              >
                + Create User
              </button>
            </div>

            {/* Users Table */}
            <div className="users-table">
              <table>
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Username</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Last Login</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={`users-table-${user.id}`}>
                      <td>
                        <div className="user-info">
                          <span className="user-name">{user.name}</span>
                          <span className="user-id">{user.id}</span>
                        </div>
                      </td>
                      <td>{user.username}</td>
                      <td>
                        <span className={`role-badge ${user.role}`}>
                          {user.role === 'admin' ? '👑 Admin' : '🤖 VA'}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        {user.last_login ? formatDate(user.last_login) : 'Never'}
                      </td>
                      <td>
                        <div className="user-actions">
                          <button
                            className="edit-btn"
                            onClick={() => startEditUser(user)}
                          >
                            Edit
                          </button>
                          {user.is_active && user.role !== 'admin' && (
                            <button
                              className="deactivate-btn"
                              onClick={() => handleDeactivateUser(user.id)}
                            >
                              Deactivate
                            </button>
                          )}
                          <button
                            className="delete-btn"
                            onClick={() => handleDeleteUser(user.id, user.username)}
                            title="Delete user permanently"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Instagram Accounts Tab */}
        {activeTab === 'accounts' && (
          <div className="accounts-tab">
            <div className="accounts-header">
              <h2>Instagram Accounts Management</h2>
              <div className="accounts-actions">
                <button
                  className="create-account-btn"
                  onClick={() => setShowCreateAccount(true)}
                >
                  + Add Account
                </button>
                <button
                  className="import-accounts-btn"
                  onClick={() => setShowImportAccounts(true)}
                >
                  📂 Import Accounts
                </button>
              </div>
            </div>

            {/* 2FA Info Banner */}
            <div className="totp-info-banner">
              <div className="info-content">
                <span className="info-icon">🔐</span>
                <div className="info-text">
                  <strong>2FA Support:</strong> Add TOTP secrets to enable automatic 2FA handling during login. 
                  Get the 16-character secret from Instagram's 2FA setup (when adding Google Authenticator).
                </div>
              </div>
            </div>

            {/* Accounts Table */}
            <div className="accounts-table-wrapper">
              <div className="accounts-table">
                <table>
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>2FA Status</th>
                    <th>Proxy Assignment</th>
                    <th>Status</th>
                    <th>Last Used</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {instagramAccounts.map((account) => (
                    <tr key={`accounts-table-${account.id}`}>
                      <td>
                        <div className="account-info">
                          <span className="account-username">{account.username}</span>
                          {account.notes && (
                            <span className="account-notes" title={account.notes}>📝</span>
                          )}
                        </div>
                      </td>
                      <td>{account.email || '-'}</td>
                      <td>{account.phone || '-'}</td>
                      <td>
                        <span className={`totp-status ${account.totp_secret ? 'enabled' : 'disabled'}`}>
                          {account.totp_secret ? '🔐 Enabled' : '🔓 Disabled'}
                        </span>
                      </td>
                      <td>
                        <div className="proxy-info">
                          {account.has_proxy ? (
                            <div className="proxy-assigned">
                              <span className="proxy-badge">
                                🌐 Proxy #{account.proxy_index}
                              </span>
                              <small className="proxy-details">
                                {account.proxy_host}:{account.proxy_port}
                              </small>
                            </div>
                          ) : (
                            <span className="no-proxy">
                              🚫 No proxy assigned
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className={`status-badge ${account.is_active ? 'active' : 'inactive'}`}>
                          {account.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        {account.last_used ? formatDate(account.last_used) : 'Never'}
                      </td>
                      <td>{formatDate(account.created_at)}</td>
                      <td>
                        <div className="account-actions">
                          <button
                            className="edit-btn"
                            onClick={() => startEditAccount(account)}
                          >
                            Edit
                          </button>
                          {account.has_proxy ? (
                            <button
                              className="remove-proxy-btn"
                              onClick={() => handleRemoveProxyAssignment(account.username)}
                              title="Remove proxy assignment"
                            >
                              Remove Proxy
                            </button>
                          ) : (
                            <button
                              className="assign-proxy-btn"
                              onClick={() => handleAssignProxy(account.username)}
                              title="Assign proxy"
                            >
                              Assign Proxy
                            </button>
                          )}
                          <button
                            className="delete-btn"
                            onClick={() => handleDeleteAccount(account.id, account.username)}
                            title="Delete account permanently"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            </div>

            {instagramAccounts.length === 0 && (
              <div className="no-accounts">
                <p>No Instagram accounts found. Add some accounts to get started.</p>
              </div>
            )}
          </div>
        )}

        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <div className="logs-tab">
            <div className="logs-header">
              <h2>Script Execution Logs</h2>
              <div className="logs-filters">
                <select
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className="user-filter"
                >
                  <option value="">All Users</option>
                  {users.filter(user => user.role === 'va').map((user, index) => (
                    <option key={`user-filter-${user.id}-${index}`} value={user.id}>
                      {user.name} ({user.username})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="logs-table">
              <table>
                <thead>
                  <tr>
                    <th>Script ID</th>
                    <th>User</th>
                    <th>Script Type</th>
                    <th>Status</th>
                    <th>Started</th>
                    <th>Duration</th>
                    <th>Accounts</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {scriptLogs.map((log) => (
                    <tr key={`script-logs-${log.script_id}`}>
                      <td>
                        <span className="script-id" title={log.script_id}>
                          {log.script_id.substring(0, 8)}...
                        </span>
                      </td>
                      <td>
                        <div className="user-info">
                          <span className="user-name">{log.user_name}</span>
                          <small className="user-username">@{log.user_username}</small>
                        </div>
                      </td>
                      <td>
                        <span className={`script-type-badge ${log.script_type}`}>
                          {log.script_type === 'daily_post' ? '📸 Daily Post' :
                           log.script_type === 'dm_automation' ? '💬 DM Automation' :
                           log.script_type === 'warmup' ? '🔥 Warmup' :
                           log.script_type}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${log.status}`}>
                          {log.status === 'running' ? '🔄 Running' :
                           log.status === 'completed' ? '✅ Completed' :
                           log.status === 'error' ? '❌ Error' :
                           log.status === 'stopped' ? '⏹️ Stopped' :
                           log.status}
                        </span>
                      </td>
                      <td>{formatDate(log.start_time)}</td>
                      <td>
                        {log.end_time ? (
                          <span>
                            {Math.round((new Date(log.end_time).getTime() - new Date(log.start_time).getTime()) / 1000 / 60)} min
                          </span>
                        ) : (
                          log.status === 'running' ? (
                            <span>
                              {Math.round((new Date().getTime() - new Date(log.start_time).getTime()) / 1000 / 60)} min
                            </span>
                          ) : '-'
                        )}
                      </td>
                      <td>
                        {log.config?.selected_account_ids?.length || 
                         log.config?.concurrent_accounts || 
                         '-'}
                      </td>
                      <td>
                        <div className="log-actions">
                          {log.logs_available && (
                            <button
                              className="view-logs-btn"
                              onClick={() => viewScriptLogs(log.script_id)}
                              title="View detailed logs"
                            >
                              📋 Logs
                            </button>
                          )}
                          {log.error && (
                            <span className="error-indicator" title={log.error}>
                              ⚠️
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {scriptLogs.length === 0 && (
              <div className="no-logs">
                <p>No script execution logs found.</p>
                {selectedUserId && (
                  <p>Try selecting a different user or view all users.</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Session Logs Tab */}
        {activeTab === 'session-logs' && (
          <div className="logs-tab">
            <h2>Session Activity Logs</h2>
            <div className="logs-table">
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Details</th>
                    <th>Location</th>
                    <th>IP Address</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log, index) => (
                    <tr key={`session-logs-${index}-${log.timestamp}`}>
                      <td>{formatDate(log.timestamp)}</td>
                      <td>{log.user_id}</td>
                      <td>
                        <span className={`action-badge ${log.action}`}>
                          {log.action}
                        </span>
                      </td>
                      <td>{log.details}</td>
                      <td>
                        <div className="location-info">
                          <span className="location-text">
                            {(log.city && log.country) ? `${log.city}, ${log.country}` : 
                             (log.ip_address === '127.0.0.1' || log.ip_address === 'system') ? 'Local, Local' : 'Unknown'}
                          </span>
                          {log.country_code && log.country_code !== 'UN' && (
                            <span className="country-flag">
                              {log.country_code === 'LC' ? '🏠' : '🌍'}
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className="ip-address">{log.ip_address}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Proxies Tab */}
        {activeTab === 'proxies' && (
          <div className="proxies-tab">
            <h2>Proxy Management</h2>
            
            {/* Proxy Usage Stats */}
            {proxyUsageStats && (
              <div className="proxy-stats">
                <div className="stat-card">
                  <h3>Total Proxies</h3>
                  <p>{proxyUsageStats.total_proxies}</p>
                </div>
                <div className="stat-card">
                  <h3>Assigned</h3>
                  <p>{proxyUsageStats.assigned_proxies}</p>
                </div>
                <div className="stat-card">
                  <h3>Available</h3>
                  <p>{proxyUsageStats.available_proxies}</p>
                </div>
                <div className="stat-card">
                  <h3>Usage %</h3>
                  <p>{proxyUsageStats.usage_percentage.toFixed(1)}%</p>
                </div>
              </div>
            )}

            {/* Proxies Table */}
            <div className="proxies-table">
              <table>
                <thead>
                  <tr>
                    <th>Proxy #</th>
                    <th>Host</th>
                    <th>Port</th>
                    <th>Status</th>
                    <th>Assigned To</th>
                  </tr>
                </thead>
                <tbody>
                  {proxies.map((proxy) => (
                    <tr key={`proxy-${proxy.index}`}>
                      <td>#{proxy.index}</td>
                      <td>{proxy.host || 'N/A'}</td>
                      <td>{proxy.port || 'N/A'}</td>
                      <td>
                        <span className={`status-badge ${proxy.is_assigned ? 'assigned' : 'available'}`}>
                          {proxy.is_assigned ? '🟢 Assigned' : '🟡 Available'}
                        </span>
                      </td>
                      <td>
                        {proxy.assigned_to ? (
                          <span className="assigned-account">
                            @{proxy.assigned_to}
                          </span>
                        ) : (
                          <span className="no-assignment">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {proxies.length === 0 && (
              <div className="no-proxies">
                <p>No proxy information available.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateUser && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Create New User</h3>
              <button onClick={() => setShowCreateUser(false)}>×</button>
            </div>
            <form onSubmit={handleCreateUser} className="modal-form">
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={newUser.name}
                  onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value as 'admin' | 'va' })}
                >
                  <option value="va">VA</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateUser(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading}>
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Edit User: {editingUser.name}</h3>
              <button onClick={() => setEditingUser(null)}>×</button>
            </div>
            <form onSubmit={handleEditUser} className="modal-form">
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>New Password (leave empty to keep current)</label>
                <input
                  type="password"
                  value={editForm.password}
                  onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={editForm.is_active}
                    onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setEditingUser(null)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading}>
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Instagram Account Modal */}
      {showCreateAccount && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Add New Instagram Account</h3>
              <button onClick={() => setShowCreateAccount(false)}>×</button>
            </div>
            <form onSubmit={handleCreateAccount} className="modal-form">
              <div className="form-group">
                <label>Username *</label>
                <input
                  type="text"
                  value={newAccount.username}
                  onChange={(e) => setNewAccount({ ...newAccount, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password *</label>
                <input
                  type="password"
                  value={newAccount.password}
                  onChange={(e) => setNewAccount({ ...newAccount, password: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={newAccount.email}
                  onChange={(e) => setNewAccount({ ...newAccount, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Email Password</label>
                <input
                  type="text"
                  value={newAccount.phone}
                  onChange={(e) => setNewAccount({ ...newAccount, phone: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={newAccount.notes}
                  onChange={(e) => setNewAccount({ ...newAccount, notes: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label>TOTP Secret (2FA) 🔐</label>
                <input
                  type="text"
                  value={newAccount.totp_secret}
                  onChange={(e) => setNewAccount({ ...newAccount, totp_secret: e.target.value })}
                  placeholder="Enter 32-character TOTP secret (e.g., JPV6 WXN4 CTU5 TSQO 3TRK 7AWE 2Z3X ZIOP)"
                  maxLength={39}
                  style={{ fontFamily: 'monospace', fontSize: '14px' }}
                />
                <small style={{ color: '#666', fontSize: '12px' }}>
                  📱 Optional: Add Google Authenticator TOTP secret (32 chars) for automatic 2FA handling during login
                </small>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateAccount(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading}>
                  Add Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Instagram Account Modal */}
      {editingAccount && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Edit Instagram Account: {editingAccount.username}</h3>
              <button onClick={() => setEditingAccount(null)}>×</button>
            </div>
            <form onSubmit={handleEditAccount} className="modal-form">
              <div className="form-group">
                <label>Username *</label>
                <input
                  type="text"
                  value={editAccountForm.username}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>New Password (leave empty to keep current)</label>
                <input
                  type="password"
                  value={editAccountForm.password}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, password: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={editAccountForm.email}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Email Password</label>
                <input
                  type="text"
                  value={editAccountForm.phone}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, phone: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={editAccountForm.notes}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, notes: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label>TOTP Secret (2FA) 🔐</label>
                <input
                  type="text"
                  value={editAccountForm.totp_secret}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, totp_secret: e.target.value })}
                  placeholder="Enter 32-character TOTP secret (e.g., JPV6 WXN4 CTU5 TSQO 3TRK 7AWE 2Z3X ZIOP)"
                  maxLength={39}
                  style={{ fontFamily: 'monospace', fontSize: '14px' }}
                />
                <small style={{ color: '#666', fontSize: '12px' }}>
                  📱 Optional: Add/update Google Authenticator TOTP secret (32 chars) for automatic 2FA handling
                </small>
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={editAccountForm.is_active}
                    onChange={(e) => setEditAccountForm({ ...editAccountForm, is_active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setEditingAccount(null)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading}>
                  Update Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Import Instagram Accounts Modal */}
      {showImportAccounts && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Import Instagram Accounts</h3>
              <button onClick={() => setShowImportAccounts(false)}>×</button>
            </div>
            <form onSubmit={handleImportAccounts} className="modal-form">
              <div className="form-group">
                <label>Select Excel/CSV File</label>
                <input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  required
                />
                <small>
                  File should contain columns: username (required), password (required), email (optional), phone (optional), notes (optional), totp_secret (optional)
                </small>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowImportAccounts(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading || !importFile}>
                  Import Accounts
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Logs Modal */}
      {showLogsModal && (
        <div className="modal-overlay">
          <div className="logs-modal">
            <div className="modal-header">
              <h3>Script Logs: {selectedScriptId.substring(0, 8)}...</h3>
              <div className="modal-actions">
                <button
                  className="download-logs-btn"
                  onClick={downloadScriptLogs}
                  title="Download logs as text file"
                >
                  📥 Download
                </button>
                <button
                  className="modal-close"
                  onClick={() => setShowLogsModal(false)}
                >
                  ×
                </button>
              </div>
            </div>
            <div className="modal-body">
              {logsLoading ? (
                <div className="logs-loading">
                  Loading logs...
                </div>
              ) : (
                <div className="logs-container">
                  <pre className="logs-content">
                    {scriptLogContent || 'No logs available'}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Proxy Assignment Modal */}
      {showProxyModal && (
        <div className="modal-overlay">
          <div className="modal proxy-assignment-modal">
            <div className="proxy-assignment-modal-scroll-container">
              <div className="modal-header">
              <h3>Assign Proxy to @{selectedAccountForProxy}</h3>
              <button 
                className="close-btn" 
                onClick={() => {
                  setShowProxyModal(false);
                  setSelectedAccountForProxy('');
                  setSelectedProxyIndex('');
                }}
              >
                ×
              </button>
            </div>
            <div className="modal-content">
              <div className="account-info-card">
                <div className="account-username">@{selectedAccountForProxy}</div>
                <div className="account-subtitle">Configure proxy assignment for optimal performance</div>
                <div className="account-badge">
                  ✨ Ready to assign
                </div>
              </div>
              
              <div className="form-section">
                <div className="form-group">
                  <label htmlFor="proxySelect">Choose Proxy Configuration:</label>
                  <select
                    id="proxySelect"
                    value={selectedProxyIndex}
                    onChange={(e) => setSelectedProxyIndex(e.target.value === '' ? '' : Number(e.target.value))}
                    className="form-input"
                  >
                    <option value="" className="auto-assign-option">🤖 Auto-assign next available proxy</option>
                    {getAvailableProxies().map((proxy) => (
                      <option key={`proxy-option-${proxy.index}`} value={proxy.index} className="proxy-option">
                        🌐 Proxy #{proxy.index} - {proxy.host}:{proxy.port}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="stats-section">
                <div className="stat-item">
                  <div className="stat-value">{getAvailableProxies().length}</div>
                  <div className="stat-label">Available</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{((proxies.length - getAvailableProxies().length) / proxies.length * 100).toFixed(0)}%</div>
                  <div className="stat-label">Usage</div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="cancel-btn" 
                onClick={() => {
                  setShowProxyModal(false);
                  setSelectedAccountForProxy('');
                  setSelectedProxyIndex('');
                }}
              >
                <span>Cancel</span>
              </button>
              <button 
                className="confirm-btn" 
                onClick={handleProxyAssignment}
                disabled={loading}
              >
                {loading ? (
                  <span>Assigning...</span>
                ) : (
                  <span>Assign Proxy</span>
                )}
              </button>
            </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
