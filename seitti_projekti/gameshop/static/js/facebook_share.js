window.fbAsyncInit = function() {
    FB.init({
      appId      : '535406523314413',
      xfbml      : true,
      version    : 'v2.6'
    });
  };

(function(d, s, id) {
  var js, fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) return;
  js = d.createElement(s); js.id = id;
  js.src = "//connect.facebook.net/fi_FI/sdk.js#xfbml=1&version=v2.6&appId=535406523314413";
  fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));