// Simple Background Script - Creators Video Automation
console.log('🚀 Creators extension starting...');

// Create context menu when extension loads
chrome.runtime.onInstalled.addListener(() => {
  console.log('✅ Extension installed, creating context menu...');
  
  // Remove any existing menus
  chrome.contextMenus.removeAll(() => {
    console.log('🧹 Cleared old menus');
    
    // Create new menu
    chrome.contextMenus.create({
      id: "send-to-creators",
      title: "📹 Send to Creators",
      contexts: ["page", "link"],
      documentUrlPatterns: ["*://www.youtube.com/*", "*://youtu.be/*"]
    }, () => {
      if (chrome.runtime.lastError) {
        console.error('❌ Menu creation failed:', chrome.runtime.lastError);
      } else {
        console.log('✅ Context menu created successfully');
      }
    });
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  console.log('🖱️ Context menu clicked:', info);
  
  const videoUrl = info.linkUrl || info.pageUrl || tab.url;
  console.log('🔗 URL detected:', videoUrl);
  
  if (videoUrl && videoUrl.includes('youtube.com')) {
    console.log('✅ Valid YouTube URL, sending to desktop app...');
    sendToDesktopApp(videoUrl);
  } else {
    console.log('❌ Not a YouTube URL');
  }
});

// Send URL to desktop app
async function sendToDesktopApp(url) {
  try {
    console.log('📡 Sending to desktop app:', url);
    
    const response = await fetch('http://localhost:7898/paste-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: url,
        timestamp: Date.now(),
        source: 'chrome-extension'
      })
    });

    if (response.ok) {
      console.log('✅ Successfully sent to desktop app');
      showNotification('✅ Video sent to Creators App!');
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    console.error('❌ Failed to send URL:', error);
    showNotification('❌ Could not connect to Creators App');
  }
}

// Simple notification
function showNotification(message) {
  try {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icon48.png',
      title: 'Creators Video Automation',
      message: message
    });
  } catch (error) {
    console.log('Notification failed, using console:', message);
  }
}