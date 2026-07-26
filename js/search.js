// Iowa Directory Search — Lunr.js
// Dynamically loaded when search box is focused

(function() {
  let searchReady = false;
  let searchIndex = null;
  let store = {};

  function loadSearch() {
    if (searchReady) return;
    searchReady = true;

    // Load Lunr.js from CDN
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/lunr@2.3.9/lunr.min.js';
    script.onload = buildIndex;
    document.head.appendChild(script);
  }

  function buildIndex() {
    fetch('/data/search-index.json')
      .then(r => r.json())
      .then(data => {
        store = {};
        searchIndex = lunr(function() {
          this.ref('id');
          this.field('name', { boost: 10 });
          this.field('city', { boost: 5 });
          this.field('category');
          this.field('phone');
          this.field('description');

          data.forEach(doc => {
            store[doc.id] = doc;
            this.add(doc);
          });
        });
      })
      .catch(() => {});
  }

  window.searchDirectory = function(query) {
    if (!searchIndex) return [];
    try {
      return searchIndex.search(query).map(r => store[r.ref]).filter(Boolean);
    } catch(e) {
      return [];
    }
  };

  // Auto-load search on first interaction with search box
  document.addEventListener('DOMContentLoaded', () => {
    const searchBox = document.querySelector('input[type="search"]');
    if (searchBox) {
      searchBox.addEventListener('focus', loadSearch);
      searchBox.addEventListener('input', function() {
        const results = window.searchDirectory(this.value);
        // Display results — future enhancement
      });
    }
  });
})();
