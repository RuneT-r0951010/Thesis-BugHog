// Simulating require.js as it would be fetched from a resource URL
(function(global) {
    // Minimal require.js necessary code to trigger the test case
    global.require = function() {};
})(this);