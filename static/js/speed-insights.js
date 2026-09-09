/**
 * Vercel Speed Insights Integration for CineFlow
 * This file loads and initializes Vercel Speed Insights to track web performance metrics
 */

(function() {
    'use strict';
    
    // Check if we're in development mode (localhost or 127.0.0.1)
    const isDevelopment = window.location.hostname === 'localhost' || 
                         window.location.hostname === '127.0.0.1';
    
    // Speed Insights doesn't track in development by default, but we'll initialize anyway
    // for when the app is deployed to production
    
    // Initialize the Speed Insights queue
    if (!window.si) {
        window.si = function() {
            (window.siq = window.siq || []).push(arguments);
        };
    }
    
    // Create and inject the Speed Insights script
    const script = document.createElement('script');
    
    // Use the debug script in development, production script otherwise
    if (isDevelopment) {
        script.src = 'https://va.vercel-scripts.com/v1/speed-insights/script.debug.js';
    } else {
        script.src = '/_vercel/speed-insights/script.js';
    }
    
    script.defer = true;
    script.setAttribute('data-sdkn', '@vercel/speed-insights');
    script.setAttribute('data-sdkv', '2.0.0');
    
    // Add error handling
    script.onerror = function() {
        console.warn('Failed to load Vercel Speed Insights script');
    };
    
    // Inject the script into the document
    if (document.head) {
        document.head.appendChild(script);
    } else {
        // Fallback if head is not yet available
        document.addEventListener('DOMContentLoaded', function() {
            document.head.appendChild(script);
        });
    }
})();
