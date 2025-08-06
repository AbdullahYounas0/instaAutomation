import { generateBeepSound } from './notificationSound';

// Mock the AudioContext and related Web Audio API
const mockAudioContext = {
  createOscillator: jest.fn(),
  createGain: jest.fn(),
  destination: {},
  currentTime: 0,
};

const mockOscillator = {
  connect: jest.fn(),
  start: jest.fn(),
  stop: jest.fn(),
  frequency: { value: 0 },
  type: 'sine',
};

const mockGainNode = {
  connect: jest.fn(),
  gain: { value: 0 },
};

beforeEach(() => {
  mockAudioContext.createOscillator.mockReturnValue(mockOscillator);
  mockAudioContext.createGain.mockReturnValue(mockGainNode);
  
  // Mock the global AudioContext
  (global as any).AudioContext = jest.fn().mockImplementation(() => mockAudioContext);
  (global as any).webkitAudioContext = jest.fn().mockImplementation(() => mockAudioContext);
  
  jest.clearAllMocks();
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('NotificationSound Utility Tests', () => {
  describe('generateBeepSound function', () => {
    it('should be defined and exportable', () => {
      expect(generateBeepSound).toBeDefined();
      expect(typeof generateBeepSound).toBe('function');
    });

    it('should execute without throwing errors', () => {
      expect(() => {
        generateBeepSound();
      }).not.toThrow();
    });

    it('should create audio context when available', () => {
      generateBeepSound();
      expect(global.AudioContext).toHaveBeenCalled();
    });

    it('should create oscillator and gain nodes', () => {
      generateBeepSound();
      expect(mockAudioContext.createOscillator).toHaveBeenCalled();
      expect(mockAudioContext.createGain).toHaveBeenCalled();
    });

    it('should connect audio nodes properly', () => {
      generateBeepSound();
      expect(mockOscillator.connect).toHaveBeenCalledWith(mockGainNode);
      expect(mockGainNode.connect).toHaveBeenCalledWith(mockAudioContext.destination);
    });

    it('should start and stop oscillator', () => {
      generateBeepSound();
      expect(mockOscillator.start).toHaveBeenCalled();
      expect(mockOscillator.stop).toHaveBeenCalled();
    });

    it('should set appropriate frequency for beep sound', () => {
      generateBeepSound();
      // Check that frequency was set to a reasonable beep sound value
      expect(mockOscillator.frequency.value).toBeGreaterThan(0);
    });

    it('should set appropriate gain/volume', () => {
      generateBeepSound();
      expect(mockGainNode.gain.value).toBeGreaterThanOrEqual(0);
      expect(mockGainNode.gain.value).toBeLessThanOrEqual(1);
    });

    it('should handle multiple rapid calls', () => {
      expect(() => {
        generateBeepSound();
        generateBeepSound();
        generateBeepSound();
      }).not.toThrow();

      expect(mockAudioContext.createOscillator).toHaveBeenCalledTimes(3);
      expect(mockOscillator.start).toHaveBeenCalledTimes(3);
    });

    it('should work with webkit audio context fallback', () => {
      // Remove standard AudioContext
      delete (global as any).AudioContext;
      
      generateBeepSound();
      expect((global as any).webkitAudioContext).toHaveBeenCalled();
    });

    it('should handle missing audio context gracefully', () => {
      // Remove both AudioContext implementations
      delete (global as any).AudioContext;
      delete (global as any).webkitAudioContext;
      
      expect(() => {
        generateBeepSound();
      }).not.toThrow();
    });

    it('should handle audio context creation errors', () => {
      (global as any).AudioContext = jest.fn().mockImplementation(() => {
        throw new Error('AudioContext creation failed');
      });

      expect(() => {
        generateBeepSound();
      }).not.toThrow();
    });

    it('should handle oscillator creation errors', () => {
      mockAudioContext.createOscillator.mockImplementation(() => {
        throw new Error('Oscillator creation failed');
      });

      expect(() => {
        generateBeepSound();
      }).not.toThrow();
    });

    it('should handle gain node creation errors', () => {
      mockAudioContext.createGain.mockImplementation(() => {
        throw new Error('Gain node creation failed');
      });

      expect(() => {
        generateBeepSound();
      }).not.toThrow();
    });

    it('should handle start/stop errors gracefully', () => {
      mockOscillator.start.mockImplementation(() => {
        throw new Error('Start failed');
      });
      mockOscillator.stop.mockImplementation(() => {
        throw new Error('Stop failed');
      });

      expect(() => {
        generateBeepSound();
      }).not.toThrow();
    });
  });

  describe('Browser Compatibility', () => {
    it('should work in environments with standard AudioContext', () => {
      (global as any).AudioContext = jest.fn().mockImplementation(() => mockAudioContext);
      delete (global as any).webkitAudioContext;

      expect(() => {
        generateBeepSound();
      }).not.toThrow();
    });

    it('should work in environments with webkit AudioContext only', () => {
      delete (global as any).AudioContext;
      (global as any).webkitAudioContext = jest.fn().mockImplementation(() => mockAudioContext);

      expect(() => {
        generateBeepSound();
      }).not.toThrow();
    });

    it('should degrade gracefully in environments without audio support', () => {
      delete (global as any).AudioContext;
      delete (global as any).webkitAudioContext;

      expect(() => {
        generateBeepSound();
      }).not.toThrow();
    });
  });

  describe('Integration with Toast System', () => {
    it('should be suitable for integration with CAPTCHA notifications', () => {
      // Test that the function works as expected for toast integration
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
      const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      generateBeepSound();

      // Should not log errors in normal operation
      expect(errorSpy).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
      errorSpy.mockRestore();
    });

    it('should provide immediate feedback for urgent notifications', () => {
      const startTime = Date.now();
      
      generateBeepSound();
      
      const endTime = Date.now();
      const executionTime = endTime - startTime;
      
      // Should execute quickly for immediate user feedback
      expect(executionTime).toBeLessThan(100); // 100ms threshold
    });

    it('should be safe for repeated calls as used in CAPTCHA detection', () => {
      // Simulate the dual beep pattern used in ToastManager
      expect(() => {
        generateBeepSound();
        setTimeout(() => generateBeepSound(), 300);
      }).not.toThrow();

      expect(mockAudioContext.createOscillator).toHaveBeenCalledTimes(2);
    });
  });
});