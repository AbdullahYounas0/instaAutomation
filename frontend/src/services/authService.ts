import { config } from '../config/config';

const API_BASE_URL = config.API_BASE_URL;

export interface LoginResponse {
  success: boolean;
  token?: string;
  user?: {
    id: string;
    name: string;
    username: string;
    role: 'admin' | 'va';
  };
  message?: string;
}

export interface VerifyTokenResponse {
  success: boolean;
  payload?: {
    user_id: string;
    username: string;
    role: 'admin' | 'va';
    exp: number;
  };
  message?: string;
}

export interface ApiResponse {
  success: boolean;
  message?: string;
  [key: string]: any;
}

export interface User {
  id: string;
  name: string;
  username: string;
  role: 'admin' | 'va';
  created_at: string;
  is_active: boolean;
  last_login: string | null;
}

export interface ActivityLog {
  timestamp: string;
  user_id: string;
  action: string;
  details: string;
  ip_address: string;
  city: string;
  country: string;
  country_code: string;
}

export interface ScriptLog {
  script_id: string;
  user_id: string;
  user_name: string;
  user_username: string;
  script_type: string;
  status: string;
  start_time: string;
  end_time?: string;
  error?: string;
  stop_reason?: string;
  config: any;
  logs_available: boolean;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  va_users: number;
  admin_users: number;
  recent_logins: number;
  running_scripts: number;
  total_scripts: number;
}

export interface InstagramAccount {
  id: string;
  username: string;
  password: string;
  email: string;
  email_Password: string;
  notes: string;
  totp_secret: string;  // Added TOTP secret field for 2FA
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_used: string | null;
  // Proxy information
  assigned_proxy?: string | null;
  proxy_index?: number | null;
  proxy_host?: string | null;
  proxy_port?: string | null;
  has_proxy?: boolean;
}

export interface ProxyInfo {
  index: number;
  proxy: string;
  host: string | null;
  port: string | null;
  is_assigned: boolean;
  assigned_to: string | null;
}

export interface ProxyUsageStats {
  total_proxies: number;
  assigned_proxies: number;
  available_proxies: number;
  assignments_count: number;
  usage_percentage: number;
}

export interface ProxyAssignments {
  [accountUsername: string]: {
    proxy: string;
    proxy_index: number | null;
    proxy_host: string | null;
    proxy_port: string | null;
    is_valid: boolean;
  };
}

