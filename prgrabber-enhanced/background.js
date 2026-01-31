// PRGrabber - Direct Clipboard Paste

const PREMIERE_BRIDGE = 'http://localhost:8590';

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "prgrabber-clipboard",
    title: "🎬 Copy to Premiere (Cmd+V)",
    contexts: ["image"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "prgrabber-clipboard" && info.srcUrl) {
    
    fetch(`${PREMIERE_BRIDGE}/paste-image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ imageUrl: info.srcUrl })
    })
    .then(response => response.json())
    .then(result => {
      if (result.success) {
        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'icon48.png',
          title: 'PRGrabber',
          message: 'Ready! Press Cmd+V in Premiere'
        });
      }
    })
    .catch(() => {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon48.png',
        title: 'PRGrabber',
        message: 'Service offline'
      });
    });
  }
});