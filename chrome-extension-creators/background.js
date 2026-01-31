// Background script for Creators Video Automation extension
let desktopAppPort = 7898;  // Port for desktop app communication

// Create context menu when extension loads
chrome.runtime.onInstalled.addListener(() => {
  console.log('Creators Video Automation extension installed');
  createContextMenu();
  
  // Show welcome notification
  try {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icon48.png',
      title: 'Creators Video Automation',
      message: 'Extension ready! Right-click YouTube videos to send to your app.'
    });
  } catch (error) {
    console.log('Welcome notification failed:', error);
  }
});

// Create context menu for YouTube videos
function createContextMenu() {
  try {
    // Clear existing menus first
    chrome.contextMenus.removeAll(() => {
      // Create simple menu for YouTube pages
      chrome.contextMenus.create({
        id: "send-to-creators",
        title: "📹 Send to Creators",
        contexts: ["page", "link"],
        documentUrlPatterns: ["*://www.youtube.com/*", "*://youtu.be/*"]
      });
      
      console.log('Context menu created successfully');
    });
  } catch (error) {
    console.error('Failed to create context menu:', error);
  }
}

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  let videoUrl = '';

  if (info.menuItemId === "send-to-creators") {
    // Get URL from either the link or the current page
    videoUrl = info.linkUrl || info.pageUrl || tab.url;
  }

  if (videoUrl && isYouTubeUrl(videoUrl)) {
    console.log('Sending video URL to desktop app:', videoUrl);
    sendToDesktopApp(videoUrl);
    
    // Show notification
    showNotification(`Sent to Creators: ${getVideoTitle(videoUrl)}`);
  } else {
    console.log('Not a valid YouTube URL:', videoUrl);
    showNotification('❌ Not a valid YouTube video');
  }
});

// Check if URL is a YouTube video
function isYouTubeUrl(url) {
  return url && (
    url.includes('youtube.com/watch') || 
    url.includes('youtu.be/') ||
    url.includes('m.youtube.com/watch')
  );
}

// Send URL to desktop app via HTTP
async function sendToDesktopApp(url) {
  const desktopUrl = `http://localhost:${desktopAppPort}/paste-url`;
  
  try {
    const response = await fetch(desktopUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: url,
        timestamp: Date.now(),
        source: 'chrome-extension'
      })
    });

    if (response.ok) {
      console.log('Successfully sent URL to desktop app');
      showNotification('✅ Video sent to Creators App!');
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    console.error('Failed to send URL to desktop app:', error);
    showNotification('❌ Could not connect to Creators App. Is it running?');
    
    // Fallback: copy to clipboard
    copyToClipboard(url);
  }
}

// Show notification to user
function showNotification(message) {
  try {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icon48.png',
      title: 'Creators Video Automation',
      message: message
    });
  } catch (error) {
    console.log('Notification failed:', error);
    // Fallback: just log the message
    console.log('NOTIFICATION:', message);
  }
}

// Extract video title from URL (basic)
function getVideoTitle(url) {
  const videoId = extractVideoId(url);
  return videoId ? `Video (${videoId})` : 'YouTube Video';
}

// Extract YouTube video ID
function extractVideoId(url) {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/,
    /youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/
  ];
  
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
}

// Fallback: copy URL to clipboard
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    showNotification('📋 URL copied to clipboard as fallback');
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
  }
}

// Extension initialization complete