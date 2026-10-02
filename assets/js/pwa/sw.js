---
permalink: /sw.js
---
// Upgrade visitors still controlled by Chirpy 5's /sw.js registration.
importScripts('{{ "/sw.min.js" | relative_url }}');
self.addEventListener('install', () => self.skipWaiting());
