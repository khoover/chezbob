var rpc = new $.JsonRpcClient({ajaxUrl: '/api'});
var autotime = "20";

function resetTimer(){
	$("#logouttime").text(autotime);
	$("body").css('background-color', '#fff');
}

function clearTimer(){
	$("#logouttime").text(0);
	$("body").css('background-color', '#fff');
}

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

function logout_timer()
{
	var time = parseInt($("#logouttime").text());
	if (time > 0)
	{
		time = time -1;
		$("#logouttime").text(time);
		
		if (time == 0)
		{
				$("body").css('background-color', '#fff');
				rpc.call('Soda.logout', [], function (result) {
				},
				function (error)
				{
					notify_error(error);
				});
		}
		else if (time < 5)
		{
			$("body").css('background-color', '#ffaaaa');
		}
	}
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
						rpc.call('Bob.getcrypt', [username], function (result) {
							if (result === null) 
							{
								//user has no password
								rpc.call('Soda.passwordlogin', [username, ""], function (result) {}, function (error){});
							}
							else
							{
								var cryptedPassword = result;
								bootbox.dialog({
								  message: "Password: <input type='Password' name='password' id='password'></input>",
								  title: "Password",
								  buttons: {
									main: {
									  label: "Login",
									  className: "btn-primary",
									  callback: function() {
									resultcryptedPassword = unixCryptTD($("#password").val(), cryptedPassword);
									rpc.call('Soda.passwordlogin', [username, resultcryptedPassword], function (result){}, function (error){});}
									  }
									}
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
			resetTimer();
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
        else if (e.data.substring(0,3) == "vdr")
		{
			//soda vend request
			resetTimer();
			rpc.call('Bob.getbarcodeinfo', [e.data.substring(3)], function (result) {
			$("#sodaname").text(result['name']);}, function (error) {});
            $("#dispensingdialog").modal('show');
		}
        else if (e.data.substring(0,3) == "vdd")
		{
			//soda vend deny
			resetTimer();
			$("#denydialog").modal('show');
            setTimeout(function(){$('.modal').modal('hide');}, 3000);
		}
         else if (e.data.substring(0,3) == "vdf")
		{
			//soda vend fail
			resetTimer();
			$("#faildialog").modal('show');
            setTimeout(function(){$('.modal').modal('hide');}, 3000);
		}
        else if (e.data.substring(0,3) == "vds")
		{
			//soda vend success
			resetTimer();
			rpc.call('Bob.getbarcodeinfo', [e.data.substring(3)], function (result) {
			$("#transaction tbody").append("<tr><td>" +  result['name']  + "</td><td>" + result['price'] + "</td></tr>");
            $('.modal').modal('hide');
            }, function (error){});
		}
		else if (e.data.substring(0,3) == "deb")
		{
			//bill deposit.
			resetTimer();
			rpc.call('Soda.getbalance', [], function (result) {
							$("#user-balance").text(result)
						},
						function (error)
						{
							notify_error(error);
						});
			
			$("#transaction tbody").append("<tr><td>Deposit <i class='fa fa-usd'></i>" +  e.data.substring(3)  + "</td><td>+" + e.data.substring(3) + "</td></tr>");
		}
		else if (e.data.substring(0,3) == "dec")
		{
			//coin deposit.
			resetTimer();
			rpc.call('Soda.getbalance', [], function (result) {
							$("#user-balance").text(result)
						},
						function (error)
						{
							notify_error(error);
						});
			
			$("#transaction tbody").append("<tr><td>Deposit coins <i class='fa fa-usd'></i>" +  e.data.substring(3)  + "</td><td>+" + e.data.substring(3) + "</td></tr>");
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
					clearTimer();
				break;
				case "slogin":
					$("#transaction tbody").empty();
					$("#transaction").show();
					$("#maindisplay").hide();
					$("#loggedin-sidebar").show();
					$("#login-sidebar").hide();
					$("#userdisplay").show();
					
					resetTimer();
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
	clearTimer();
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
	/*
	window.addEventListener('touchstart', function(e){
		resetTimer();
	}, false)*/

 
	setInterval(logout_timer, 1000);
});