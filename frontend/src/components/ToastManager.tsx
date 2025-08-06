import React, { useEffect } from 'react';
import { toast, ToastContainer, ToastOptions } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { generateBeepSound } from '../utils/notificationSound';

interface ToastManagerProps {
  children: React.ReactNode;
}

const ToastManager: React.FC<ToastManagerProps> = ({ children }) => {
  const playNotificationSound = () => {
    try {
      // Generate WhatsApp-like notification sound
      generateBeepSound(660, 200); // First beep
      setTimeout(() => generateBeepSound(880, 200), 100); // Second beep after 100ms
    } catch (e) {
      console.log('Audio play failed:', e);
    }
  };

  const showCaptchaToast = (accountUsername: string) => {
    const toastId = `captcha-${accountUsername}`;
    
    // Play notification sound
    playNotificationSound();
    
    const toastOptions: ToastOptions = {
      position: 'bottom-right',
      autoClose: 30000, // 30 seconds (to match backend timeout)
      hideProgressBar: false,
      closeOnClick: true, // Allow clicking on toast to close it
      pauseOnHover: true,
      draggable: true, // Enable dragging
      progress: undefined,
      theme: 'colored',
      toastId: toastId,
      className: 'captcha-toast',
      style: {
        backgroundColor: '#ff9800',
        color: 'white',
        fontSize: '14px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        borderRadius: '8px',
        minHeight: '80px'
      }
    };

    toast.warn(
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ fontSize: '24px' }}>🔐</div>
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: '4px', fontSize: '16px', color: '#fff' }}>
            Account: <span style={{ color: '#ffff00' }}>{accountUsername}</span>
          </div>
          <div style={{ fontSize: '13px', opacity: 1.0, marginBottom: '2px' }}>
            CAPTCHA/2FA verification required
          </div>
          <div style={{ fontSize: '12px', opacity: 0.9 }}>
            Please manually solve the verification
          </div>
          <div style={{ fontSize: '11px', marginTop: '4px', opacity: 0.8 }}>
            Auto-resuming in 30 seconds...
          </div>
        </div>
      </div>,
      toastOptions
    );
  };

  // Expose the function globally so other components can use it
  useEffect(() => {
    (window as any).showCaptchaToast = showCaptchaToast;
    
    return () => {
      delete (window as any).showCaptchaToast;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // We intentionally want this to run only once

  return (
    <>
      {children}
      <ToastContainer
        position="bottom-right"
        autoClose={30000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick={true}
        rtl={false}
        pauseOnFocusLoss
        draggable={true}
        pauseOnHover
        theme="light"
        closeButton={true}
      />
      <style>{`
        .captcha-toast {
          background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%) !important;
          border-left: 4px solid #ff5722 !important;
          border: 2px solid #ff5722 !important;
        }
        
        .Toastify__toast--warning.captcha-toast {
          background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%) !important;
          animation: pulse 2s ease-in-out infinite alternate;
        }
        
        .Toastify__toast--warning.captcha-toast .Toastify__close-button {
          color: white !important;
          opacity: 0.8 !important;
          font-size: 20px !important;
        }
        
        .Toastify__toast--warning.captcha-toast .Toastify__close-button:hover {
          opacity: 1 !important;
        }
        
        .Toastify__close-button {
          position: absolute;
          top: 8px;
          right: 8px;
          cursor: pointer !important;
        }
        
        @keyframes pulse {
          from {
            box-shadow: 0 4px 12px rgba(255, 87, 34, 0.3);
          }
          to {
            box-shadow: 0 6px 16px rgba(255, 87, 34, 0.6);
          }
        }
      `}</style>
    </>
  );
};

export default ToastManager;
