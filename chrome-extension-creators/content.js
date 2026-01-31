// Content script for YouTube pages
console.log('Paste to Creators: Content script loaded on', window.location.href);

// Inject CSS for visual feedback
const style = document.createElement('style');
style.textContent = `
  .creators-highlight {
    border: 2px solid #FFFF00 !important;
    box-shadow: 0 0 10px rgba(255, 255, 0, 0.5) !important;
    transition: all 0.3s ease !important;
  }
`;
document.head.appendChild(style);

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getCurrentVideoInfo') {
    const videoInfo = getCurrentVideoInfo();
    sendResponse(videoInfo);
  } else if (request.action === 'highlightVideo') {
    highlightCurrentVideo();
  }
});

// Get current video information
function getCurrentVideoInfo() {
  const url = window.location.href;
  const title = document.title;
  
  // Try to get video title from page
  const titleElement = document.querySelector('h1.title, #watch-header-title, .title, h1[class*="title"]');
  const videoTitle = titleElement ? titleElement.textContent.trim() : title;
  
  // Get video duration if available
  const durationElement = document.querySelector('.ytp-time-duration, .video-stream');
  const duration = durationElement ? durationElement.textContent : null;
  
  return {
    url: url,
    title: videoTitle,
    duration: duration,
    timestamp: Date.now()
  };
}

// Highlight current video with visual feedback
function highlightCurrentVideo() {
  // Find the main video player
  const videoPlayer = document.querySelector('#movie_player, .html5-video-player, video');
  
  if (videoPlayer) {
    videoPlayer.classList.add('creators-highlight');
    
    // Remove highlight after 2 seconds
    setTimeout(() => {
      videoPlayer.classList.remove('creators-highlight');
    }, 2000);
  }
}

// Add hover effect to YouTube video thumbnails for better UX
function addThumbnailEffects() {
  const thumbnails = document.querySelectorAll('a[href*="/watch?v="], a[href*="youtu.be/"]');
  
  thumbnails.forEach(thumbnail => {
    if (!thumbnail.hasAttribute('data-creators-enhanced')) {
      thumbnail.setAttribute('data-creators-enhanced', 'true');
      
      // Add tooltip on hover
      thumbnail.addEventListener('mouseenter', (e) => {
        const tooltip = document.createElement('div');
        tooltip.className = 'creators-tooltip';
        tooltip.textContent = 'Right-click → Paste to Creators';
        tooltip.style.cssText = `
          position: absolute;
          background: #FFFF00;
          color: #000;
          padding: 5px 10px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: bold;
          z-index: 9999;
          pointer-events: none;
          top: ${e.pageY - 30}px;
          left: ${e.pageX}px;
        `;
        document.body.appendChild(tooltip);
      });
      
      thumbnail.addEventListener('mouseleave', () => {
        const tooltip = document.querySelector('.creators-tooltip');
        if (tooltip) tooltip.remove();
      });
    }
  });
}

// Run on page load and when YouTube navigates (SPA)
function initialize() {
  addThumbnailEffects();
  
  // YouTube is a Single Page Application, so we need to watch for navigation
  const observer = new MutationObserver((mutations) => {
    let shouldUpdate = false;
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length > 0) {
        shouldUpdate = true;
      }
    });
    
    if (shouldUpdate) {
      setTimeout(addThumbnailEffects, 1000);
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

// Keyboard shortcut: Ctrl+Shift+C to send current video
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.shiftKey && e.key === 'C') {
    const videoInfo = getCurrentVideoInfo();
    if (videoInfo.url.includes('youtube.com/watch') || videoInfo.url.includes('youtu.be/')) {
      chrome.runtime.sendMessage({
        action: 'sendToDesktop',
        videoInfo: videoInfo
      });
      highlightCurrentVideo();
    }
  }
});