// Popup script for Paste to Creators extension
const desktopAppPort = 7898;

document.addEventListener('DOMContentLoaded', () => {
  const statusElement = document.getElementById('status');
  const testButton = document.getElementById('testConnection');
  const sendButton = document.getElementById('sendCurrentVideo');

  // Test connection on popup open
  testConnection();

  // Set up event listeners
  testButton.addEventListener('click', testConnection);
  sendButton.addEventListener('click', sendCurrentVideo);

  // Test connection to desktop app
  async function testConnection() {
    statusElement.textContent = '🔄 Testing connection...';
    statusElement.className = 'status disconnected';
    testButton.disabled = true;

    try {
      const response = await fetch(`http://localhost:${desktopAppPort}/ping`, {
        method: 'GET',
        mode: 'cors'
      });

      if (response.ok) {
        statusElement.textContent = '🟢 Connected to desktop app';
        statusElement.className = 'status connected';
        sendButton.disabled = false;
      } else {
        throw new Error('App not responding');
      }
    } catch (error) {
      statusElement.textContent = '🔴 Desktop app not running';
      statusElement.className = 'status disconnected';
      sendButton.disabled = true;
    } finally {
      testButton.disabled = false;
    }
  }

  // Send current video to desktop app
  async function sendCurrentVideo() {
    try {
      // Get current active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab || !isYouTubeUrl(tab.url)) {
        showMessage('⚠️ Please navigate to a YouTube video first');
        return;
      }

      // Send the URL
      const success = await sendUrlToDesktop(tab.url);
      if (success) {
        showMessage('✅ Video sent successfully!');
        window.close();
      } else {
        showMessage('❌ Failed to send video');
      }
    } catch (error) {
      console.error('Error sending current video:', error);
      showMessage('❌ Error occurred');
    }
  }

  // Send URL to desktop application
  async function sendUrlToDesktop(url) {
    try {
      const response = await fetch(`http://localhost:${desktopAppPort}/paste-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          timestamp: Date.now(),
          source: 'chrome-extension-popup'
        })
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to send URL:', error);
      return false;
    }
  }

  // Check if URL is a YouTube video
  function isYouTubeUrl(url) {
    return url && (
      url.includes('youtube.com/watch') || 
      url.includes('youtu.be/') ||
      url.includes('m.youtube.com/watch')
    );
  }

  // Show temporary message
  function showMessage(message) {
    const originalText = statusElement.textContent;
    const originalClass = statusElement.className;
    
    statusElement.textContent = message;
    statusElement.className = 'status connected';
    
    setTimeout(() => {
      statusElement.textContent = originalText;
      statusElement.className = originalClass;
    }, 2000);
  }
});