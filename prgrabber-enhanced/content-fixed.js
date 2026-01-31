// PRGrabber Enhanced Content Script - Fixed

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Content script received:', request.action);
  
  if (request.action === 'copyImageToClipboard') {
    copyImageToClipboard(request.imageUrl);
  } else if (request.action === 'showPasteNotification') {
    showPasteNotification(request.message, request.enhanced);
  }
  
  // Always send response
  sendResponse({received: true});
});

function copyImageToClipboard(imageUrl) {
  console.log('Copying image to clipboard:', imageUrl);
  
  try {
    // Create a temporary canvas to convert image URL to blob
    const img = new Image();
    img.crossOrigin = 'anonymous';
    
    img.onload = function() {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        // Convert canvas to blob
        canvas.toBlob((blob) => {
          if (blob && navigator.clipboard) {
            // Write to clipboard
            navigator.clipboard.write([
              new ClipboardItem({ [blob.type]: blob })
            ]).then(() => {
              console.log('Image copied to clipboard');
              showPasteNotification('📋 Image copied - press Cmd+V in Premiere!', false);
            }).catch(clipError => {
              console.error('Clipboard write failed:', clipError);
              showPasteNotification('⚠️ Copy failed - use download option', false);
            });
          } else {
            console.error('Clipboard API not available or blob creation failed');
            showPasteNotification('⚠️ Clipboard not supported - use download option', false);
          }
        }, 'image/png');
        
      } catch (canvasError) {
        console.error('Canvas processing failed:', canvasError);
        showPasteNotification('⚠️ Image processing failed', false);
      }
    };
    
    img.onerror = function() {
      console.error('Image load failed');
      showPasteNotification('⚠️ Could not load image', false);
    };
    
    img.src = imageUrl;
    
  } catch (error) {
    console.error('Copy to clipboard failed:', error);
    showPasteNotification('⚠️ Clipboard access failed', false);
  }
}

function showPasteNotification(message, enhanced) {
  enhanced = enhanced || false;
  console.log('Showing notification:', message, 'enhanced:', enhanced);
  
  // Remove any existing notifications
  const existingNotifications = document.querySelectorAll('.prgrabber-notification');
  existingNotifications.forEach(n => n.remove());
  
  // Create floating notification
  const notification = document.createElement('div');
  notification.className = 'prgrabber-notification';
  
  const bgColor = enhanced 
    ? 'linear-gradient(135deg, #00d4ff 0%, #0066cc 100%)'  // Blue for enhanced
    : 'linear-gradient(135deg, #ff6b35 0%, #cc4400 100%)'; // Orange for clipboard
  
  const icon = enhanced ? '⚡' : '📋';
  
  notification.style.cssText = `
    position: fixed !important;
    top: 20px !important;
    right: 20px !important;
    background: ${bgColor} !important;
    color: white !important;
    padding: 16px 20px !important;
    border-radius: 10px !important;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3) !important;
    z-index: 999999 !important;
    max-width: 300px !important;
    cursor: pointer !important;
    border: 2px solid rgba(255,255,255,0.3) !important;
  `;
  
  notification.innerHTML = `
    <div style="display: flex; align-items: center; gap: 10px;">
      <div style="font-size: 20px;">${icon}</div>
      <div>
        <div style="font-weight: 700; margin-bottom: 2px;">PRGrabber</div>
        <div style="opacity: 0.95; font-size: 13px; line-height: 1.3;">
          ${message}
        </div>
      </div>
    </div>
  `;
  
  try {
    document.body.appendChild(notification);
    console.log('Notification added to page');
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
        console.log('Notification removed');
      }
    }, 5000);
    
    // Click to dismiss
    notification.addEventListener('click', () => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
        console.log('Notification dismissed by click');
      }
    });
    
  } catch (error) {
    console.error('Failed to show notification:', error);
  }
}