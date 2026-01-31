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
  chrome.contextMenus.create({
    id: "paste-to-creators",
    title: "📹 Send to Creators",
    contexts: ["link", "page"],
    targetUrlPatterns: [
      "*://www.youtube.com/watch?v=*",
      "*://youtu.be/*",
      "*://m.youtube.com/watch?v=*"
    ]
  });

  // Also create menu for when right-clicking on YouTube pages
  chrome.contextMenus.create({
    id: "paste-current-video",
    title: "📹 Send Current Video to Creators", 
    contexts: ["page"],
    documentUrlPatterns: [
      "*://www.youtube.com/watch?v=*",
      "*://youtu.be/*",
      "*://m.youtube.com/watch?v=*"
    ]
  });
}

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  let videoUrl = '';

  if (info.menuItemId === "paste-to-creators" && info.linkUrl) {
    // Right-clicked on a YouTube link
    videoUrl = info.linkUrl;
  } else if (info.menuItemId === "paste-current-video" && info.pageUrl) {
    // Right-clicked on current YouTube page
    videoUrl = info.pageUrl;
  }

  if (videoUrl) {
    console.log('Sending video URL to desktop app:', videoUrl);
    sendToDesktopApp(videoUrl);
    
    // Show notification
    showNotification(`Sent to Creators App: ${getVideoTitle(videoUrl)}`);
  }
});

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