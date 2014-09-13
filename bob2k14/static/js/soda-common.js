var rpc = new $.JsonRpcClient({ajaxUrl: '/api'});
var autotime = "20";
var increment_time = 30;


// We maintain modal dialogs in a stack
var modal_stack= []

function showModal(id, selector, onShowF, onHideF) {
  if (onShowF != null) {
    $(selector).modal("show").on("shown.bs.modal", function(e) {onShowF()});
  } else {
    $(selector).modal("show");
  }

  modal_stack.push({'id': id, 'cleanup': function () {
    if (onHideF != null) {
      $(selector).modal("hide").on("hidden.bs.modal", function(e) {onHideF()});
    } else {
      $(selector).modal("hide");
    }
  }});
}

function popModal(id) {
  shown = false;
  for (var i in modal_stack)
    if (modal_stack[i].id == id) {
      shown = true;
      break;
    }

  if (!shown)
    return

  while (modal_stack.length > 0) {
    t = modal_stack.pop()

    t.cleanup()    

    if (t.id == id)
      break;
  }
}

function popAllModals() {
  while (modal_stack.length > 0) {
    t = modal_stack.pop()
    t.cleanup()    
  }
}

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

function notify_error(err)
{
  /*
  if (typeof(err) == 'object') {
    alert(err.message + ' ' + err.stack)
  }
  else
    alert(err);
  */
}

function ignore(result) {}

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

function decimalToHex(d, padding) {
    var hex = Number(d).toString(16);
    padding = typeof (padding) === "undefined" || padding === null ? padding = 2 : padding;

    while (hex.length < padding) {
        hex = "0" + hex;
    }

    return hex;
}

function refreshsodastates()
{
	//should only be updated when a vend occurs...

	rpc.call('Soda.getinventory', [], function(result) {
    window.sodaStatus = result;
    for (var slot in result) {
      var count = result[slot]
			var backgroundcolor = "rgb(255,230,80)"
      if (count == "unknown") // unknown
		    backgroundcolor = "rgb(255,230,80)";
      else if (count > 0)
				backgroundcolor = "rgb(18,255,9)";
      else // count <=0
					backgroundcolor = "rgb(255,41,0)";
      $("#count" + slot).text(count);
			$("#soda" + slot).css("background-color", backgroundcolor);
		}
  }, notify_error);
}

window.source = null;

function configureEventSource()
{
    window.source = new EventSource('/stream');
    window.source.onerror = function(e){
        //display nice error message
        //This is one of the few modals we don't want cleaned up on logout, so
        //we leave it outside the modal stack.
        $("#disconnected").modal('show').on('shown.bs.modal', function(e) {
            setTimeout(function() {
                $("#disconnected").modal('hide').on('hidden.bs.modal', function(e) {configureEventSource();});
            }
            , 15000);});
    }
	window.source.onmessage = function(e) {
		if (e.data.substring(0,3) == "sbc")
		{
			//this is a barcode that was purchased
			resetTimer();
			var barcode = e.data.substring(3);
      popModal("dispensingdialog");

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
      showModal("dispensingdialog", "#dispensingdialog", null, null)
		}
        else if (e.data.substring(0,3) == "vdd")
		{
			//soda vend deny
			resetTimer();
      showModal("denydialog", "#denydialog", function() {
        setTimeout(function(){
                      popModal("denydialog");
                      popModal("dispensingdialog");
                   }, 3000)
      }, null)
		}
         else if (e.data.substring(0,3) == "vdf")
		{
			//soda vend fail
			resetTimer();
      showModal("faildialog", "#faildialog", function() {
        setTimeout(function(){
                    popModal("faildialog");
                    popModal("dispensingdialog");
                   }, 3000)
      }, null)
		}
        else if (e.data.substring(0,3) == "vds")
		{
			//soda vend success
			resetTimer();
			rpc.call('Bob.getbarcodeinfo', [e.data.substring(3)], function (result) {
			$("#transaction tbody").append("<tr><td>" +  result['name']  + "</td><td>" + result['price'] + "</td></tr>");
            popModal("dispensingdialog")
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
					$("#more-time-sidebar").hide();
					$("#restock-sidebar").hide();
					$("#maindisplay").show();
					$("#transaction").hide();
					$("#login-sidebar").show();
					$("#userdisplay").hide();
          popAllModals();
					clearTimer();
				break;
				case "slogin":
					$("#transaction tbody").empty();
					$("#transaction").show();
					$("#maindisplay").hide();
					$("#loggedin-sidebar").show();
					$("#more-time-sidebar").show();
					$("#login-sidebar").hide();
					$("#userdisplay").show();

          roles = rpc.call('Soda.getroles', [], function (result) {
              for (var i in result.roles) {
                if (result.roles[i] == "restocker") {
					        $("#restock-sidebar").show();
                }
              }
						},
						function (error)
						{
              alert("ERRROR:" + error.message + "\n" + error.stack);
							notify_error(error);
						});
          

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
	refreshsodastates();
}

function add_more_time()
{
  var time = parseInt($("#logouttime").text());

  if (time != 0) {
    time += increment_time;

    // For now we limit time increases up to 5 minutes
    if (time > 300)
      time = 300;
    $("#logouttime").text(time)
  }

  refreshsodastates();
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

	$("#more-time").on('click', function() {
		add_more_time();
	});

	$("#restock").on('click', function() {
    showModal("restockingdialog", "#restockingdialog", null, null)
	});

	$("#restockingdialog-done").on('click', function() {
    popModal("restockingdialog")
	});

  function addBoxCallback(buttonId) {
    $("#re-soda" + buttonId).on('click', function () {
      bootbox.dialog({
        title: "Restock", // This could be more specific...
        message: "<img src='img/logos/" + buttonId + ".jpg' /> " +
                " <input type='number' id='re-new-" + buttonId + "' value='" + 
                window.sodaStatus[buttonId] + "'></input>",
        buttons: {
          cancel: {
            label: "Cancel",
            className: "btn-primary",
            callback: function () {}
          },
          update: {
            label: "Update",
            className: "btn-primary",
            callback: function () {
              rpc.call("Soda.updateinventory",
                [buttonId, $("#re-new-" + buttonId).val()], ignore,
                notify_error);
              refreshsodastates();
            }
          }
        }
      });
    });
  }

  addBoxCallback("01")
  addBoxCallback("02")
 // addBoxCallback("03")
  addBoxCallback("04")
  addBoxCallback("05")
  addBoxCallback("06")
  addBoxCallback("07")
  addBoxCallback("08")
  addBoxCallback("09")
  addBoxCallback("0A")

	configureEventSource();
	/*
	window.addEventListener('touchstart', function(e){
		resetTimer();
	}, false)*/

	refreshsodastates();
	setInterval(logout_timer, 1000);
});
