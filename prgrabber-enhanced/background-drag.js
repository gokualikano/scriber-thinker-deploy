// PRGrabber Enhanced - Drag & Drop Version (Works with cracked Premiere)

const PREMIERE_BRIDGE = 'http://localhost:8590';

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "prgrabber-drag",
    title: "🎬 Grab for Premiere (Drag)",
    contexts: ["image"]
  });
  
  console.log('PRGrabber Drag version loaded');
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "prgrabber-drag" && info.srcUrl) {
    handleDragGrab(info.srcUrl, tab);
  }
});

function handleDragGrab(imageUrl, tab) {
  console.log('Grabbing for drag:', imageUrl);
  
  // Send to drag helper service
  fetch(`${PREMIERE_BRIDGE}/paste-image`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ imageUrl: imageUrl })
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    } else {
      throw new Error('Drag service unavailable');
    }
  })
  .then(result => {
    console.log('Drag success:', result);
    showNotification('✅ Ready to drag to Premiere!', 'success');
    
    // Show drag instructions
    chrome.tabs.sendMessage(tab.id, {
      action: 'showDragInstructions',
      filename: result.filename
    }).catch(err => console.log('Tab message failed:', err));
  })
  .catch(error => {
    console.log('Drag service failed:', error);
    
    // Fallback to regular download
    const timestamp = new Date().toISOString().replace(/[-:]/g, '').slice(2, 14);
    const extension = getImageExtension(imageUrl);
    const filename = `pr_${timestamp}.${extension}`;
    
    chrome.downloads.download({
      url: imageUrl,
      filename: `PRGrabber/${filename}`,
      saveAs: false
    }, (downloadId) => {
      if (!chrome.runtime.lastError) {
        showNotification('📁 Downloaded - drag to Premiere!', 'success');
        setTimeout(() => chrome.downloads.show(downloadId), 500);
      }
    });
  });
}

function getImageExtension(url) {
  try {
    const urlObj = new URL(url);
    const match = urlObj.pathname.match(/\.([a-zA-Z0-9]+)$/);
    if (match) {
      const ext = match[1].toLowerCase();
      if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)) {
        return ext;
      }
    }
  } catch (e) {
    // Ignore
  }
  return 'jpg';
}

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