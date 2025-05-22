onmessage = function(event) {
  importScripts('https://a.test/report/?leak=f949706-import');
  postMessage('Worker executed');
};