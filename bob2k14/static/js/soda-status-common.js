var rpc = new $.JsonRpcClient({ajaxUrl: '/api'});
var autotime = "20";
var increment_time = 30;
window.paused = false;


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
	if (time > 0 && !window.paused)
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
      refreshsodastates();
		}
        else if (e.data.substring(0,3) == "vdr")
		{
		}
        else if (e.data.substring(0,3) == "vdd")
		{
			//soda vend deny
      refreshsodastates();
		}
         else if (e.data.substring(0,3) == "vdf")
		{
			//soda vend fail
      refreshsodastates();
		}
        else if (e.data.substring(0,3) == "vds")
		{
			//soda vend success
      refreshsodastates();
		}
		else if (e.data.substring(0,3) == "deb")
		{
			//bill deposit.
		}
		else if (e.data.substring(0,3) == "dec")
		{
			//coin deposit.
		}
		else
		{
			switch(e.data)
			{
				case "refresh":
					window.location.reload();
					break;
				case "slogout":
				break;
				case "slogin":
				break;
			}
		}
	}
}


$(document).ready(function() {
	toggleFullScreen();

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

	refreshsodastates();
	setInterval(logout_timer, 1000);
});
