window.analytics = { track: function (eventName) { console.log("track", eventName); } };
window.analytics.track("pageview");
