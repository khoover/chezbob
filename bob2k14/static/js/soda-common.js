var rpc = new $.JsonRpcClient({ajaxUrl: '/api'});

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

function soda_login()
{
	 bootbox.prompt("Username?", function(result) {
		if (result === null) { //dismissed
		}
		else
		{
			var username = result;
			//check if it exists.
						rpc.call('Soda.getcrypt', [username], function (result) {
							if (result == "") 
							{
								//user has no password
								rpc.call('Soda.passwordlogin', [username, ""], function (result) {}, function (error){});
							}
							else
							{
								var cryptedPassword = result;
								bootbox.prompt("Password?", function(result) {
									resultcryptedPassword = unixCryptTD(result, cryptedPassword);
									rpc.call('Soda.passwordlogin', [username, resultcryptedPassword], function (result) {}, function (error){});
								});
								
							}
						},
						function (error)
						{
							bootbox.alert("User "+ username + " not found.");
						});
		}
	 });
}

function configureEventSource()
{
    var source = new EventSource('/stream');
	source.onmessage = function(e) {
		if (e.data.substring(0,3) == "sbc")
		{
			//this is a barcode that was purchased
			var barcode = e.data.substring(3);
			
			rpc.call('Soda.getbalance', [], function (result) {
							$("#user-balance").text(result)
						},
						function (error)
						{
							notify_error(error);
						});
						
			rpc.call('Bob.getbarcodeinfo', [barcode], function (result) {
			if(result['name'] === undefined)
			{
				bootbox.alert("Unrecognized barcode " + barcode + ".");
			}
			else
			{
				$("#transaction tbody").append("<tr><td>" +  result['name']  + "</td><td>" + result['price'] + "</td></tr>");
			}
			}, function(error){});
		}
		else
		{
			switch(e.data)
			{
				case "refresh":
					window.location.reload();
					break;
				case "slogout":
					$("#loggedin-sidebar").hide();
					$("#maindisplay").show();
					$("#transaction").hide();
					$("#login-sidebar").show();
					$("#userdisplay").hide();
				break;
				case "slogin":
					$("#transaction tbody").empty();
					$("#transaction").show();
					$("#maindisplay").hide();
					$("#loggedin-sidebar").show();
					$("#login-sidebar").hide();
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
}

function logout()
{
	rpc.call('Soda.logout', [], function (result) {
		},
		function (error)
		{
			notify_error(error);
		});
}

$(document).ready(function() {
	toggleFullScreen();
	
	$("#login").on('click', function()
	{
		soda_login();
	});
	
	$("#logout").on('click', function() {
		logout();
	});
	configureEventSource();
});