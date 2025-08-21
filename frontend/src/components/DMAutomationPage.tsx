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

const DMAutomationPage: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [scriptId, setScriptId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [scriptStatus, setScriptStatus] = useState<ScriptStatus | null>(null);
  const [isPaused] = useState(false); // Removing unused setter
  const [showResponsesModal, setShowResponsesModal] = useState(false);
  const [responses, setResponses] = useState<any[]>([]);
  const [availableAccounts, setAvailableAccounts] = useState<InstagramAccount[]>([]);
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    targetFile: null as File | null,
    dmPromptFile: null as File | null,
    customPrompt: '',
    dmsPerAccount: 30
  });
  
  // New state for spintax preview functionality
  const [spintaxPreviews, setSpintaxPreviews] = useState<string[]>([]);
  const [selectedSpintaxIndex, setSelectedSpintaxIndex] = useState<number>(-1);
  const [editableSpintax, setEditableSpintax] = useState<string>('');
  const [showSpintaxPreview, setShowSpintaxPreview] = useState<boolean>(false);
  const [promptFileContent, setPromptFileContent] = useState<string>('');
  const [isGeneratingPreviews, setIsGeneratingPreviews] = useState<boolean>(false);
  const [isGeneratingAISamples, setIsGeneratingAISamples] = useState<boolean>(false);

  // Define fetchLogs and checkScriptStatus using useCallback before the useEffect
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
      setScriptStatus(response.data);
      
      // Auto-stop UI when script completes or encounters error
      if (status === 'completed' || status === 'error') {
        setIsRunning(false);
        
        // Show completion/error message
        if (status === 'completed') {
          // Add success message to logs if not already present
          const successMsg = '🎉 DM automation completed successfully!';
          setLogs(prev => {
            if (!prev.some(log => log.includes('completed successfully') || log.includes('🎉'))) {
              return [...prev, successMsg];
            }
            return prev;
          });
        } else if (status === 'error') {
          // Add error message to logs
          const errorMsg = response.data.error || 'Script encountered an error';
          setLogs(prev => {
            if (!prev.some(log => log.includes('Script encountered an error') || log.includes('❌'))) {
              return [...prev, `❌ Error: ${errorMsg}`];
            }
            return prev;
          });
          
          // Check if error is due to browser closure
          if (errorMsg.toLowerCase().includes('browser') && (errorMsg.toLowerCase().includes('closed') || errorMsg.toLowerCase().includes('connection'))) {
            // Auto-reset UI for browser closure
            setTimeout(() => {
              setScriptId(null);
              setScriptStatus(null);
              setLogs(prev => [...prev, '🔄 UI reset - Ready for new automation']);
            }, 2000);
          }
        }
      }
    } catch (error) {
      console.error('Error checking script status:', error);
      // If we can't reach the server, assume the script stopped
      setIsRunning(false);
      setScriptStatus(null);
    }
  }, [scriptId]);

  useEffect(() => {
    // Set up CAPTCHA detection
    const captchaDetector = CaptchaDetector.getInstance();
    captchaDetector.setOnCaptchaDetected((event) => {
      // CAPTCHA detected - backend will handle this automatically
      console.log(`CAPTCHA detected for account: ${event.accountUsername}`);
      // Note: The backend script handles automatic TOTP retry internally
      // The UI just monitors without showing notifications
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

  const handleFileChange = (field: string, file: File) => {
    setFormData(prev => ({
      ...prev,
      [field]: file
    }));
    
    // If it's a prompt file, read its content and generate previews
    if (field === 'dmPromptFile' && file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setPromptFileContent(content);
        generateSpintaxPreviews(content);
      };
      reader.readAsText(file);
    }
  };

  const generateSpintaxPreviews = async (promptContent: string) => {
    if (!promptContent.trim()) return;
    
    setIsGeneratingPreviews(true);
    setShowSpintaxPreview(true);
    
    try {
      const response = await axios.post(getApiUrl('/generate-spintax-previews'), {
        prompt: promptContent
      }, {
        headers: getApiHeaders()
      });
      
      if (response.data.success && response.data.previews) {
        setSpintaxPreviews(response.data.previews);
        setSelectedSpintaxIndex(-1);
        setEditableSpintax('');
      } else {
        alert('Failed to generate spintax previews');
      }
    } catch (error) {
      console.error('Error generating spintax previews:', error);
      alert('Error generating spintax previews');
    } finally {
      setIsGeneratingPreviews(false);
    }
  };

  const generateAISamples = async () => {
    if (!promptFileContent.trim()) {
      alert('Please upload a prompt file first');
      return;
    }
    
    setIsGeneratingAISamples(true);
    
    try {
      const response = await axios.post(getApiUrl('/generate-ai-spintax-samples'), {
        prompt: promptFileContent,
        count: 3
      }, {
        headers: getApiHeaders()
      });
      
      if (response.data.success && response.data.samples) {
        // Replace existing previews with new AI samples
        setSpintaxPreviews(response.data.samples);
        setSelectedSpintaxIndex(-1);
        setEditableSpintax('');
        
        // Show message if AI was not used
        if (!response.data.ai_used && response.data.message) {
          alert(response.data.message);
        }
      } else {
        alert('Failed to generate AI spintax samples');
      }
    } catch (error) {
      console.error('Error generating AI spintax samples:', error);
      alert('Error generating AI spintax samples');
    } finally {
      setIsGeneratingAISamples(false);
    }
  };

  const selectSpintaxOption = (index: number) => {
    setSelectedSpintaxIndex(index);
    setEditableSpintax(spintaxPreviews[index]);
  };

  const confirmSpintaxSelection = () => {
    if (editableSpintax.trim()) {
      // Update the custom prompt with the final selected/edited version
      setFormData(prev => ({
        ...prev,
        customPrompt: editableSpintax
      }));
      setShowSpintaxPreview(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (selectedAccountIds.length === 0) {
      alert('Please select at least one Instagram account');
      return;
    }

    if (!formData.targetFile) {
      alert('Please upload a target accounts file (Excel/CSV) containing the users you want to send DMs to');
      return;
    }

    // Check if prompt file was uploaded but spintax not selected
    if (formData.dmPromptFile && promptFileContent && !formData.customPrompt) {
      alert('Please select and confirm a spintax template from the uploaded prompt file before starting the automation.');
      setShowSpintaxPreview(true);
      return;
    }

    const data = new FormData();
    data.append('account_ids', JSON.stringify(selectedAccountIds));
    if (formData.targetFile) data.append('target_file', formData.targetFile);
    if (formData.dmPromptFile) data.append('dm_prompt_file', formData.dmPromptFile);
    data.append('custom_prompt', formData.customPrompt);
    data.append('dms_per_account', formData.dmsPerAccount.toString());

    try {
      setIsRunning(true);
      setScriptStatus(null);  // Reset status
      setLogs([]);  // Clear previous logs
      
      const response = await axios.post(getApiUrl('/dm-automation/start'), data, {
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
      setLogs(prev => [...prev, `🛑 ${reason}`]);
      
      // Clean up browser close detection
      BrowserCloseDetector.getInstance().cleanup();
    } catch (error) {
      console.error('Error stopping script:', error);
      setIsRunning(false);
      setScriptId(null);
      setScriptStatus(null);
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
      link.download = `dm_automation_script_${scriptId}_logs.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading logs:', error);
      alert('Error downloading logs');
    }
  };

  const viewPositiveResponses = async () => {
    if (!scriptId) return;

    try {
      const response = await axios.get(getApiUrl(`/script/${scriptId}/responses`), {
        headers: getApiHeaders()
      });
      
      setResponses(response.data.responses || []);
      setShowResponsesModal(true);
    } catch (error) {
      console.error('Error fetching responses:', error);
      alert('Error fetching responses');
    }
  };

  const defaultPrompt = `Create a personalized Instagram DM for {first_name} in {city} who works in {bio}. 
The message should be about offering virtual assistant services to help with business tasks. 
Keep it friendly, professional, and under 500 characters. 
Mention how VA services could specifically help their type of work.
Make it feel personal and not like spam.`;

  return (
    <div className="script-page">
      <div className="script-header">
        <h1>💬 Instagram DM Automation</h1>
        <p>Send personalized direct messages to targeted Instagram users with AI-powered content</p>
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
                <small>Select the bot accounts for DM automation ({selectedAccountIds.length} selected)</small>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="dms-per-account">
                DMs per Account
              </label>
              <input
                type="number"
                id="dms-per-account"
                min="1"
                max="100"
                value={formData.dmsPerAccount}
                onChange={(e) => setFormData(prev => ({...prev, dmsPerAccount: parseInt(e.target.value)}))}
                disabled={isRunning}
              />
              <small>Number of DMs each account should send</small>
            </div>

            <div className="form-group">
              <label htmlFor="target-file">
                Target Accounts File (CSV/Excel) *
              </label>
              <input
                type="file"
                id="target-file"
                accept=".xlsx,.xls,.csv"
                onChange={(e) => e.target.files && handleFileChange('targetFile', e.target.files[0])}
                disabled={isRunning}
                required
              />
              <small>Required: File containing target users to DM (columns: username, first_name, city, bio, etc.)</small>
            </div>

            <div className="form-group">
              <label htmlFor="dm-prompt-file">
                🎲 DM Prompt File with Spintax (Text)
              </label>
              <input
                type="file"
                id="dm-prompt-file"
                accept=".txt"
                onChange={(e) => e.target.files && handleFileChange('dmPromptFile', e.target.files[0])}
                disabled={isRunning}
              />
              <small>
                Upload a text file containing spintax templates (e.g., {"{Hello|Hi|Hey} {first_name}!"}).
                {promptFileContent && (
                  <span className="spintax-status">
                    {formData.customPrompt ? 
                      ' ✅ Spintax template selected and confirmed!' : 
                      ' ⚠️ Please select a spintax option from the previews.'
                    }
                  </span>
                )}
              </small>
              {promptFileContent && !formData.customPrompt && (
                <button 
                  type="button" 
                  className="btn btn-secondary btn-small spintax-preview-btn"
                  onClick={() => setShowSpintaxPreview(true)}
                  disabled={isRunning}
                >
                  🎲 Choose Spintax Template
                </button>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="custom-prompt">
                {formData.customPrompt && promptFileContent ? 
                  '✅ Selected Spintax Template (Ready to Use)' : 
                  'Custom DM Prompt (Alternative to file upload)'
                }
              </label>
              <textarea
                id="custom-prompt"
                value={formData.customPrompt}
                onChange={(e) => setFormData(prev => ({...prev, customPrompt: e.target.value}))}
                disabled={isRunning}
                rows={6}
                placeholder={formData.customPrompt && promptFileContent ? 
                  'Your selected and edited spintax template will appear here...' : 
                  defaultPrompt
                }
                className={formData.customPrompt && promptFileContent ? 'spintax-selected' : ''}
              />
              <small>
                {formData.customPrompt && promptFileContent ? (
                  <>
                    ✅ Spintax template confirmed and ready for DM automation. 
                    <button 
                      type="button" 
                      className="btn-link"
                      onClick={() => setShowSpintaxPreview(true)}
                      disabled={isRunning}
                    >
                      Edit Spintax Template
                    </button>
                  </>
                ) : (
                  <>Custom prompt for AI message generation. Use placeholders like {'{first_name}'}, {'{city}'}, {'{bio}'}</>
                )}
              </small>
            </div>

            <div className="form-actions">
              {!isRunning ? (
                <button type="submit" className="btn btn-primary">
                  Start DM Automation
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
                  isRunning ? 'running' : 'idle'
                }`}></span>
                <span>
                  {isPaused ? '⏸️ Paused (CAPTCHA/2FA)' :
                   scriptStatus?.status === 'completed' ? '✅ Completed' : 
                   scriptStatus?.status === 'error' ? '❌ Error' : 
                   isRunning ? '🔄 Running' : '⏸️ Idle'}
                  {isPaused && <span style={{fontSize: '12px', display: 'block', opacity: 0.8}}>Resuming automatically...</span>}
                </span>
                {scriptStatus && (scriptStatus.status === 'completed' || scriptStatus.status === 'error') && (
                  <small style={{marginLeft: '10px', opacity: 0.7}}>
                    {new Date(scriptStatus.end_time!).toLocaleTimeString()}
                  </small>
                )}
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
          
          {/* Positive Responses Button - Under the logs */}
          <div className="logs-footer">
            <button 
              onClick={viewPositiveResponses}
              className={`btn btn-success btn-small ${(!scriptStatus || scriptStatus.status !== 'completed') ? 'disabled' : ''}`}
              title="View responses from DM recipients"
              disabled={!scriptStatus || scriptStatus.status !== 'completed'}
            >
              💬 Positive Responses
            </button>
          </div>
        </div>
      </div>

      <div className="script-info">
        <h3>How it works:</h3>
        <ol>
          <li>Select Instagram bot accounts from the available list</li>
          <li>Set the number of DMs per account</li>
          <li>Upload target accounts file (optional - uses default if not provided)</li>
          <li>Provide a custom DM prompt or upload a prompt file</li>
          <li>Start the automation - browsers will open automatically for selected accounts</li>
          <li>Monitor progress in real-time</li>
        </ol>
        
        <div className="script-features">
          <h4>Features:</h4>
          <ul>
            <li>✅ AI-powered message personalization</li>
            <li>✅ Advanced Spintax content variation (NEW)</li>
            <li>✅ 8 different message structure templates (NEW)</li>
            <li>✅ Dynamic contextual placeholders (NEW)</li>
            <li>✅ Bulk DM campaigns across multiple accounts</li>
            <li>✅ Dynamic browser opening based on account count in file</li>
            <li>✅ Response tracking and analysis</li>
            <li>✅ Rate limiting and proxy support</li>
            <li>✅ Human-like behavior simulation</li>
            <li>✅ Comprehensive logging and reporting</li>
            <li>✅ Enhanced ban avoidance through message variation</li>
          </ul>
        </div>

        <div className="dm-settings-info">
          <h4>Enhanced DM Content Variation:</h4>
          <p>
            The script now uses advanced content variation techniques to avoid spam detection:
          </p>
          <ul>
            <li><strong>Spintax Processing:</strong> Messages use {'{option1|option2|option3}'} syntax for automatic variation</li>
            <li><strong>8 Message Templates:</strong> Professional, casual, question-based, and story-driven approaches</li>
            <li><strong>Dynamic Placeholders:</strong> Time-sensitive content like {'{day_of_week}'}, {'{time_of_day}'}, {'{season}'}</li>
            <li><strong>Business Context:</strong> Industry-specific benefits and value propositions</li>
            <li><strong>Natural Personalization:</strong> Name, location, and bio integration without repetitive patterns</li>
          </ul>
          <p>
            Each message is structurally unique while maintaining professional quality and relevance to the recipient.
            This advanced variation system significantly reduces the risk of being flagged as spam by Instagram's algorithms.
          </p>
        </div>
      </div>

      {/* Spintax Preview Modal */}
      {showSpintaxPreview && (
        <div className="modal-overlay" onClick={() => setShowSpintaxPreview(false)}>
          <div className="modal-content spintax-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🎲 Spintax Preview & Selection</h2>
              <button 
                className="modal-close"
                onClick={() => setShowSpintaxPreview(false)}
                title="Close"
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              {isGeneratingPreviews ? (
                <div className="loading-spinner">
                  <p>🔄 Generating spintax variations...</p>
                </div>
              ) : (
                <div className="spintax-container">
                  <div className="spintax-instructions">
                    <p><strong>📋 Instructions:</strong></p>
                    <ol>
                      <li>Review the generated variations below</li>
                      <li>Select your preferred option</li>
                      <li>Edit it if needed</li>
                      <li>Confirm to use it for DM automation</li>
                    </ol>
                    <div className="ai-generation-section">
                      <button 
                        className="btn btn-secondary btn-ai-generate"
                        onClick={generateAISamples}
                        disabled={isGeneratingAISamples || !promptFileContent}
                        title="Generate more spintax variations using AI"
                      >
                        {isGeneratingAISamples ? '🤖 Generating...' : '🤖 Generate More Samples with AI'}
                      </button>
                    </div>
                  </div>
                  
                  <div className="spintax-previews-container">
                    <h3>Generated Variations:</h3>
                    <div className="spintax-previews">
                      {spintaxPreviews.map((preview, index) => (
                        <div 
                          key={index} 
                          className={`spintax-option ${selectedSpintaxIndex === index ? 'selected' : ''}`}
                          onClick={() => selectSpintaxOption(index)}
                        >
                          <div className="option-header">
                            <span className="option-number">Option {index + 1}</span>
                            {selectedSpintaxIndex === index && <span className="selected-badge">✓ Selected</span>}
                          </div>
                          <div className="option-content">
                            {preview}
                          </div>
                          <div className="option-stats">
                            {preview.length} characters | {preview.split(' ').length} words
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {selectedSpintaxIndex !== -1 && (
                    <div className="spintax-editor">
                      <h3>✏️ Edit Selected Option (Optional):</h3>
                      <textarea
                        value={editableSpintax}
                        onChange={(e) => setEditableSpintax(e.target.value)}
                        rows={6}
                        placeholder="Edit your selected spintax template here..."
                        className="spintax-edit-textarea"
                      />
                      <div className="editor-stats">
                        {editableSpintax.length} characters | {editableSpintax.split(' ').length} words
                      </div>
                    </div>
                  )}

                  <div className="spintax-actions">
                    <button 
                      className="btn btn-secondary"
                      onClick={() => setShowSpintaxPreview(false)}
                    >
                      Cancel
                    </button>
                    <button 
                      className="btn btn-primary"
                      onClick={confirmSpintaxSelection}
                      disabled={selectedSpintaxIndex === -1 || !editableSpintax.trim()}
                    >
                      Confirm & Use This Template
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Positive Responses Modal */}
      {showResponsesModal && (
        <div className="modal-overlay" onClick={() => setShowResponsesModal(false)}>
          <div className="modal-content responses-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>💬 Positive Responses</h2>
              <button 
                className="modal-close"
                onClick={() => setShowResponsesModal(false)}
                title="Close"
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              {responses.length > 0 ? (
                <div className="responses-container">
                  <div className="responses-summary">
                    <p><strong>Total Responses:</strong> {responses.length}</p>
                  </div>
                  <div className="responses-table">
                    <div className="table-header">
                      <div className="table-cell">Bot Account</div>
                      <div className="table-cell">Responder</div>
                      <div className="table-cell">Message</div>
                      <div className="table-cell">Timestamp</div>
                    </div>
                    {responses.map((response, index) => (
                      <div key={index} className="table-row">
                        <div className="table-cell account-cell">
                          📧 {response.account}
                        </div>
                        <div className="table-cell responder-cell">
                          👤 @{response.responder}
                        </div>
                        <div className="table-cell message-cell">
                          {response.message}
                        </div>
                        <div className="table-cell timestamp-cell">
                          🕒 {new Date(response.timestamp).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="no-responses">
                  <p>🔍 No responses found for this automation.</p>
                  <p>Responses are collected from unread messages in the DM inbox after sending.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DMAutomationPage;
