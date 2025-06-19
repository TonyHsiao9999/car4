
function loadGoogleMapsAPI(apiKey) {
    var script = document.createElement('script');
    script.src = 'https://maps.googleapis.com/maps/api/js?key=' + apiKey + '&libraries=places';
    document.head.appendChild(script);
}

var apiKey;
var hostname = window.location.hostname;

if (hostname === 'pre-release-pax.ltc.hantek-iot.com') {
    apiKey = 'AIzaSyCTt9tgOe-7ZQ_FrNYwGUTzOcEdg8LPvSg';
} else if (hostname === 'www.ntpc.ltc-car.org'){
    apiKey = 'AIzaSyCP0XZ5q6wZMzOhAxOHtJ2IjKNfUPWKCRY';
} else {
    apiKey = 'AIzaSyAoCZ5NAKyxIYBiqZRq6gVCcfgy8xjvRLA';
}

loadGoogleMapsAPI(apiKey);
