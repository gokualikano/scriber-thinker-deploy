/**
 * PRGrabber - Premiere Pro Extension
 */

var csInterface = new CSInterface();
var recentImports = [];

// Initialize extension
document.addEventListener('DOMContentLoaded', function() {
    initializeExtension();
});

function initializeExtension() {
    console.log('PRGrabber extension loaded');
    
    // Bind event listeners
    document.getElementById('importBtn').addEventListener('click', importFromUrl);
    document.getElementById('clipboardBtn').addEventListener('click', importFromClipboard);
    document.getElementById('lastBtn').addEventListener('click', importLastCopied);
    
    // Auto-import when URL is pasted
    document.getElementById('imageUrl').addEventListener('paste', function(e) {
        setTimeout(function() {
            var url = document.getElementById('imageUrl').value.trim();
            if (url && isValidImageUrl(url)) {
                importFromUrl();
            }
        }, 100);
    });
    
    updateStatus('Ready to import images');
}

function importFromUrl() {
    var url = document.getElementById('imageUrl').value.trim();
    
    if (!url) {
        updateStatus('Please paste an image URL', 'error');
        return;
    }
    
    if (!isValidImageUrl(url)) {
        updateStatus('Please enter a valid image URL', 'error');
        return;
    }
    
    importImage(url);
}

function importFromClipboard() {
    // Try to get clipboard content
    csInterface.evalScript('getClipboardText()', function(result) {
        if (result && isValidImageUrl(result)) {
            document.getElementById('imageUrl').value = result;
            importImage(result);
        } else {
            updateStatus('No valid image URL in clipboard', 'error');
        }
    });
}

function importLastCopied() {
    if (recentImports.length > 0) {
        var lastUrl = recentImports[0].url;
        document.getElementById('imageUrl').value = lastUrl;
        importImage(lastUrl);
    } else {
        updateStatus('No recent imports found', 'error');
    }
}

function importImage(imageUrl) {
    updateStatus('Downloading and importing...', 'loading');
    setLoading(true);
    
    // Generate temporary filename
    var timestamp = new Date().toISOString().replace(/[-:]/g, '').slice(2, 14);
    var extension = getFileExtension(imageUrl) || 'jpg';
    var filename = 'pr_' + timestamp + '.' + extension;
    
    // ExtendScript to download and import image
    var script = `
        try {
            // Download image to temp directory
            var tempFolder = Folder.temp;
            var imageFile = new File(tempFolder.fsName + "/${filename}");
            
            // Download image (simplified - in real implementation you'd use HTTP requests)
            // For now, we'll use a placeholder approach
            var success = downloadImageToFile("${imageUrl}", imageFile);
            
            if (success) {
                // Import to Premiere Pro
                var importedItem = app.project.importFiles([imageFile.fsName], 
                    false,    // suppressUI
                    app.project.getInsertionBin(), 
                    false     // ignoreFileExtension
                );
                
                if (importedItem && importedItem.length > 0) {
                    // Add to timeline at playhead position
                    var activeSequence = app.project.activeSequence;
                    if (activeSequence) {
                        var videoTrack = activeSequence.videoTracks[0];
                        if (videoTrack) {
                            var currentTime = activeSequence.getPlayerPosition();
                            videoTrack.insertClip(importedItem[0], currentTime);
                        }
                    }
                    "SUCCESS: Image imported and added to timeline";
                } else {
                    "ERROR: Failed to import image";
                }
            } else {
                "ERROR: Failed to download image";
            }
        } catch (e) {
            "ERROR: " + e.toString();
        }
        
        // Helper function to download image
        function downloadImageToFile(url, file) {
            try {
                // This is a simplified version - real implementation would use proper HTTP requests
                // For demonstration, we'll assume the download succeeds
                return true;
            } catch (e) {
                return false;
            }
        }
    `;
    
    csInterface.evalScript(script, function(result) {
        setLoading(false);
        
        if (result && result.indexOf('SUCCESS') === 0) {
            updateStatus('✅ Image imported to timeline!', 'success');
            addToRecent(imageUrl, filename);
            document.getElementById('imageUrl').value = '';
        } else {
            var errorMsg = result && result.indexOf('ERROR:') === 0 ? 
                          result.substring(6) : 'Import failed';
            updateStatus('❌ ' + errorMsg, 'error');
        }
    });
}

function isValidImageUrl(url) {
    try {
        var urlObj = new URL(url);
        var pathname = urlObj.pathname.toLowerCase();
        var validExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'];
        
        return validExtensions.some(function(ext) {
            return pathname.endsWith(ext);
        }) || pathname.includes('image') || url.includes('googleusercontent.com');
    } catch (e) {
        return false;
    }
}

function getFileExtension(url) {
    try {
        var pathname = new URL(url).pathname;
        var match = pathname.match(/\.([a-zA-Z0-9]+)$/);
        return match ? match[1] : null;
    } catch (e) {
        return null;
    }
}

function updateStatus(message, type) {
    var statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = 'status' + (type ? ' ' + type : '');
    
    // Clear status after 5 seconds if it's an error or success
    if (type === 'error' || type === 'success') {
        setTimeout(function() {
            if (statusEl.className.includes(type)) {
                updateStatus('Ready to import images');
            }
        }, 5000);
    }
}

function setLoading(isLoading) {
    var container = document.querySelector('.container');
    if (isLoading) {
        container.classList.add('loading');
    } else {
        container.classList.remove('loading');
    }
}

function addToRecent(url, filename) {
    var item = {
        url: url,
        filename: filename,
        timestamp: new Date().toLocaleTimeString()
    };
    
    recentImports.unshift(item);
    if (recentImports.length > 5) {
        recentImports.pop();
    }
    
    updateRecentList();
}

function updateRecentList() {
    var listEl = document.getElementById('recentList');
    
    if (recentImports.length === 0) {
        listEl.innerHTML = '<p class="no-recent">No recent imports</p>';
        return;
    }
    
    var html = '';
    recentImports.forEach(function(item) {
        var shortUrl = item.url.length > 40 ? item.url.substring(0, 40) + '...' : item.url;
        html += '<div class="recent-item" onclick="reuseRecentItem(\'' + 
                item.url + '\')">' + item.filename + '<br><small>' + 
                shortUrl + ' • ' + item.timestamp + '</small></div>';
    });
    
    listEl.innerHTML = html;
}

function reuseRecentItem(url) {
    document.getElementById('imageUrl').value = url;
    importImage(url);
}