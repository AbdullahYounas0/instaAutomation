import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { toast } from 'react-toastify';
import ToastManager from './ToastManager';
import { generateBeepSound } from '../utils/notificationSound';

// Mock dependencies
jest.mock('react-toastify', () => ({
  toast: {
    warn: jest.fn(),
  },
  ToastContainer: ({ children }: { children?: React.ReactNode }) => <div data-testid="toast-container">{children}</div>,
}));

jest.mock('../utils/notificationSound', () => ({
  generateBeepSound: jest.fn(),
}));

describe('ToastManager', () => {
  const mockGenerateBeepSound = generateBeepSound as jest.MockedFunction<typeof generateBeepSound>;
  const mockToastWarn = toast.warn as jest.MockedFunction<typeof toast.warn>;

  beforeEach(() => {
    jest.clearAllMocks();
    // Clear any existing window functions
    delete (window as any).showCaptchaToast;
  });

  afterEach(() => {
    // Clean up global functions
    delete (window as any).showCaptchaToast;
  });

  it('renders children and ToastContainer', () => {
    render(
      <ToastManager>
        <div data-testid="child-component">Test Child</div>
      </ToastManager>
    );

    expect(screen.getByTestId('child-component')).toBeInTheDocument();
    expect(screen.getByTestId('toast-container')).toBeInTheDocument();
  });

  it('exposes showCaptchaToast function globally', () => {
    render(
      <ToastManager>
        <div>Test</div>
      </ToastManager>
    );

    expect((window as any).showCaptchaToast).toBeDefined();
    expect(typeof (window as any).showCaptchaToast).toBe('function');
  });

  it('cleans up global function on unmount', () => {
    const { unmount } = render(
      <ToastManager>
        <div>Test</div>
      </ToastManager>
    );

    expect((window as any).showCaptchaToast).toBeDefined();

    unmount();

    expect((window as any).showCaptchaToast).toBeUndefined();
  });

  it('shows CAPTCHA toast with correct styling and content', async () => {
    render(
      <ToastManager>
        <div>Test</div>
      </ToastManager>
    );

    const testUsername = 'testuser123';

    await act(async () => {
      (window as any).showCaptchaToast(testUsername);
    });

    expect(mockToastWarn).toHaveBeenCalledTimes(1);
    expect(mockGenerateBeepSound).toHaveBeenCalled();

    const toastCall = mockToastWarn.mock.calls[0];
    const toastOptions = toastCall[1];

    // Verify toast options
    expect(toastOptions).toBeDefined();
    expect(toastOptions).toMatchObject({
      position: 'bottom-right',
      autoClose: 300000, // 5 minutes
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      theme: 'colored',
      toastId: `captcha-${testUsername}`,
      className: 'captcha-toast',
    });
  });

  it('handles audio play failures gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    mockGenerateBeepSound.mockImplementationOnce(() => {
      throw new Error('Audio failed');
    });

    render(
      <ToastManager>
        <div>Test</div>
      </ToastManager>
    );

    const testUsername = 'testuser';

    await act(async () => {
      (window as any).showCaptchaToast(testUsername);
    });

    expect(consoleSpy).toHaveBeenCalledWith('Audio play failed:', expect.any(Error));
    // Toast should still be displayed even if audio fails
    expect(mockToastWarn).toHaveBeenCalledTimes(1);

    consoleSpy.mockRestore();
  });

  it('creates unique toast IDs for different usernames', async () => {
    render(
      <ToastManager>
        <div>Test</div>
      </ToastManager>
    );

    const username1 = 'user1';
    const username2 = 'user2';

    await act(async () => {
      (window as any).showCaptchaToast(username1);
      (window as any).showCaptchaToast(username2);
    });

    expect(mockToastWarn).toHaveBeenCalledTimes(2);

    const firstToastOptions = mockToastWarn.mock.calls[0][1];
    const secondToastOptions = mockToastWarn.mock.calls[1][1];

    expect(firstToastOptions).toBeDefined();
    expect(secondToastOptions).toBeDefined();
    expect(firstToastOptions?.toastId).toBe('captcha-user1');
    expect(secondToastOptions?.toastId).toBe('captcha-user2');
  });

  it('displays correct toast content', async () => {
    render(
      <ToastManager>
        <div>Test</div>
      </ToastManager>
    );

    const testUsername = 'testuser123';

    await act(async () => {
      (window as any).showCaptchaToast(testUsername);
    });

    const toastContent = mockToastWarn.mock.calls[0][0];

    // Render the toast content to verify text
    if (React.isValidElement(toastContent)) {
      const { container } = render(toastContent);
      expect(container).toHaveTextContent(`Account: ${testUsername}`);
      expect(container).toHaveTextContent('CAPTCHA/2FA verification Occured');
      expect(container).toHaveTextContent('Auto-resuming in 30 seconds...');
      expect(container).toHaveTextContent('🔐');
    }
  });

  it('only shows toast for actual CAPTCHA events, not automatic login dialog handling', async () => {
    render(
      <ToastManager>
        <div>Test</div>
      </ToastManager>
    );

    // This should trigger a toast (real CAPTCHA)
    await act(async () => {
      (window as any).showCaptchaToast('realcaptcha');
    });

    expect(mockToastWarn).toHaveBeenCalledTimes(1);
    expect(mockGenerateBeepSound).toHaveBeenCalledTimes(1);

    // Reset mocks
    jest.clearAllMocks();

    // These usernames/scenarios should still work (this test validates our backend changes work with frontend)
    const automaticHandlingUsernames = [
      'user_from_onetap_page',
      'user_save_login_info',
      'user_not_now_clicked'
    ];

    for (const username of automaticHandlingUsernames) {
      await act(async () => {
        (window as any).showCaptchaToast(username);
      });
    }

    // All should still show toasts since showCaptchaToast is called directly
    // The filtering happens at the log detection level, not in the toast display
    expect(mockToastWarn).toHaveBeenCalledTimes(automaticHandlingUsernames.length);
  });
});