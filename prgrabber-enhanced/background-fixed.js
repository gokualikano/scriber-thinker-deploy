// PRGrabber Enhanced - Fixed Background Script

const PREMIERE_BRIDGE = 'http://localhost:8590';

chrome.runtime.onInstalled.addListener(() => {
  // Create context menu for images
  chrome.contextMenus.create({
    id: "prgrabber-paste",
    title: "🎬 Paste to Premiere Timeline",
    contexts: ["image"]
  });
  
  // Backup download option
  chrome.contextMenus.create({
    id: "prgrabber-download",
    title: "📁 Download for Premiere",
    contexts: ["image"]
  });
  
  console.log('PRGrabber Enhanced loaded');
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  console.log('Context menu clicked:', info.menuItemId);
  
  if (info.srcUrl) {
    if (info.menuItemId === "prgrabber-paste") {
      handleDirectPaste(info.srcUrl, tab);
    } else if (info.menuItemId === "prgrabber-download") {
      handleDownload(info.srcUrl, tab);
    }
  }
});

function handleDirectPaste(imageUrl, tab) {
  console.log('Handling direct paste for:', imageUrl);
  
  // Try bridge service first
  fetch(`${PREMIERE_BRIDGE}/paste-image`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ imageUrl: imageUrl })
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    } else {
      throw new Error('Bridge service unavailable');
    }
  })
  .then(result => {
    console.log('Bridge success:', result);
    showNotification('⚡ Ready to paste in Premiere Pro!', 'success');
    
    // Send notification to page
    chrome.tabs.sendMessage(tab.id, {
      action: 'showPasteNotification',
      message: '⚡ Press Cmd+V in Premiere timeline!',
      enhanced: true
    }).catch(err => console.log('Tab message failed:', err));
  })
  .catch(error => {
    console.log('Bridge unavailable, using clipboard method...', error);
    
    // Fallback: Copy to clipboard using content script
    chrome.tabs.sendMessage(tab.id, {
      action: 'copyImageToClipboard',
      imageUrl: imageUrl
    }).catch(err => console.log('Clipboard fallback failed:', err));
    
    showNotification('📋 Copied to clipboard - paste in Premiere!', 'info');
  });
}

function handleDownload(imageUrl, tab) {
  console.log('Handling download for:', imageUrl);
  
  try {
    const timestamp = new Date().toISOString()
      .replace(/[-:]/g, '')
      .slice(2, 14);
    
    const extension = getImageExtension(imageUrl);
    const filename = `pr_${timestamp}.${extension}`;
    
    chrome.downloads.download({
      url: imageUrl,
      filename: `PRGrabber/${filename}`,
      saveAs: false
    }, (downloadId) => {
      if (chrome.runtime.lastError) {
        console.error('Download failed:', chrome.runtime.lastError);
        showNotification('❌ Download failed', 'error');
      } else {
        console.log('Download success:', downloadId);
        showNotification(`📁 ${filename} downloaded`, 'success');
        setTimeout(() => {
          if (downloadId) {
            chrome.downloads.show(downloadId);
          }
        }, 500);
      }
    });
    
  } catch (error) {
    console.error('Download error:', error);
    showNotification('❌ Download failed', 'error');
  }
}

function getImageExtension(url) {
  try {
    const urlObj = new URL(url);
    const path = urlObj.pathname;
    const match = path.match(/\.([a-zA-Z0-9]+)$/);
    if (match) {
      const ext = match[1].toLowerCase();
      if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)) {
        return ext;
      }
    }
  } catch (e) {
    console.log('Extension detection failed:', e);
  }
  return 'jpg';
}

function showNotification(message, type) {
  if (chrome.notifications) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icon48.png',
      title: 'PRGrabber Enhanced',
      message: message
    }, (notificationId) => {
      if (chrome.runtime.lastError) {
        console.log('Notification failed:', chrome.runtime.lastError);
      } else {
        console.log('Notification shown:', message);
      }
    });
  } else {
    console.log('Notifications not available');
  }
}

// Health check for bridge service - simplified
setInterval(() => {
  fetch(`${PREMIERE_BRIDGE}/status`)
    .then(response => response.ok)
    .catch(() => false);
}, 30000);