// PRGrabber Content Script - Drag Instructions

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showDragInstructions') {
    showDragInstructions(request.filename);
  }
  sendResponse({received: true});
});

function showDragInstructions(filename) {
  // Remove existing notifications
  const existing = document.querySelectorAll('.prgrabber-drag-notification');
  existing.forEach(n => n.remove());
  
  // Create drag instruction notification
  const notification = document.createElement('div');
  notification.className = 'prgrabber-drag-notification';
  
  notification.style.cssText = `
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%) !important;
    color: white !important;
    padding: 20px !important;
    border-radius: 12px !important;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3) !important;
    z-index: 999999 !important;
    max-width: 350px !important;
    cursor: pointer !important;
    border: 2px solid rgba(255,255,255,0.2) !important;
    animation: slideInBounce 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) !important;
  `;
  
  notification.innerHTML = `
    <div style="display: flex; align-items: flex-start; gap: 12px;">
      <div style="font-size: 24px; margin-top: 2px;">🎬</div>
      <div style="flex: 1;">
        <div style="font-weight: 700; font-size: 15px; margin-bottom: 8px;">
          Ready for Premiere!
        </div>
        <div style="opacity: 0.95; line-height: 1.4; margin-bottom: 10px;">
          Finder opened with your image selected.
        </div>
        <div style="background: rgba(255,255,255,0.15); padding: 8px 10px; border-radius: 6px; font-size: 13px; line-height: 1.3;">
          <strong>📋 Next:</strong><br>
          Drag from Finder → Premiere timeline
        </div>
        ${filename ? `<div style="opacity: 0.8; font-size: 11px; margin-top: 8px; font-family: monospace;">${filename}</div>` : ''}
      </div>
    </div>
  `;
  
  // Add animation styles
  if (!document.querySelector('#prgrabber-drag-styles')) {
    const style = document.createElement('style');
    style.id = 'prgrabber-drag-styles';
    style.textContent = `
      @keyframes slideInBounce {
        0% { 
          transform: translateX(120%) scale(0.8); 
          opacity: 0; 
        }
        60% { 
          transform: translateX(-10px) scale(1.02); 
          opacity: 1; 
        }
        100% { 
          transform: translateX(0) scale(1); 
          opacity: 1; 
        }
      }
      @keyframes slideOutFade {
        from { 
          transform: translateX(0) scale(1); 
          opacity: 1; 
        }
        to { 
          transform: translateX(120%) scale(0.9); 
          opacity: 0; 
        }
      }
    `;
    document.head.appendChild(style);
  }
  
  document.body.appendChild(notification);
  
  // Auto-remove after 8 seconds (longer for drag instructions)
  setTimeout(() => {
    if (notification.parentNode) {
      notification.style.animation = 'slideOutFade 0.4s ease-in !important';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 400);
    }
  }, 8000);
  
  // Click to dismiss
  notification.addEventListener('click', () => {
    if (notification.parentNode) {
      notification.style.animation = 'slideOutFade 0.4s ease-in !important';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 400);
    }
  });
}