// PRGrabber Background Script - Dead Simple

chrome.runtime.onInstalled.addListener(() => {
  // Add right-click menu for images
  chrome.contextMenus.create({
    id: "prgrabber",
    title: "🎬 Grab for Premiere Pro",
    contexts: ["image"]
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "prgrabber" && info.srcUrl) {
    try {
      // Get timestamp for unique filename
      const now = new Date();
      const timestamp = now.toISOString()
        .replace(/[-:]/g, '')
        .replace(/\..+/, '')
        .slice(2, 14); // YYMMDDHHMMSS
      
      // Get file extension from URL
      let extension = 'jpg';
      try {
        const url = new URL(info.srcUrl);
        const path = url.pathname;
        const match = path.match(/\.([a-zA-Z0-9]+)$/);
        if (match) {
          const ext = match[1].toLowerCase();
          if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)) {
            extension = ext;
          }
        }
      } catch (e) {
        // Use default jpg
      }
      
      const filename = `pr_${timestamp}.${extension}`;
      
      // Download to PRGrabber folder
      chrome.downloads.download({
        url: info.srcUrl,
        filename: `PRGrabber/${filename}`,
        saveAs: false
      }, (downloadId) => {
        if (chrome.runtime.lastError) {
          console.error('Download failed:', chrome.runtime.lastError);
          showNotification('❌ Download failed', 'error');
        } else {
          showNotification(`✅ ${filename} ready for Premiere!`, 'success');
          
          // Open downloads folder after 1 second
          setTimeout(() => {
            chrome.downloads.show(downloadId);
          }, 1000);
        }
      });
      
    } catch (error) {
      console.error('PRGrabber error:', error);
      showNotification('❌ Something went wrong', 'error');
    }
  }
});

function showNotification(message, type) {
  if (chrome.notifications) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icon48.png',
      title: 'PRGrabber',
      message: message
    });
  }
}