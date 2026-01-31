// Enhanced background script for Copy to Premiere Pro extension
// Communicates with local Premiere Bridge Server

const BRIDGE_SERVER = 'http://localhost:8589';

chrome.runtime.onInstalled.addListener(() => {
  // Create context menu for images
  chrome.contextMenus.create({
    id: "copyToPremiereImage",
    title: "📸 Copy to Premiere Pro (Paste Ready)",
    contexts: ["image"]
  });
  
  // Create context menu for links to images
  chrome.contextMenus.create({
    id: "copyToPremiereLink", 
    title: "📸 Copy Image to Premiere Pro",
    contexts: ["link"],
    documentUrlPatterns: ["*://*/*"]
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  let imageUrl = null;
  
  if (info.menuItemId === "copyToPremiereImage") {
    imageUrl = info.srcUrl;
  } else if (info.menuItemId === "copyToPremiereLink") {
    imageUrl = info.linkUrl;
  }
  
  if (imageUrl) {
    try {
      // Generate filename with timestamp
      const now = new Date();
      const timestamp = now.toISOString()
        .replace(/[-:]/g, '')
        .replace(/\..+/, '')
        .slice(0, 15); // YYYYMMDDHHMMSS
      
      const extension = getImageExtension(imageUrl);
      const filename = `browser_${timestamp}.${extension}`;
      
      // Send image to bridge server
      const response = await fetch(`${BRIDGE_SERVER}/copy-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          imageUrl: imageUrl,
          filename: filename
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        // Show success notification
        showNotification('✅ Image ready for Cmd+V in Premiere Pro!', 'success');
        
        // Send message to content script
        chrome.tabs.sendMessage(tab.id, {
          action: 'showNotification',
          message: '✅ Ready for Cmd+V in Premiere Pro!',
          filename: result.filename,
          enhanced: true
        });
        
      } else {
        // Fallback to regular download if server is not available
        console.log('Bridge server not available, using fallback download...');
        await fallbackDownload(imageUrl, filename);
        
        showNotification('📁 Image saved to PremiereBridge folder', 'info');
        
        chrome.tabs.sendMessage(tab.id, {
          action: 'showNotification', 
          message: '📁 Drag from PremiereBridge folder to timeline',
          filename: filename,
          enhanced: false
        });
      }
      
    } catch (error) {
      console.error('Error communicating with bridge server:', error);
      
      // Fallback to regular download
      const timestamp = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
      const extension = getImageExtension(imageUrl);
      const filename = `browser_${timestamp}.${extension}`;
      
      await fallbackDownload(imageUrl, filename);
      
      showNotification('📁 Image saved (bridge offline)', 'warning');
    }
  }
});

async function fallbackDownload(imageUrl, filename) {
  // Regular Chrome download as fallback
  chrome.downloads.download({
    url: imageUrl,
    filename: `PremiereBridge/${filename}`,
    saveAs: false
  });
}

function getImageExtension(url) {
  const match = url.match(/\.([a-zA-Z0-9]+)(?:\?|$)/);
  if (match) {
    const ext = match[1].toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) {
      return ext === 'jpg' ? 'jpg' : ext;
    }
  }
  return 'png'; // Default fallback
}

function showNotification(message, type) {
  if (chrome.notifications) {
    const iconMap = {
      success: 'icon48.png',
      warning: 'icon48.png', 
      error: 'icon48.png',
      info: 'icon48.png'
    };
    
    chrome.notifications.create({
      type: 'basic',
      iconUrl: iconMap[type] || 'icon48.png',
      title: 'Copy to Premiere Pro',
      message: message
    });
  }
}

// Health check for bridge server
setInterval(async () => {
  try {
    const response = await fetch(`${BRIDGE_SERVER}/status`);
    if (response.ok) {
      const status = await response.json();
      console.log('Bridge server status:', status);
    }
  } catch (error) {
    // Server offline - that's okay, we have fallback
  }
}, 30000); // Check every 30 seconds