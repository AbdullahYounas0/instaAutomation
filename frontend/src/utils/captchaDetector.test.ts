import CaptchaDetector from './captchaDetector';

// Mock console methods for testing
const mockConsole = {
  log: jest.spyOn(console, 'log').mockImplementation(() => {}),
  error: jest.spyOn(console, 'error').mockImplementation(() => {}),
  warn: jest.spyOn(console, 'warn').mockImplementation(() => {}),
};

interface CaptchaEvent {
  accountUsername: string;
  timestamp: string;
  type: 'captcha' | '2fa' | 'verification';
}

describe('CaptchaDetector Utility Tests', () => {
  let detector: CaptchaDetector;

  beforeEach(() => {
    detector = CaptchaDetector.getInstance();
    jest.clearAllMocks();
    mockConsole.log.mockClear();
    mockConsole.error.mockClear();
    mockConsole.warn.mockClear();
  });

  afterEach(() => {
    // Clean up any global state if needed
  });

  describe('Singleton Pattern', () => {
    it('should return the same instance when called multiple times', () => {
      const instance1 = CaptchaDetector.getInstance();
      const instance2 = CaptchaDetector.getInstance();
      
      expect(instance1).toBe(instance2);
    });

    it('should maintain state across multiple getInstance calls', () => {
      const instance1 = CaptchaDetector.getInstance();
      const mockCallback = jest.fn();
      
      instance1.setOnCaptchaDetected(mockCallback);
      
      const instance2 = CaptchaDetector.getInstance();
      
      expect(instance2).toBe(instance1);
    });
  });

  describe('Callback Management', () => {
    it('should accept callback function for CAPTCHA detection', () => {
      const mockCallback = jest.fn();
      
      expect(() => {
        detector.setOnCaptchaDetected(mockCallback);
      }).not.toThrow();
    });

    it('should call callback when CAPTCHA is detected in logs', () => {
      const mockCallback = jest.fn();
      detector.setOnCaptchaDetected(mockCallback);
      
      const testLogs = [
        '🔔 Please check the account testuser123 and manually solve the CAPTCHA or 2FA'
      ];
      
      detector.detectCaptchaInLogs(testLogs);
      
      expect(mockCallback).toHaveBeenCalledTimes(1);
      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          accountUsername: 'testuser123',
          type: 'verification',
          timestamp: expect.any(String)
        })
      );
    });

    it('should update callback when called multiple times', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      
      detector.setOnCaptchaDetected(callback1);
      detector.setOnCaptchaDetected(callback2);
      
      const testLogs = ['🔔 Please check the account testuser and manually solve the CAPTCHA or 2FA'];
      detector.detectCaptchaInLogs(testLogs);
      
      expect(callback1).not.toHaveBeenCalled();
      expect(callback2).toHaveBeenCalledTimes(1);
    });
  });

  describe('Log Detection Functionality', () => {
    it('should detect bell emoji pattern in logs', () => {
      const mockCallback = jest.fn();
      detector.setOnCaptchaDetected(mockCallback);
      
      const testLogs = [
        'Some normal log entry',
        '🔔 Please check the account myaccount and manually solve the CAPTCHA or 2FA',
        'Another normal log'
      ];
      
      detector.detectCaptchaInLogs(testLogs);
      
      expect(mockCallback).toHaveBeenCalledTimes(1);
      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          accountUsername: 'myaccount',
          type: 'verification'
        })
      );
    });

    it('should detect warning pattern in logs', () => {
      const mockCallback = jest.fn();
      detector.setOnCaptchaDetected(mockCallback);
      
      const testLogs = [
        '⚠️ Account warningtest requires verification/2FA'
      ];
      
      detector.detectCaptchaInLogs(testLogs);
      
      expect(mockCallback).toHaveBeenCalledTimes(1);
      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          accountUsername: 'warningtest',
          type: 'verification'
        })
      );
    });

    it('should ignore logs from "Save your login info?" page handling', () => {
      const mockCallback = jest.fn();
      detector.setOnCaptchaDetected(mockCallback);
      
      const testLogs = [
        '[testuser] Handling \'Save your login info?\' dialog...',
        '[testuser] ✅ Clicked \'Not now\' on save login info dialog',
        'accounts/onetap page detected',
        'Looking for \'Not now\' button on save login info dialog...',
        '🔔 Please check the account realcaptcha and manually solve the CAPTCHA or 2FA'
      ];
      
      detector.detectCaptchaInLogs(testLogs);
      
      // Should only trigger for the real CAPTCHA, not the "Save login info" handling
      expect(mockCallback).toHaveBeenCalledTimes(1);
      expect(mockCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          accountUsername: 'realcaptcha',
          type: 'verification'
        })
      );
    });

    it('should handle multiple CAPTCHA detections in different logs', () => {
      const mockCallback = jest.fn();
      detector.setOnCaptchaDetected(mockCallback);
      
      const testLogs = [
        '🔔 Please check the account user1 and manually solve the CAPTCHA or 2FA',
        '⚠️ Account user2 requires verification/2FA',
        '🔔 Please check the account user3 and manually solve the CAPTCHA or 2FA'
      ];
      
      detector.detectCaptchaInLogs(testLogs);
      
      expect(mockCallback).toHaveBeenCalledTimes(3);
    });

    it('should ignore logs without CAPTCHA patterns', () => {
      const mockCallback = jest.fn();
      detector.setOnCaptchaDetected(mockCallback);
      
      const testLogs = [
        'Normal log entry',
        'Another normal entry',
        'User logged in successfully',
        'Post uploaded'
      ];
      
      detector.detectCaptchaInLogs(testLogs);
      
      expect(mockCallback).not.toHaveBeenCalled();
    });

    it('should handle empty log arrays', () => {
      const mockCallback = jest.fn();
      detector.setOnCaptchaDetected(mockCallback);
      
      expect(() => {
        detector.detectCaptchaInLogs([]);
      }).not.toThrow();
      
      expect(mockCallback).not.toHaveBeenCalled();
    });

    it('should prevent duplicate notifications within time window', async () => {
      const mockCallback = jest.fn();
      detector.setOnCaptchaDetected(mockCallback);
      
      const testLogs = [
        '🔔 Please check the account sameuser and manually solve the CAPTCHA or 2FA'
      ];
      
      // First detection
      detector.detectCaptchaInLogs(testLogs);
      expect(mockCallback).toHaveBeenCalledTimes(1);
      
      // Second detection for same user should be ignored
      detector.detectCaptchaInLogs(testLogs);
      expect(mockCallback).toHaveBeenCalledTimes(1);
    });
  });

  describe('Delay Simulation', () => {
    it('should provide simulateDelay method', () => {
      expect(typeof detector.simulateDelay).toBe('function');
    });

    it('should return a promise from simulateDelay', () => {
      const result = detector.simulateDelay();
      expect(result).toBeInstanceOf(Promise);
    });
  });

  describe('Integration Readiness', () => {
    it('should be ready for React component integration', () => {
      expect(CaptchaDetector.getInstance).toBeDefined();
      expect(typeof CaptchaDetector.getInstance).toBe('function');
    });

    it('should provide expected interface', () => {
      const instance = CaptchaDetector.getInstance();
      
      expect(instance).toBeTruthy();
      expect(typeof instance.setOnCaptchaDetected).toBe('function');
      expect(typeof instance.detectCaptchaInLogs).toBe('function');
      expect(typeof instance.simulateDelay).toBe('function');
    });

    it('should handle concurrent usage from multiple components', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      
      const instance1 = CaptchaDetector.getInstance();
      const instance2 = CaptchaDetector.getInstance();
      
      // Both instances should be the same
      expect(instance1).toBe(instance2);
      
      // Setting callbacks shouldn't interfere with singleton behavior
      instance1.setOnCaptchaDetected(callback1);
      expect(instance2).toBe(instance1);
    });
  });

  describe('Error Handling', () => {
    it('should handle malformed log entries gracefully', () => {
      const mockCallback = jest.fn();
      detector.setOnCaptchaDetected(mockCallback);
      
      const malformedLogs = [
        null as any,
        undefined as any,
        '',
        '🔔 Please check the account',  // Missing username
        '⚠️ Account requires verification/2FA'  // Missing username
      ];
      
      expect(() => {
        detector.detectCaptchaInLogs(malformedLogs.filter(log => log !== null && log !== undefined));
      }).not.toThrow();
    });

    it('should handle callback execution errors', () => {
      const errorCallback = jest.fn().mockImplementation(() => {
        throw new Error('Callback error');
      });
      
      detector.setOnCaptchaDetected(errorCallback);
      
      const testLogs = ['🔔 Please check the account testuser and manually solve the CAPTCHA or 2FA'];
      
      expect(() => {
        detector.detectCaptchaInLogs(testLogs);
      }).not.toThrow();
    });
  });
});