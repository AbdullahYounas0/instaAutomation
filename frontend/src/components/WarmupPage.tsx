import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { authService, InstagramAccount } from '../services/authService';
import { getApiUrl, getApiHeaders, getMultipartHeaders } from '../utils/apiUtils';
import CaptchaDetector from '../utils/captchaDetector';
import './ScriptPage.css';

const WarmupPage: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [scriptId, setScriptId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [scriptStatus, setScriptStatus] = useState<'idle' | 'running' | 'completed' | 'error' | 'stopped'>('idle');
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [isPaused] = useState(false);
  const [availableAccounts, setAvailableAccounts] = useState<InstagramAccount[]>([]);
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    warmupDurationMin: 10,
    warmupDurationMax: 400,
    schedulerDelay: 0,
    activities: {
      feedScroll: true,
      watchReels: true,
      likeReels: true,
      likePosts: true,
      explorePage: true,
      randomVisits: true
    },
    timing: {
      activityDelayMin: 3,
      activityDelayMax: 7,
      scrollAttemptsMin: 5,
      scrollAttemptsMax: 10
    }
  });

  // Initial setup effect
  useEffect(() => {
    // Set up CAPTCHA detection
    const captchaDetector = CaptchaDetector.getInstance();
    captchaDetector.setOnCaptchaDetected((event) => {
      // CAPTCHA detected - backend will handle this automatically
      console.log(`CAPTCHA detected for account: ${event.accountUsername}`);
      // Note: The backend script handles automatic TOTP retry internally
      // The UI just monitors without showing notifications
    });

    // Check for running scripts first, then load accounts
    checkForRunningScripts();
    loadAvailableAccounts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  // Separate effect for polling when script is running
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (scriptId && isRunning && !isPaused) {
      // Start fetching logs immediately when script is detected
      if (scriptId) {
        fetchLogs();
        checkScriptStatus();
      }
      
      // Then set up interval for continuous polling
      interval = setInterval(() => {
        fetchLogs();
        checkScriptStatus();
      }, 2000);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
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

  const checkForRunningScripts = async () => {
    try {
      const response = await axios.get(getApiUrl('/scripts/running'), {
        headers: getApiHeaders()
      });
      
      console.log('All running scripts:', response.data.scripts);
      const runningWarmupScripts = response.data.scripts.filter((s: any) => s.type === 'warmup');
      console.log('Filtered warmup scripts:', runningWarmupScripts);
      
      if (runningWarmupScripts.length > 0) {
        const script = runningWarmupScripts[0];
        console.log('Restoring warmup script state:', script);
        setScriptId(script.id);
        setIsRunning(true);
        setScriptStatus('running');
        // Load the script's configuration if available
        if (script.config) {
          setSelectedAccountIds(script.config.selected_account_ids || []);
        }
        console.log('Found running warmup script:', script.id);
        
        // Immediately fetch logs and status for the restored script
        setTimeout(() => {
          fetchLogs();
          checkScriptStatus();
        }, 100);
      } else {
        console.log('No running warmup scripts found');
      }
    } catch (error) {
      console.error('Error checking running scripts:', error);
    }
  };

  // Remove the handleCaptchaPause function since backend handles the delay

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
  }, [scriptId]);

  const checkScriptStatus = useCallback(async () => {
    if (!scriptId) return;
    
    try {
      const response = await axios.get(getApiUrl(`/script/${scriptId}/status`), {
        headers: getApiHeaders()
      });
      
      const status = response.data.status;
      setScriptStatus(status);
      
      // If script is completed, error, or stopped, update the UI
      if (status === 'completed' || status === 'error' || status === 'stopped') {
        setIsRunning(false);
        
        // Show completion message
        if (status === 'completed') {
          alert('Warmup script completed successfully!');
        } else if (status === 'error') {
          alert('Warmup script encountered an error. Check logs for details.');
        } else if (status === 'stopped') {
          alert('Warmup script was stopped.');
        }
      }
    } catch (error) {
      console.error('Error checking script status:', error);
    }
  }, [scriptId]);

  const handleActivityChange = (activity: string, value: boolean) => {
    setFormData(prev => ({
      ...prev,
      activities: {
        ...prev.activities,
        [activity]: value
      }
    }));
  };

  const handleTimingChange = (field: string, value: number) => {
    setFormData(prev => ({
      ...prev,
      timing: {
        ...prev.timing,
        [field]: value
      }
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (selectedAccountIds.length === 0) {
      alert('Please select at least one Instagram account');
      return;
    }

    // Validate scheduler delay is greater than maximum warmup time
    const maxWarmupHours = formData.warmupDurationMax / 60;
    if (formData.schedulerDelay !== 0 && formData.schedulerDelay <= maxWarmupHours) {
      alert(`Scheduler delay (${formData.schedulerDelay}h) must be greater than maximum warmup duration (${maxWarmupHours.toFixed(1)}h) to avoid conflicts.`);
      return;
    }

    const data = new FormData();
    data.append('account_ids', JSON.stringify(selectedAccountIds));
    data.append('warmup_duration_min', formData.warmupDurationMin.toString());
    data.append('warmup_duration_max', formData.warmupDurationMax.toString());
    data.append('scheduler_delay', formData.schedulerDelay.toString());
    
    // Activities
    data.append('feed_scroll', formData.activities.feedScroll.toString());
    data.append('watch_reels', formData.activities.watchReels.toString());
    data.append('like_reels', formData.activities.likeReels.toString());
    data.append('like_posts', formData.activities.likePosts.toString());
    data.append('explore_page', formData.activities.explorePage.toString());
    data.append('random_visits', formData.activities.randomVisits.toString());
    
    // Timing
    data.append('activity_delay_min', formData.timing.activityDelayMin.toString());
    data.append('activity_delay_max', formData.timing.activityDelayMax.toString());
    data.append('scroll_attempts_min', formData.timing.scrollAttemptsMin.toString());
    data.append('scroll_attempts_max', formData.timing.scrollAttemptsMax.toString());

    try {
      setIsRunning(true);
      setScriptStatus('running');
      const response = await axios.post(getApiUrl('/warmup/start'), data, {
        headers: getMultipartHeaders(),
      });
      
      setScriptId(response.data.script_id);
    } catch (error: any) {
      console.error('Error starting script:', error);
      alert(error.response?.data?.error || 'Error starting script');
      setIsRunning(false);
      setScriptStatus('idle');
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
      setScriptStatus('stopped');
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

      // Create download link
      const blob = new Blob([response.data], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `warmup_script_${scriptId}_logs.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading logs:', error);
      alert('Error downloading logs');
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  return (
    <div className="script-page">
      <div className="script-header">
        <h1>🔥 Instagram Account Warmup</h1>
        <p>Warm up Instagram accounts with natural human-like activities to build trust and engagement</p>
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
                            {account.email_Password && <small><strong>Email Password:</strong> {account.email_Password}</small>}
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
                <small>Select the accounts you want to warm up ({selectedAccountIds.length} selected)</small>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="warmup-duration-range">
                Random Warmup Duration Range (minutes)
              </label>
              <div className="slider-group">
                <div className="slider-item">
                  <label>Minimum: {formData.warmupDurationMin} min</label>
                  <input
                    type="range"
                    id="warmup-duration-min"
                    min="10"
                    max="400"
                    value={formData.warmupDurationMin}
                    onChange={(e) => {
                      const value = parseInt(e.target.value);
                      setFormData(prev => ({
                        ...prev, 
                        warmupDurationMin: Math.min(value, prev.warmupDurationMax - 1)
                      }));
                    }}
                    disabled={isRunning}
                  />
                </div>
                <div className="slider-item">
                  <label>Maximum: {formData.warmupDurationMax} min</label>
                  <input
                    type="range"
                    id="warmup-duration-max"
                    min="10"
                    max="400"
                    value={formData.warmupDurationMax}
                    onChange={(e) => {
                      const value = parseInt(e.target.value);
                      const maxHours = value / 60;
                      setFormData(prev => ({
                        ...prev, 
                        warmupDurationMax: Math.max(value, prev.warmupDurationMin + 1),
                        // Auto-adjust scheduler delay if it becomes invalid
                        schedulerDelay: prev.schedulerDelay !== 0 && prev.schedulerDelay <= maxHours 
                          ? Math.ceil(maxHours) + 1 
                          : prev.schedulerDelay
                      }));
                    }}
                    disabled={isRunning}
                  />
                </div>
              </div>
              <small>
                Each account will warm up for a random duration between {formData.warmupDurationMin} and {formData.warmupDurationMax} minutes
                ({formatDuration(formData.warmupDurationMin)} - {formatDuration(formData.warmupDurationMax)})
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="scheduler-delay">
                Recurring Delay: {formData.schedulerDelay === 0 ? 'Start Immediately (No Recurring)' : `${formData.schedulerDelay} hour${formData.schedulerDelay > 1 ? 's' : ''} between sessions`}
              </label>
              <input
                type="range"
                id="scheduler-delay"
                min="0"
                max="10"
                value={formData.schedulerDelay}
                onChange={(e) => setFormData(prev => ({...prev, schedulerDelay: parseInt(e.target.value)}))}
                disabled={isRunning}
              />
              <small>
                {formData.schedulerDelay === 0 
                  ? 'Single warmup session - script will start immediately and run once' 
                  : `Recurring warmup sessions - script will run for ${formData.warmupDurationMin}-${formData.warmupDurationMax} minutes, then wait ${formData.schedulerDelay} hour${formData.schedulerDelay > 1 ? 's' : ''}, then repeat automatically until stopped`
                }
                {formData.schedulerDelay !== 0 && formData.schedulerDelay <= (formData.warmupDurationMax / 60) && (
                  <span style={{color: '#ff6b35', display: 'block', marginTop: '4px'}}>
                    ⚠️ Recurring delay should be greater than max warmup time ({(formData.warmupDurationMax / 60).toFixed(1)}h) for optimal scheduling
                  </span>
                )}
              </small>
            </div>

            <div className="form-group">
              <label>Activity Types</label>
              <div className="checkbox-grid">
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={formData.activities.feedScroll}
                    onChange={(e) => handleActivityChange('feedScroll', e.target.checked)}
                    disabled={isRunning}
                  />
                  <span>Feed Scrolling</span>
                </label>
                
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={formData.activities.watchReels}
                    onChange={(e) => handleActivityChange('watchReels', e.target.checked)}
                    disabled={isRunning}
                  />
                  <span>Watch Reels</span>
                </label>
                
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={formData.activities.likeReels}
                    onChange={(e) => handleActivityChange('likeReels', e.target.checked)}
                    disabled={isRunning}
                  />
                  <span>Like Reels</span>
                </label>
                
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={formData.activities.likePosts}
                    onChange={(e) => handleActivityChange('likePosts', e.target.checked)}
                    disabled={isRunning}
                  />
                  <span>Like Posts</span>
                </label>
                
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={formData.activities.explorePage}
                    onChange={(e) => handleActivityChange('explorePage', e.target.checked)}
                    disabled={isRunning}
                  />
                  <span>Explore Page</span>
                </label>
                
                <label className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={formData.activities.randomVisits}
                    onChange={(e) => handleActivityChange('randomVisits', e.target.checked)}
                    disabled={isRunning}
                  />
                  <span>Random Page Visits</span>
                </label>
              </div>
              <small>Select which activities to perform during warmup</small>
            </div>

            <div className="form-group">
              <label>Activity Timing Settings</label>
              <div className="timing-grid">
                <div className="timing-item">
                  <label>Activity Delay Min (seconds)</label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={formData.timing.activityDelayMin}
                    onChange={(e) => handleTimingChange('activityDelayMin', parseInt(e.target.value))}
                    disabled={isRunning}
                  />
                </div>
                
                <div className="timing-item">
                  <label>Activity Delay Max (seconds)</label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={formData.timing.activityDelayMax}
                    onChange={(e) => handleTimingChange('activityDelayMax', parseInt(e.target.value))}
                    disabled={isRunning}
                  />
                </div>
                
                <div className="timing-item">
                  <label>Scroll Attempts Min</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={formData.timing.scrollAttemptsMin}
                    onChange={(e) => handleTimingChange('scrollAttemptsMin', parseInt(e.target.value))}
                    disabled={isRunning}
                  />
                </div>
                
                <div className="timing-item">
                  <label>Scroll Attempts Max</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={formData.timing.scrollAttemptsMax}
                    onChange={(e) => handleTimingChange('scrollAttemptsMax', parseInt(e.target.value))}
                    disabled={isRunning}
                  />
                </div>
              </div>
              <small>
                Activity delay: {formData.timing.activityDelayMin}-{formData.timing.activityDelayMax} seconds | 
                Scroll attempts: {formData.timing.scrollAttemptsMin}-{formData.timing.scrollAttemptsMax} per activity
              </small>
            </div>

            <div className="form-actions">
              {!isRunning ? (
                <button type="submit" className="btn btn-primary">
                  Start Account Warmup
                </button>
              ) : (
                <button type="button" onClick={() => handleStop()} className="btn btn-danger">
                  Stop Warmup
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
                <span className={`status-dot ${isPaused ? 'paused' : isRunning ? 'running' : 'idle'}`}></span>
                <span>
                  {isPaused ? 'Paused (CAPTCHA/2FA)' : isRunning ? 'Running' : 'Idle'}
                  {isPaused && <span style={{fontSize: '12px', display: 'block', opacity: 0.8}}>Resuming automatically...</span>}
                </span>
              </div>
              {scriptId && (scriptStatus === 'completed' || scriptStatus === 'error') && (
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
          <li>Set the random warmup duration range (10-400 minutes per session)</li>
          <li>Configure recurring delay (0-10 hours) - if 0, runs once; if &gt; 0, runs repeatedly with delays</li>
          <li>Select activities and configure timing settings for natural behavior</li>
          <li>Start the warmup - browsers will open automatically for selected accounts</li>
          <li>Monitor progress in real-time - each cycle runs for random duration, then waits</li>
          <li>Stop manually anytime to end the recurring sessions</li>
        </ol>
        
        <div className="script-features">
          <h4>Features:</h4>
          <ul>
            <li>✅ Human-like behavior simulation</li>
            <li>✅ Random duration selection for unpredictable patterns</li>
            <li>✅ Recurring sessions with configurable delays</li>
            <li>✅ Multiple activity types (scrolling, liking, watching)</li>
            <li>✅ Configurable duration range (10 minutes to 6.7 hours per session)</li>
            <li>✅ Dynamic account selection from database</li>
            <li>✅ Random delays and natural patterns</li>
            <li>✅ Comprehensive activity logging</li>
            <li>✅ Error handling and recovery</li>
            <li>🔄 Automatic recurring cycles until manually stopped</li>
          </ul>
        </div>

        <div className="warmup-benefits">
          <h4>Benefits of Account Warmup:</h4>
          <ul>
            <li>🔥 Increases account trust score with Instagram</li>
            <li>📈 Improves engagement rates for future posts</li>
            <li>🛡️ Reduces risk of account restrictions</li>
            <li>🎯 Better reach and visibility for content</li>
            <li>⚡ Prepares accounts for automation campaigns</li>
            <li>🎲 Random duration prevents detection patterns</li>
            <li>🔄 Recurring sessions maintain consistent account activity</li>
            <li>⏰ Automated scheduling for hands-free operation</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default WarmupPage;
