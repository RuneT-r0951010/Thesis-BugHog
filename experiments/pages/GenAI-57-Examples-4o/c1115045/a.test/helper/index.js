var bypassDefaultSrc = function() {
  var img = document.createElement('img');
  img.src = 'https://xlab.tencent.com';
  document.body.appendChild(img);
  img.onload = function() {
    document.location.href = "https://a.test/report/?leak=c1115045-default-src";
  };
};

var bypassScriptSrc = function() {
  var script = document.createElement('script');
  script.src = 'http://d1iv3.me/test.js';
  document.body.appendChild(script);
  script.onload = function() {
    document.location.href = "https://a.test/report/?leak=c1115045-script-src";
  };
};

bypassDefaultSrc();
bypassScriptSrc();
