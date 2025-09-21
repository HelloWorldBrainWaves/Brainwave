function initMapFromServer() {
    // this function will be run by the loaded Google Maps script callback
    // It creates the map and add markers for: current user, selected match, & recommended spot
    const darkModeStyle = [
        { elementType: 'geometry', stylers: [{ color: '#242f3e' }] },
        { elementType: 'labels.text.fill', stylers: [{ color: '#d59563' }] },
        { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#17263c' }] }
    ];

    const defaultCenter = CURRENT_USER ? { lat: CURRENT_USER.latitude || 40.4237, lng: CURRENT_USER.longitude || -86.9212 } : { lat:40.4237, lng:-86.9212 };
    const map = new google.maps.Map(document.getElementById("map"), {
        center: defaultCenter,
        zoom: 15,
        styles: darkModeStyle
    });

    // add marker function
    function addMarker(p, title, iconUrl) {
        const mk = new google.maps.Marker({
        position: p,
        map,
        title,
        icon: iconUrl ? { url: iconUrl, scaledSize: new google.maps.Size(40, 40) } : undefined
        });
        return mk;
    }

    // Add current user
    if (CURRENT_USER) {
        addMarker({lat: CURRENT_USER.latitude, lng: CURRENT_USER.longitude}, "You are here",
        "https://cdn-icons-png.flaticon.com/512/64/64113.png");
    }

    // Add selected match
    if (SELECTED_USER) {
        addMarker({lat: SELECTED_USER.latitude || (CURRENT_USER.latitude+0.001), lng: SELECTED_USER.longitude || (CURRENT_USER.longitude+0.001)}, SELECTED_USER.name,
        "http://maps.google.com/mapfiles/ms/icons/blue-dot.png");
    }

    // Recommended spot: try RECOMMENDED with lat/lng; if missing, look up in SPOTS
    let recPos = null;
    let recName = null;
    if (RECOMMENDED && RECOMMENDED.lat && RECOMMENDED.lng) {
        recPos = {lat: RECOMMENDED.lat, lng: RECOMMENDED.lng};
        recName = RECOMMENDED.spot;
    } else if (RECOMMENDED && RECOMMENDED.spot) {
        recName = RECOMMENDED.spot;
        const found = SPOTS.find(s => s.name === RECOMMENDED.spot);
        if (found) recPos = {lat: found.lat, lng: found.lng};
    }
    if (!recPos) {
        // fallback to first spot
        recPos = {lat: SPOTS[0].lat, lng: SPOTS[0].lng};
        recName = SPOTS[0].name;
    }
    const recMarker = addMarker(recPos, recName, "http://maps.google.com/mapfiles/ms/icons/green-dot.png");

    // Create info windows with distances
    function kmBetween(a, b) {
        function toRad(x){return x*Math.PI/180;}
        const R = 6371;
        const dLat = toRad(b.lat-a.lat), dLon = toRad(b.lng-a.lng);
        const aa = Math.sin(dLat/2)**2 + Math.cos(toRad(a.lat))*Math.cos(toRad(b.lat))*Math.sin(dLon/2)**2;
        const cc = 2*Math.atan2(Math.sqrt(aa), Math.sqrt(1-aa));
        return R*cc;
    }

    // Info for selected match
    if (SELECTED_USER && CURRENT_USER) {
        const d1 = kmBetween({lat:CURRENT_USER.latitude, lng:CURRENT_USER.longitude}, {lat:SELECTED_USER.latitude || CURRENT_USER.latitude+0.001, lng:SELECTED_USER.longitude || CURRENT_USER.longitude+0.001});
        const d2 = kmBetween({lat:CURRENT_USER.latitude, lng:CURRENT_USER.longitude}, recPos);
        const content = `<b>${SELECTED_USER.name}</b><br>Distance to you: ${d1.toFixed(2)} km<br>Distance from you to recommended spot: ${d2.toFixed(2)} km<br><a target="_blank" href="https://www.google.com/maps/dir/?api=1&origin=${CURRENT_USER.latitude},${CURRENT_USER.longitude}&destination=${recPos.lat},${recPos.lng}">Get Directions to Recommended Spot</a>`;
        const iw = new google.maps.InfoWindow({content});
        // attach on click to recMarker
        recMarker.addListener('click', ()=> iw.open(map));
    }

    document.getElementById("info").innerText = `Recommended: ${recName}`;
}

Load Google Maps with callback to initMapFromServer
async src="https://maps.googleapis.com/maps/api/js?key={{ google_api_key }}&callback=initMapFromServer">
src="{{ url_for('static', filename='js/main.js') }}"