// Background script for Copy to Premiere Pro extension

chrome.runtime.onInstalled.addListener(() => {
  // Create context menu for images
  chrome.contextMenus.create({
    id: "copyToPremiereImage",
    title: "📸 Copy to Premiere Pro",
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
      const filename = `premiere_${timestamp}.${extension}`;
      
      // Download image to ~/Downloads/PremiereBridge/
      chrome.downloads.download({
        url: imageUrl,
        filename: `PremiereBridge/${filename}`,
        saveAs: false
      }, (downloadId) => {
        if (chrome.runtime.lastError) {
          console.error('Download failed:', chrome.runtime.lastError);
          showNotification('❌ Failed to copy image to Premiere Pro', 'error');
        } else {
          showNotification(`✅ Image copied to Premiere Pro: ${filename}`, 'success');
          
          // Send message to content script to show in-page notification
          chrome.tabs.sendMessage(tab.id, {
            action: 'showNotification',
            message: '✅ Image copied to Premiere Pro!',
            filename: filename
          });
        }
      });
      
    } catch (error) {
      console.error('Error copying image:', error);
      showNotification('❌ Error copying image to Premiere Pro', 'error');
    }
  }
});

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
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icon48.png',
      title: 'Copy to Premiere Pro',
      message: message
    });
  }
}