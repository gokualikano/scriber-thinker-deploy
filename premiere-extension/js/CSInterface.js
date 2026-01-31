/**
 * CSInterface - Simplified Adobe CEP Interface
 */

var CSInterface = function() {};

CSInterface.prototype.evalScript = function(script, callback) {
    try {
        window.__adobe_cep__.evalScript(script, callback);
    } catch (err) {
        if (callback) {
            callback('CSInterface not available');
        }
    }
};

CSInterface.prototype.getSystemPath = function(pathType) {
    var path = '';
    try {
        path = window.__adobe_cep__.getSystemPath(pathType);
    } catch (err) {
        // Fallback paths
        switch(pathType) {
            case 'userData':
                path = '~/Documents';
                break;
            case 'desktop':
                path = '~/Desktop';
                break;
            default:
                path = '';
        }
    }
    return path;
};

CSInterface.prototype.openURLInDefaultBrowser = function(url) {
    try {
        window.__adobe_cep__.openURLInDefaultBrowser(url);
    } catch (err) {
        window.open(url, '_blank');
    }
};

CSInterface.prototype.closeExtension = function() {
    try {
        window.__adobe_cep__.closeExtension();
    } catch (err) {
        window.close();
    }
};