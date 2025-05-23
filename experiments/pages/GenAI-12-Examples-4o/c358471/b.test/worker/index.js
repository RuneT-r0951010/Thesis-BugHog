onmessage = function() {
  try {
    fetch('https://b.test/force-cross-origin-fetch')
      .then(response => {
        if (response.ok) {
          postMessage('cross-origin-request-successful');
        }
      });
  } catch {
    // Handle error
  }
};