function statusChangeCallback(response) {
  if (response.status === 'connected') {
    fetchUserInfo();
  }
}

function checkLoginState() {
  FB.getLoginStatus(function(response) {
    statusChangeCallback(response);
  });
}

window.fbAsyncInit = function() {
FB.init({
  appId      : '1680373072180095',
  cookie     : true,
  xfbml      : true,
  version    : 'v2.5'
});

};

(function(d, s, id) {
  var js, fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) return;
  js = d.createElement(s); js.id = id;
  js.src = "//connect.facebook.net/en_US/sdk.js";
  fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));

function fetchUserInfo() {
  console.log('Welcome!  Fetching your information.... ');
  FB.api('/me?fields=first_name,last_name,email,id', function(response) {
    console.log(response);
    var csrftoken = $('input[name="csrfmiddlewaretoken"]').attr("value");
    $.ajax({
      type: 'POST',
      url: "/facebook_login",
      data: { firstName: response.first_name,
              lastName: response.last_name,
              id: response.id,
              email: response.email,
              csrfmiddlewaretoken: csrftoken },
      dataType: "json",
      success: function(data) {
        if (data.status == 1) {
          $('body').html(data.html);
        }
        else {
          window.location.href = data.url;
        }
      }
    });
  });
}
