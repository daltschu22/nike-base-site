/* Map providers share one data, filtering, and details flow. */
(() => {
    const container = document.getElementById('map-container');
    if (!container) return;
    const element = id => document.getElementById(id);
    const center = { lat: 39.8283, lng: -98.5795 };
    let map = null;
    let provider = null;
    let markers = [];
    let sites = [];
    let loaded = false;
    let googleTimer;

    function coordinates(site) {
        if (site.latitude === null || site.longitude === null ||
            site.latitude === undefined || site.longitude === undefined ||
            typeof site.latitude === 'boolean' || typeof site.longitude === 'boolean' ||
            String(site.latitude).trim() === '' || String(site.longitude).trim() === '') return null;
        const lat = Number(site.latitude);
        const lng = Number(site.longitude);
        return Number.isFinite(lat) && Number.isFinite(lng) &&
            Math.abs(lat) <= 90 && Math.abs(lng) <= 180 ? { lat, lng } : null;
    }

    function showSiteInfo(site) {
        element('site-name').textContent = site.name || site.site_code || 'Nike site';
        const set = (id, value) => { element(id).querySelector('span').textContent = value; };
        const position = coordinates(site);
        set('site-code', site.site_code || 'Unknown');
        set('site-type', site.site_type || 'Unknown');
        set('site-location', `${site.state || 'Unknown'} (${position.lat.toFixed(4)}, ${position.lng.toFixed(4)})`);
        set('site-description', site.description || 'No description available');
        set('site-status', site.status || 'Unknown');
        const wiki = element('site-wiki');
        wiki.hidden = true;
        try {
            const url = new URL(site.wiki_url);
            if (url.protocol === 'https:' && url.hostname === 'en.wikipedia.org') {
                wiki.href = url.href;
                wiki.hidden = false;
            }
        } catch (_) { /* Leave invalid links hidden. */ }
        element('site-info').hidden = false;
    }

    function closeSiteInfo() { element('site-info').hidden = true; }

    function renderSites(recenter = false) {
        if (!map) return;
        closeSiteInfo();
        markers.forEach(marker => provider === 'google' ? marker.setMap(null) : map.removeLayer(marker));
        markers = [];
        const state = element('state-filter').value;
        const type = element('type-filter').value;
        const filtered = sites.filter(site => (!state || site.state === state) && (!type || site.site_type === type));
        const visible = filtered.filter(site => coordinates(site));
        visible.forEach(site => {
            const position = coordinates(site);
            let marker;
            if (provider === 'google') {
                marker = new google.maps.Marker({ position, map, title: site.name || site.site_code });
                marker.addListener('click', () => showSiteInfo(site));
            } else {
                marker = L.marker([position.lat, position.lng], {
                    title: site.name || site.site_code || '', alt: site.name || site.site_code || 'Nike site',
                }).addTo(map);
                marker.on('click', () => showSiteInfo(site));
            }
            markers.push(marker);
        });
        if (loaded) {
            let message = sites.length === 0 ? 'No site data is available yet.' :
                visible.length === 0 ? 'No mapped locations match these filters.' :
                `Showing ${visible.length} of ${sites.length} site locations.`;
            if (filtered.length > visible.length) message += ` ${filtered.length - visible.length} locations have no valid coordinates.`;
            element('data-status').textContent = message;
        }
        if (recenter && visible.length) {
            if (provider === 'google') {
                const bounds = new google.maps.LatLngBounds();
                visible.forEach(site => bounds.extend(coordinates(site)));
                map.fitBounds(bounds);
                // fitBounds adjusts zoom asynchronously, so cap it after the map settles.
                google.maps.event.addListenerOnce(map, 'idle', () => {
                    if (map.getZoom() > 10) map.setZoom(10);
                });
            } else {
                map.fitBounds(visible.map(site => {
                    const point = coordinates(site);
                    return [point.lat, point.lng];
                }), { padding: [24, 24], maxZoom: 10 });
            }
        }
    }

    async function loadSites() {
        element('loading').hidden = false;
        element('retry-load').hidden = true;
        element('data-status').textContent = 'Loading site data…';
        ['apply-filters', 'reset-filters', 'state-filter', 'type-filter'].forEach(id => { element(id).disabled = true; });
        try {
            const response = await fetch(container.dataset.sitesUrl, { signal: AbortSignal.timeout(15000) });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            if (!data.success || !Array.isArray(data.sites) || data.sites.some(site => !site || typeof site !== 'object')) {
                throw new Error('Invalid site response');
            }
            sites = data.sites;
            loaded = true;
            const selected = element('state-filter').value;
            element('state-filter').replaceChildren(new Option('All States', ''));
            [...new Set(sites.map(site => site.state).filter(Boolean))].sort().forEach(state => {
                element('state-filter').add(new Option(state, state));
            });
            element('state-filter').value = selected;
            if (map) renderSites();
            else element('data-status').textContent = `${sites.length} site locations loaded. Waiting for the map…`;
        } catch (error) {
            console.error('Error loading sites:', error);
            element('data-status').textContent = 'Could not load site data. Please retry.';
            element('retry-load').hidden = false;
        } finally {
            element('loading').hidden = true;
            ['apply-filters', 'reset-filters', 'state-filter', 'type-filter'].forEach(id => { element(id).disabled = false; });
        }
    }

    function initLeaflet(fallback = false) {
        clearTimeout(googleTimer);
        if (provider === 'leaflet') return;
        if (!window.L) {
            element('map-status').textContent = 'The map library could not load. Please reload the page.';
            return;
        }
        element('map').replaceChildren();
        provider = 'leaflet';
        markers = [];
        map = L.map('map').setView([center.lat, center.lng], 4);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        }).addTo(map);
        element('map-status').textContent = fallback ? 'Google Maps is unavailable. Using OpenStreetMap.' : '';
        renderSites();
    }

    // Define callbacks before inserting the asynchronous Google script.
    window.initGoogleMap = () => {
        if (provider === 'leaflet') return; // Ignore a callback arriving after the fallback.
        clearTimeout(googleTimer);
        try {
            map = new google.maps.Map(element('map'), { center, zoom: 4, mapTypeId: 'terrain' });
            provider = 'google';
            element('map-status').textContent = '';
            renderSites();
        } catch (error) {
            console.error('Google Maps failed:', error);
            initLeaflet(true);
        }
    };
    window.gm_authFailure = () => initLeaflet(true);
    element('apply-filters').addEventListener('click', () => renderSites(true));
    element('reset-filters').addEventListener('click', () => {
        element('state-filter').value = '';
        element('type-filter').value = '';
        renderSites();
        if (!map) return;
        if (provider === 'google') { map.setCenter(center); map.setZoom(4); }
        else map.setView([center.lat, center.lng], 4);
    });
    element('close-info').addEventListener('click', closeSiteInfo);
    element('retry-load').addEventListener('click', loadSites);
    document.addEventListener('keydown', event => { if (event.key === 'Escape') closeSiteInfo(); });
    if (container.dataset.googleKey) {
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?${new URLSearchParams({
            key: container.dataset.googleKey, callback: 'initGoogleMap', loading: 'async',
        })}`;
        script.async = true;
        script.onerror = () => initLeaflet(true);
        googleTimer = setTimeout(() => initLeaflet(true), 10000);
        document.head.appendChild(script);
    } else initLeaflet();
    loadSites();
})();