class AuthService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    };
  }

  private getAuthHeadersForFormData(): HeadersInit {
    const token = localStorage.getItem('auth_token');
    return {
      'Authorization': token ? `Bearer ${token}` : ''
    };
  }

  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      return await response.json();
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async verifyToken(token: string): Promise<VerifyTokenResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      return await response.json();
    } catch (error) {
      console.error('Token verification error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async logout(): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });

      const result = await response.json();
      
      // Clear local storage regardless of response
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      
      return result;
    } catch (error) {
      console.error('Logout error:', error);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      return { success: true, message: 'Logged out locally' };
    }
  }

  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  isAdmin(): boolean {
    const user = this.getCurrentUser();
    return user?.role === 'admin';
  }

  // Admin endpoints
  async getUsers(): Promise<{ success: boolean; users?: User[]; message?: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get users error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async createUser(name: string, username: string, password: string, role: 'admin' | 'va' = 'va'): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ name, username, password, role }),
      });

      return await response.json();
    } catch (error) {
      console.error('Create user error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async updateUser(userId: string, updates: Partial<User>): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(updates),
      });

      return await response.json();
    } catch (error) {
      console.error('Update user error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async deactivateUser(userId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/deactivate`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Deactivate user error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async deleteUser(userId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Delete user error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async getActivityLogs(userId?: string, limit: number = 100): Promise<{ success: boolean; logs?: ActivityLog[]; message?: string }> {
    try {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      params.append('limit', limit.toString());

      const response = await fetch(`${API_BASE_URL}/admin/activity-logs?${params}`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get activity logs error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async getScriptLogs(userId?: string, limit: number = 100): Promise<{ success: boolean; script_logs?: ScriptLog[]; message?: string }> {
    try {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      if (limit) params.append('limit', limit.toString());

      const response = await fetch(`${API_BASE_URL}/admin/script-logs?${params}`, {
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Server error' }));
        return { success: false, message: errorData.message || `Server error: ${response.status}` };
      }

      return await response.json();
    } catch (error) {
      console.error('Get script logs error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async getAdminStats(): Promise<{ success: boolean; stats?: AdminStats; message?: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/stats`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get admin stats error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  // Instagram Accounts Management
  async getInstagramAccounts(): Promise<{ success: boolean; accounts?: InstagramAccount[]; message?: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/instagram-accounts`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get Instagram accounts error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async getActiveInstagramAccounts(): Promise<{ success: boolean; accounts?: InstagramAccount[]; message?: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/instagram-accounts/active`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get active Instagram accounts error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async addInstagramAccount(
    username: string,
    password: string,
    email: string = '',
    email_Password: string = '',
    notes: string = '',
    totp_secret: string = ''
  ): Promise<{ success: boolean; account?: InstagramAccount; message?: string }> {
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      formData.append('email', email);
      formData.append('email_Password', email_Password);
      formData.append('notes', notes);
      formData.append('totp_secret', totp_secret);

      const response = await fetch(`${API_BASE_URL}/instagram-accounts`, {
        method: 'POST',
        headers: this.getAuthHeadersForFormData(),
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error('Add Instagram account error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async updateInstagramAccount(
    accountId: string,
    updates: Partial<InstagramAccount>
  ): Promise<{ success: boolean; account?: InstagramAccount; message?: string }> {
    try {
      const formData = new FormData();
      
      // Add only the fields that are being updated
      if (updates.username !== undefined) formData.append('username', updates.username);
      if (updates.password !== undefined) formData.append('password', updates.password);
      if (updates.email !== undefined) formData.append('email', updates.email);
      if (updates.email_Password !== undefined) formData.append('email_Password', updates.email_Password);
      if (updates.notes !== undefined) formData.append('notes', updates.notes);
      if (updates.totp_secret !== undefined) formData.append('totp_secret', updates.totp_secret);
      if (updates.is_active !== undefined) formData.append('is_active', updates.is_active.toString());

      const response = await fetch(`${API_BASE_URL}/instagram-accounts/${accountId}`, {
        method: 'PUT',
        headers: this.getAuthHeadersForFormData(),
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error('Update Instagram account error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async deleteInstagramAccount(accountId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/instagram-accounts/${accountId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Delete Instagram account error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async importInstagramAccounts(file: File): Promise<{ success: boolean; added_count?: number; skipped_count?: number; skipped_accounts?: any[]; message?: string }> {
    try {
      const formData = new FormData();
      formData.append('accounts_file', file);

      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/instagram-accounts/import`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error('Import Instagram accounts error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  // Proxy Management Methods
  async getAllProxies(): Promise<{ 
    success: boolean; 
    proxies?: ProxyInfo[]; 
    usage_stats?: ProxyUsageStats; 
    available_indices?: number[]; 
    message?: string 
  }> {
    try {
      const response = await fetch(`${API_BASE_URL}/proxies`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get all proxies error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async getProxyAssignments(): Promise<{ 
    success: boolean; 
    assignments?: ProxyAssignments; 
    message?: string 
  }> {
    try {
      const response = await fetch(`${API_BASE_URL}/proxy-assignments`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get proxy assignments error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async assignProxy(username: string, proxyIndex?: number): Promise<ApiResponse> {
    try {
      const formData = new FormData();
      formData.append('username', username);
      if (proxyIndex !== undefined) {
        formData.append('proxy_index', proxyIndex.toString());
      }

      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/proxy-assignments`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: formData,
      });

      const data = await response.json();
      
      if (!response.ok) {
        console.error('Assign proxy HTTP error:', response.status, data);
        return { 
          success: false, 
          message: data.message || data.detail?.message || `HTTP Error ${response.status}` 
        };
      }
      
      return data;
    } catch (error) {
      console.error('Assign proxy network error:', error);
      return { success: false, message: `Network error: ${error}` };
    }
  }

  async reassignProxy(username: string, newProxyIndex: number): Promise<ApiResponse> {
    try {
      const formData = new FormData();
      formData.append('new_proxy_index', (newProxyIndex - 1).toString()); // Convert to 0-based index

      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/proxy-assignments/${username}`, {
        method: 'PUT',
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error('Reassign proxy error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async removeProxyAssignment(username: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/proxy-assignments/${username}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });

      const data = await response.json();
      
      if (!response.ok) {
        console.error('Remove proxy HTTP error:', response.status, data);
        return { 
          success: false, 
          message: data.message || data.detail?.message || `HTTP Error ${response.status}` 
        };
      }
      
      return data;
    } catch (error) {
      console.error('Remove proxy assignment network error:', error);
      return { success: false, message: `Network error: ${error}` };
    }
  }
}

export const authService = new AuthService();
