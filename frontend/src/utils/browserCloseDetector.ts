/**
 * Browser Close Detection Utility
 * Handles automatic script termination when user closes browser/tab
 */

interface ScriptCleanupConfig {
  scriptId: string | null;
  onBrowserClose?: () => void;
}

class BrowserCloseDetector {
  private static instance: BrowserCloseDetector;
  private isBeforeUnloadListenerAdded = false;
  private currentScriptId: string | null = null;
  private onBrowserCloseCallback?: () => void;

  private constructor() {}

  public static getInstance(): BrowserCloseDetector {
    if (!BrowserCloseDetector.instance) {
      BrowserCloseDetector.instance = new BrowserCloseDetector();
    }
    return BrowserCloseDetector.instance;
  }

  /**
   * Set up browser close detection for a running script
   */
  public setupBrowserCloseDetection(config: ScriptCleanupConfig) {
    this.currentScriptId = config.scriptId;
    this.onBrowserCloseCallback = config.onBrowserClose;

    if (config.scriptId && !this.isBeforeUnloadListenerAdded) {
      this.addBeforeUnloadListener();
    } else if (!config.scriptId && this.isBeforeUnloadListenerAdded) {
      this.removeBeforeUnloadListener();
    }
  }

  /**
   * Clean up detection when script stops normally
   */
  public cleanup() {
    this.currentScriptId = null;
    this.onBrowserCloseCallback = undefined;
    this.removeBeforeUnloadListener();
  }

  private addBeforeUnloadListener() {
    if (this.isBeforeUnloadListenerAdded) return;

    // Handle browser/tab close
    window.addEventListener('beforeunload', this.handleBeforeUnload);
    
    // Handle page navigation
    window.addEventListener('unload', this.handleUnload);

    // Handle visibility change (when tab is closed)
    document.addEventListener('visibilitychange', this.handleVisibilityChange);

    this.isBeforeUnloadListenerAdded = true;
  }

  private removeBeforeUnloadListener() {
    if (!this.isBeforeUnloadListenerAdded) return;

    window.removeEventListener('beforeunload', this.handleBeforeUnload);
    window.removeEventListener('unload', this.handleUnload);
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);

    this.isBeforeUnloadListenerAdded = false;
  }

  private handleBeforeUnload = (event: BeforeUnloadEvent) => {
    if (this.currentScriptId) {
      // Show warning to user
      const message = 'You have a running script. Closing will stop the automation.';
      event.preventDefault();
      event.returnValue = message;
      
      // Try to stop the script immediately
      this.stopScriptOnClose();
      
      return message;
    }
  };

  private handleUnload = () => {
    if (this.currentScriptId) {
      this.stopScriptOnClose();
    }
  };

  private handleVisibilityChange = () => {
    // If document becomes hidden and we have a running script
    if (document.hidden && this.currentScriptId) {
      // Use a timeout to check if the tab was actually closed
      setTimeout(() => {
        if (document.hidden && this.currentScriptId) {
          this.stopScriptOnClose();
        }
      }, 1000);
    }
  };

  private stopScriptOnClose() {
    if (!this.currentScriptId) return;

    try {
      // Call the callback if provided
      if (this.onBrowserCloseCallback) {
        this.onBrowserCloseCallback();
      }

      // Make API call to stop the script
      this.sendStopScriptRequest(this.currentScriptId);
    } catch (error) {
      console.error('Error stopping script on browser close:', error);
    }
  }

  private async sendStopScriptRequest(scriptId: string) {
    try {
      // Get token from localStorage
      const token = localStorage.getItem('auth_token');
      
      if (navigator.sendBeacon) {
        // sendBeacon doesn't support custom headers, so we include token in the body
        const formData = new FormData();
        formData.append('reason', 'Browser closed by User');
        if (token) {
          formData.append('token', token);
        }

        navigator.sendBeacon(
          `getApiUrl('/script/${scriptId}/stop`,
          formData
        );
      } else {
        // Fallback for browsers that don't support sendBeacon
        fetch(`getApiUrl('/script/${scriptId}/stop`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          },
          body: JSON.stringify({
            reason: 'Browser closed by User'
          }),
          keepalive: true // Keep request alive during page unload
        }).catch(error => {
          console.error('Error in fallback stop request:', error);
        });
      }
    } catch (error) {
      console.error('Error sending stop script request:', error);
    }
  }
}

export default BrowserCloseDetector;
