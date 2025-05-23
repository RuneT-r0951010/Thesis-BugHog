console.log('Sensitive operation executed');
var img = new Image();
img.src = 'https://a.test/report/?leak=c1074317&success';
document.body.appendChild(img);
