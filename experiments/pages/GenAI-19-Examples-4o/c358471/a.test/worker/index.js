importScripts('https://b.test/cross-origin.js');

self.onmessage = function(event) {
  if (event.data === 'check') {
    fetch('https://b.test/', {mode: 'no-cors'}).then(response => {
      postMessage('success');
    }).catch(error => {
      postMessage('error');
    });
  }
};