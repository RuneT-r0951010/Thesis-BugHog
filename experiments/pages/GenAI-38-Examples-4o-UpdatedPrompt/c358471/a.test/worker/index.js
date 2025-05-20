importScripts('https://b.test/script.js');
var xhttp = new XMLHttpRequest();
xhttp.open("GET", "https://b.test/api", true);
xhttp.send();
xhttp.onload = function() {
  console.log('XHR completed');
};