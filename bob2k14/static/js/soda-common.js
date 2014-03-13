function toggleFullScreen() {
  if (!document.fullscreenElement &&    // alternative standard method
      !document.mozFullScreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement ) {  // current working methods
    if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen();
    } else if (document.documentElement.msRequestFullscreen) {
      document.documentElement.msRequestFullscreen();
    } else if (document.documentElement.mozRequestFullScreen) {
      document.documentElement.mozRequestFullScreen();
    } else if (document.documentElement.webkitRequestFullscreen) {
      document.documentElement.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    } else if (document.mozCancelFullScreen) {
      document.mozCancelFullScreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    }
  }
}

function notify_error()
{
}

function configureEventSource()
{
    var source = new EventSource('/stream');
	source.onmessage = function(e) {
		switch(e.data)
		{
			case "refresh":
				window.location.reload();
				break;
			case "slogout":
				$("#userdisplay").hide();
			break;
			case "slogin":
				menuIndex = 0;
				$("#userdisplay").show();
				rpc.call('Soda.getusername', [], function (result) {
						$("#user-nick").text(result)
					},
					function (error)
					{
						notify_error(error);
					});
						rpc.call('Soda.getbalance', [], function (result) {
						$("#user-balance").text(result)
					},
					function (error)
					{
						notify_error(error);
					});
			break;
		}
	}
}
$(document).ready(function() {
	toggleFullScreen();
	configureEventSource();
});