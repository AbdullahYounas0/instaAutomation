interface CaptchaEvent {
  accountUsername: string;
  timestamp: string;
  type: 'captcha' | '2fa' | 'verification';
}

class CaptchaDetector {
  private static instance: CaptchaDetector;
  private detectedEvents: Set<string> = new Set();
  private onCaptchaDetected?: (event: CaptchaEvent) => void;

  private constructor() {}

  public static getInstance(): CaptchaDetector {
    if (!CaptchaDetector.instance) {
      CaptchaDetector.instance = new CaptchaDetector();
    }
    return CaptchaDetector.instance;
  }

  public setOnCaptchaDetected(callback: (event: CaptchaEvent) => void) {
    this.onCaptchaDetected = callback;
  }

  public detectCaptchaInLogs(logs: string[]): void {
    // We need to handle different log formats from different features
    
    // Main pattern - the bell emoji notification that appears in all features
    // This is the most reliable indicator of CAPTCHA/2FA
    const bellPattern = /🔔 Please check the account (\w+) and manually solve the CAPTCHA or 2FA/;
    
    // Fallback pattern - also reliable for notification detection
    const warningPattern = /⚠️ Account (\w+) requires verification\/2FA/;

    // Patterns to EXCLUDE (these are handled automatically by the script)
    const excludePatterns = [
      /save.*login.*info/i,
      /accounts\/onetap/i,
      /Not now.*button/i,
      /Clicked.*Not now/i,
      /Handling.*Save your login info/i
    ];

    logs.forEach(log => {
      // First check if this log should be excluded (automatic handling)
      const shouldExclude = excludePatterns.some(pattern => pattern.test(log));
      if (shouldExclude) {
        console.log('Log excluded from CAPTCHA detection (automatic handling):', log);
        return; // Skip this log
      }

      // First try to extract username from the bell emoji pattern (most reliable)
      let match = log.match(bellPattern);
      let accountUsername = match ? match[1].trim() : null;
      
      // If no match with bell pattern, try the warning pattern
      if (!accountUsername) {
        match = log.match(warningPattern);
        if (match) accountUsername = match[1].trim();
      }
      
      // If we found an account username from either pattern, proceed
      if (accountUsername) {
        console.log('CAPTCHA detected for account:', accountUsername); // Debugging
        
        const currentTime = Date.now();
        const eventKey = `${accountUsername}-${currentTime}`;
        
        // Check if notification was sent in last 5 minutes to avoid duplicates
        const timeWindow = 300000; // 5 minutes
        
        // TypeScript safety: accountUsername is definitely a string at this point
        const recentEventKey = Array.from(this.detectedEvents)
          .find(key => accountUsername && key.startsWith(accountUsername) && 
                 currentTime - parseInt(key.split('-')[1]) < timeWindow);

        if (!recentEventKey) {
          this.detectedEvents.add(eventKey);
          
          const event: CaptchaEvent = {
            accountUsername,
            timestamp: new Date().toISOString(),
            type: 'verification'
          };

          // Trigger the callback
          if (this.onCaptchaDetected) {
            this.onCaptchaDetected(event);
          }

          // Clean up old events after 10 minutes
          setTimeout(() => {
            this.detectedEvents.delete(eventKey);
          }, 600000); // 10 minutes
        }
      }
    });
  }

  // We no longer need getEventType as we're using a fixed type

  public simulateDelay(): Promise<void> {
    // Return a promise that resolves after 5 minutes
    return new Promise(resolve => {
      setTimeout(resolve, 300000); // 5 minutes = 300,000 milliseconds
    });
  }
}

export default CaptchaDetector;
