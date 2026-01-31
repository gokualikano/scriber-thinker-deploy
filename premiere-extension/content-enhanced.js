// Enhanced content script for Copy to Premiere Pro extension

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showNotification') {
    showInPageNotification(request.message, request.filename, request.enhanced);
  }
});

function showInPageNotification(message, filename, enhanced = false) {
  // Create floating notification
  const notification = document.createElement('div');
  
  // Enhanced styling based on mode
  const bgGradient = enhanced 
    ? 'linear-gradient(135deg, #00c851 0%, #007e33 100%)'  // Green for enhanced
    : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'; // Blue for regular
  
  const icon = enhanced ? '⚡' : '📁';
  
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${bgGradient};
    color: white;
    padding: 18px 22px;
    border-radius: 12px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 6px 16px rgba(0,0,0,0.3);
    z-index: 999999;
    max-width: 320px;
    animation: slideIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    cursor: pointer;
    border: 2px solid rgba(255,255,255,0.2);
  `;
  
  notification.innerHTML = `
    <div style="display: flex; align-items: center; gap: 12px;">
      <div style="font-size: 24px; filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3));">${icon}</div>
      <div>
        <div style="font-weight: 700; margin-bottom: 4px; font-size: 15px;">
          Premiere Pro${enhanced ? ' ⚡' : ''}
        </div>
        <div style="opacity: 0.95; font-size: 13px; line-height: 1.3;">
          ${message}
        </div>
        ${filename ? `<div style="opacity: 0.8; font-size: 11px; margin-top: 4px; font-family: 'Monaco', monospace; background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; display: inline-block;">${filename}</div>` : ''}
        ${enhanced ? `<div style="opacity: 0.9; font-size: 12px; margin-top: 6px; font-weight: 600;">Press Cmd+V in Premiere timeline!</div>` : ''}
      </div>
    </div>
  `;
  
  // Add animations
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { 
        transform: translateX(120%) scale(0.8); 
        opacity: 0; 
      }
      to { 
        transform: translateX(0) scale(1); 
        opacity: 1; 
      }
    }
    @keyframes slideOut {
      from { 
        transform: translateX(0) scale(1); 
        opacity: 1; 
      }
      to { 
        transform: translateX(120%) scale(0.8); 
        opacity: 0; 
      }
    }
    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.05); }
    }
  `;
  document.head.appendChild(style);
  
  document.body.appendChild(notification);
  
  // Enhanced mode gets a subtle pulse animation
  if (enhanced) {
    setTimeout(() => {
      notification.style.animation = 'pulse 1.5s ease-in-out 2';
    }, 500);
  }
  
  // Auto-remove after different times based on mode
  const displayTime = enhanced ? 6000 : 4000;  // Enhanced shows longer
  
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.4s cubic-bezier(0.55, 0.085, 0.68, 0.53)';
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
      if (style.parentNode) {
        style.parentNode.removeChild(style);
      }
    }, 400);
  }, displayTime);
  
  // Click to dismiss
  notification.addEventListener('click', () => {
    notification.style.animation = 'slideOut 0.4s cubic-bezier(0.55, 0.085, 0.68, 0.53)';
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 400);
  });
}

// Add subtle visual feedback on image hover (enhanced mode detection)
let hoverTimeout;
document.addEventListener('mouseover', (e) => {
  if (e.target.tagName === 'IMG') {
    clearTimeout(hoverTimeout);
    hoverTimeout = setTimeout(() => {
      // Could add subtle overlay showing "Right-click for Premiere Pro"
      // But keeping it minimal for now
    }, 1000);
  }
});

document.addEventListener('mouseout', (e) => {
  if (e.target.tagName === 'IMG') {
    clearTimeout(hoverTimeout);
  }
});