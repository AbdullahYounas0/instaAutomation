import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { authService, InstagramAccount } from '../services/authService';
import { getApiUrl, getApiHeaders, getMultipartHeaders } from '../utils/apiUtils';
import CaptchaDetector from '../utils/captchaDetector';
import BrowserCloseDetector from '../utils/browserCloseDetector';
import './ScriptPage.css';

interface ScriptStatus {
  status: 'running' | 'completed' | 'error' | 'stopped';
  start_time?: string;
  end_time?: string;
  error?: string;
}

const DailyPostPage: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [scriptId, setScriptId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [scriptStatus, setScriptStatus] = useState<ScriptStatus | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [isPaused] = useState(false); // Removing unused setter
  const [availableAccounts, setAvailableAccounts] = useState<InstagramAccount[]>([]);
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    mediaFile: null as File | null,
    caption: ''
  });

  // Use useCallback to memoize the functions
  const fetchLogs = useCallback(async () => {
    if (!scriptId) return;
    
    try {
      const response = await axios.get(getApiUrl(`/script/${scriptId}/logs`), {
        headers: getApiHeaders()
      });
      
      const newLogs = response.data.logs;
      setLogs(newLogs);
      
      // Check for CAPTCHA/2FA events in logs
      CaptchaDetector.getInstance().detectCaptchaInLogs(newLogs);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  }, [scriptId]); // Add scriptId as a dependency

  const checkScriptStatus = useCallback(async () => {
    if (!scriptId) return;

    try {
      const token = authService.getToken();
      const response = await axios.get(getApiUrl(`/script/${scriptId}/status`), {
        headers: getApiHeaders()
      });
      
      setScriptStatus(response.data);
      
      // If script completed or has error, stop running
      if (response.data.status === 'completed' || response.data.status === 'error' || response.data.status === 'stopped') {
        setIsRunning(false);
      }
    } catch (error: any) {
      console.error('Error checking script status:', error);
      
      // Only stop the script if we get a specific error indicating the script doesn't exist
      // Don't stop on network errors or temporary server issues
      if (error.response?.status === 404) {
        // Script not found - it probably completed or was stopped
        console.log('Script not found (404) - stopping frontend monitoring');
        setIsRunning(false);
        setScriptStatus(null);
      } else if (error.response?.status >= 500) {
        // Server error - keep trying
        console.log('Server error - continuing to monitor script');
      } else {
        // Other errors (network, etc.) - keep trying for a bit longer
        console.log('Network or other error - continuing to monitor script');
      }
    }
  }, [scriptId]); // Add scriptId as a dependency

  useEffect(() => {
    // Set up CAPTCHA detection
    const captchaDetector = CaptchaDetector.getInstance();
    captchaDetector.setOnCaptchaDetected((event) => {
      if ((window as any).showCaptchaToast) {
        (window as any).showCaptchaToast(event.accountUsername);
      }
      // Note: The backend script handles automatic TOTP retry internally
      // The UI just shows the notification and continues monitoring
    });

    // Set up browser close detection
    const browserCloseDetector = BrowserCloseDetector.getInstance();
    browserCloseDetector.setupBrowserCloseDetection({
      scriptId: isRunning ? scriptId : null,
      onBrowserClose: () => {
        // Update local state immediately
        setIsRunning(false);
        setScriptStatus(prev => prev ? { ...prev, status: 'stopped', error: 'Browser closed by User' } : null);
      }
    });

    // Load available accounts
    loadAvailableAccounts();

    let interval: NodeJS.Timeout;
    if (scriptId && isRunning && !isPaused) {
      interval = setInterval(async () => {
        await fetchLogs();
        await checkScriptStatus();
      }, 2000);
    }
    
    return () => {
      clearInterval(interval);
      // Clean up browser close detection when component unmounts or script stops
      if (!isRunning) {
        browserCloseDetector.cleanup();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scriptId, isRunning, isPaused]);

  const loadAvailableAccounts = async () => {
    try {
      const result = await authService.getActiveInstagramAccounts();
      if (result.success && result.accounts) {
        setAvailableAccounts(result.accounts);
      }
    } catch (error) {
      console.error('Error loading accounts:', error);
    }
  };

  const handleFileChange = (file: File) => {
    setFormData(prev => ({
      ...prev,
      mediaFile: file
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (selectedAccountIds.length === 0 || !formData.mediaFile || !formData.caption.trim()) {
      alert('Please select at least one account, a media file, and enter a caption');
      return;
    }

    const data = new FormData();
    data.append('account_ids', JSON.stringify(selectedAccountIds));
    data.append('media_file', formData.mediaFile);
    data.append('caption', formData.caption);

    try {
      setIsRunning(true);
      setScriptStatus(null);  // Reset status
      setLogs([]);  // Clear previous logs
      
      const response = await axios.post(getApiUrl('/daily-post/start'), data, {
        headers: getMultipartHeaders(),
      });
      
      setScriptId(response.data.script_id);
    } catch (error: any) {
      console.error('Error starting script:', error);
      alert(error.response?.data?.error || 'Error starting script');
      setIsRunning(false);
      setScriptStatus(null);
    }
  };

  const handleStop = async (reason: string = 'Script stopped by user') => {
    if (!scriptId) return;

    try {
      await axios.post(getApiUrl(`/script/${scriptId}/stop`), {
        reason: reason
      }, {
        headers: getApiHeaders()
      });
      setIsRunning(false);
      setScriptId(null);
      setScriptStatus(null);
      
      // Clean up browser close detection
      BrowserCloseDetector.getInstance().cleanup();
    } catch (error) {
      console.error('Error stopping script:', error);
    }
  };

  const downloadLogs = async () => {
    if (!scriptId) return;

    try {
      const response = await axios.get(getApiUrl(`/script/${scriptId}/download-logs`), {
        headers: getApiHeaders(),
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `daily_post_${scriptId}_logs.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading logs:', error);
      alert('Error downloading logs');
    }
  };

  return (
    <div className="script-page">
      <div className="script-header">
        <h1>📸 Instagram Daily Post</h1>
        <p>Automatically post images or videos to multiple Instagram accounts simultaneously</p>
      </div>

      <div className="script-content">
        <div className="script-form-section">
          <form onSubmit={handleSubmit} className="script-form">
            <div className="form-group">
              <label>Select Instagram Accounts *</label>
              <div className="accounts-selection">
                {availableAccounts.length > 0 ? (
                  <div className="accounts-grid">
                    {availableAccounts.map((account) => (
                      <label key={account.id} className="account-checkbox">
                        <input
                          type="checkbox"
                          checked={selectedAccountIds.includes(account.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedAccountIds([...selectedAccountIds, account.id]);
                            } else {
                              setSelectedAccountIds(selectedAccountIds.filter(id => id !== account.id));
                            }
                          }}
                          disabled={isRunning}
                        />
                        <span className="account-info">
                          <strong>{account.username}</strong>
                          <div className="account-details">
                            <small><strong>Password:</strong> {account.password}</small>
                            {account.email && <small><strong>Email:</strong> {account.email}</small>}
                            {account.phone && <small><strong>Email Password:</strong> {account.phone}</small>}
                            <div className="proxy-info">
                              {account.has_proxy ? (
                                <small><strong>Proxy:</strong> 🌐 #{account.proxy_index} ({account.proxy_host}:{account.proxy_port})</small>
                              ) : (
                                <small><strong>Proxy:</strong> 🚫 Not assigned</small>
                              )}
                            </div>
                          </div>
                        </span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <p className="no-accounts">No Instagram accounts available. Please ask an admin to add accounts.</p>
                )}
                <small>Select the accounts you want to post to ({selectedAccountIds.length} selected)</small>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="media-file">
                Media File (Image/Video) *
              </label>
              <input
                type="file"
                id="media-file"
                accept=".jpg,.jpeg,.png,.gif,.mp4,.mov,.avi"
                onChange={(e) => e.target.files && handleFileChange(e.target.files[0])}
                disabled={isRunning}
                required
              />
              <small>Image (.jpg, .png, .gif) or Video (.mp4, .mov, .avi) to post</small>
            </div>

            <div className="form-group">
              <label htmlFor="caption">
                Caption *
              </label>
              <textarea
                id="caption"
                value={formData.caption}
                onChange={(e) => setFormData(prev => ({...prev, caption: e.target.value}))}
                disabled={isRunning}
                rows={3}
                placeholder="Enter your caption for the post"
                required
              />
              <small>Caption is required for all posts</small>
            </div>

            <div className="form-actions">
              {!isRunning ? (
                <button type="submit" className="btn btn-primary">
                  Start Daily Post
                </button>
              ) : (
                <button type="button" onClick={() => handleStop()} className="btn btn-danger">
                  Stop Automation
                </button>
              )}
            </div>
          </form>
        </div>

        <div className="script-logs-section">
          <div className="logs-header">
            <h3>Real-time Logs</h3>
            <div className="logs-controls">
              <div className="status-indicator">
                <span className={`status-dot ${
                  isPaused ? 'paused' :
                  scriptStatus?.status === 'completed' ? 'completed' : 
                  scriptStatus?.status === 'error' ? 'error' :
                  scriptStatus?.status === 'stopped' ? 'stopped' :
                  isRunning ? 'running' : 'idle'
                }`}></span>
                <span className="status-text">
                  {isPaused ? 'Paused (CAPTCHA/2FA)' :
                   scriptStatus?.status === 'completed' ? 'Completed' :
                   scriptStatus?.status === 'error' ? 'Error' :
                   scriptStatus?.status === 'stopped' ? 'Stopped' :
                   isRunning ? 'Running' : 'Idle'}
                </span>
              </div>
              
              {scriptId && scriptStatus && (scriptStatus.status === 'completed' || scriptStatus.status === 'error') && (
                <button 
                  onClick={downloadLogs}
                  className="btn btn-secondary btn-small"
                  title="Download logs as text file"
                >
                  📥 Download Logs
                </button>
              )}
            </div>
          </div>
          
          <div className="logs-container">
            {logs.length > 0 ? (
              logs.map((log, index) => (
                <div key={index} className="log-entry">
                  {log}
                </div>
              ))
            ) : (
              <div className="no-logs">
                {isRunning ? 'Waiting for logs...' : 'No logs available. Start the script to see logs.'}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="script-info">
        <h3>How it works:</h3>
        <ol>
          <li>Select Instagram accounts from the available list</li>
          <li>Upload image or video file to post</li>
          <li>Enter a caption for your post</li>
          <li>Start automation and monitor progress in real-time</li>
        </ol>
        
        <div className="script-features">
          <h4>Features:</h4>
          <ul>
            <li>✅ Select multiple accounts from admin-managed list</li>
            <li>✅ Image & Video support</li>
            <li>✅ Custom captions for each post</li>
            <li>✅ Visual browser mode for monitoring</li>
            <li>✅ Human-like behavior simulation</li>
            <li>✅ CAPTCHA/2FA handling with auto-pause</li>
            <li>✅ Comprehensive logging and reporting</li>
          </ul>
        </div>

        <div className="daily-post-info">
          <h4>Daily Post Settings Information:</h4>
          <p>
            The script automatically handles Instagram posting with human-like behavior patterns. 
            When CAPTCHA or 2FA is detected, the system will automatically handle TOTP verification and show a notification 
            sound to alert you. You can monitor progress in real-time with visual mode enabled.
          </p>
        </div>
      </div>
    </div>
  );
};

export default DailyPostPage;
