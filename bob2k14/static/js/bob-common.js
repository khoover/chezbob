
var rpc = new $.JsonRpcClient({ajaxUrl: '/api'});
var menuIndex = 0;
var extraIndex = 0;
var extrafunctions = [];
var menufunctions = [soda_login, add_money, extra_items, buy_other, message, logout, transactions, my_chez_bob, transfer, barcode_id, nickname, password];

function soda_login()
{
	rpc.call('Bob.sodalogin', [], function (result) {
		},
		function (error)
		{
			bootbox.alert("There was a problem logging into the soda machine. It looks like someone is already logged in there, so try again after they have logged out.");
		});
}

function logout()
{
	rpc.call('Bob.logout', [], function (result) {
		},
		function (error)
		{
			notify_error(error);
		});
}
function add_money()
{
	 bootbox.dialog({
	  message: "Chez Bob encourages the use of the soda machine for all deposits, as it is both more accurate and makes collecting deposits easier.  Would you like to transfer your login to the soda machine to make a deposit there?  (In the future, you can do this directly with the 'Soda Login' menu item or by logging into the soda machine directly.)",
	  title: "Deposit at soda machine?",
	  buttons: {
		success: {
		  label: "Login to Soda Machine",
		  className: "btn-success",
		  callback: function() {
			soda_login();
		  }
		},
		danger: {
		  label: "Deposit anyway!",
		  className: "btn-danger",
		  callback: function() {
		    bootbox.prompt("How much money was deposited in the Bank of Bob?", function(result) {                
			  if (result === null) {                                             
				bootbox.alert("Deposit cancelled.");                             
			  } else {
				//do some error-checking here.
				//call rpc
			  }
			});
		  }
		}
	  }
	});
	 
}

function purchase_item(barcode)
{
	rpc.call('Bob.getbarcodeinfo', [barcode], function (result) {
			bootbox.confirm("Really purchase item " + result['name'] + " for " + result['price'] + "?", function (res) {
				if (res)
				{
					//do purchase here.
				}
			});
		},
		function (error)
		{
		});
}

function extra_items()
{
	rpc.call('Bob.getextras', [], function (result) {
			$("#extraitemmenu").empty();
			$("#extratitle").text("Purchase extra items");
			extrafunctions = [];
			extraIndex = 0;
			//re-populate the menu
			$.each(result, function(i,item){
				var extrafunction = function () {
					purchase_item(item['barcode']);};
				extrafunctions[i] = extrafunction;
				var menuitem = $("#extraitemmenu").append('<a href="#" class="list-group-item">' + item['name'] + '<span class="badge pull-right">' + item['price'] + '</span></a>');
				menuitem.on('click', extrafunction);
			});
			
			var closefunction = function()
			{
				$("#extra-actions").hide();
				$("#actions").show();
			};
			extrafunctions.push(closefunction);
			$("#extraitemmenu").append('<a href="#" class="list-group-item">Done</a>').on('click',closefunction);
			$($("#extraitemmenu").get(0)).addClass("active");
			$("#actions").hide();
			$("#extra-actions").show();
		},
		function (error)
		{
			notify_error(error);
		});
}

function buy_other()
{
     $("#actions").hide();
	 $("#buyother").show();
}

function message()
{
     $("#actions").hide();
	 $("#message").show();
}

function transactions()
{
	rpc.call('Bob.transactions', [], function (result) {
			$("#extraitemmenu").empty();
			$("#extratitle").text("Last 10 transactions");
			extrafunctions = [];
			extraIndex = 0;
			//re-populate the menu
			$.each(result, function(i,item){
				var extrafunction = function () {
					purchase_item(item['id']);};
				extrafunctions[i] = extrafunction;
				var menuitem = $("#extraitemmenu").append('<a href="#" class="list-group-item">' + item['xacttype'] + '<span class="badge pull-right">' + item['xactvalue'] + '</span></a>');
				menuitem.on('click', extrafunction);
			});
			
			var closefunction = function()
			{
				$("#extra-actions").hide();
				$("#actions").show();
			};
			extrafunctions.push(closefunction);
			$("#extraitemmenu").append('<a href="#" class="list-group-item">Done</a>').on('click',closefunction);
			$($("#extraitemmenu").get(0)).addClass("active");
			$("#actions").hide();
			$("#extra-actions").show();
		},
		function (error)
		{
			notify_error(error);
		});
}

function my_chez_bob()
{
     $("#actions").hide();
	 $("#mychezbob").show();
}

function transfer()
{
     $("#actions").hide();
	 $("#transfer").show();
}

function barcode_id()
{
     $("#actions").hide();
	 $("#barcodeid").show();
}

function nickname()
{
     $("#actions").hide();
	 $("#nickname").show();
}

function password()
{
     $("#actions").hide();
	 $("#passwordchange").show();
}

function notify_error(error)
{
	bootbox.alert("Error: " + error);
}

function handle_login()
{
	//capture username and password
	var username = $("#login-username").val();
	var password = $("#login-password").val();
	
	//silly crypt will require that we get the crypted password first for a salt.
	var salt = ""
	rpc.call('Bob.getcrypt', [username], function (result) {
		var cryptedPassword = unixCryptTD(password, result)
		rpc.call('Bob.passwordlogin', [username, cryptedPassword], function(result) {
			//login success. webevent should detect login can call handler.
		},
		function (error)
		{
			notify_error(error);
		});
	},
	function (error)
	{
		notify_error(error);
	}
	);
}

$(document).ready(function() {
	$("#btn-login").on("click", handle_login);
	
    var source = new EventSource('/stream');
	source.onmessage = function(e) {
		switch(e.data)
		{
			case "logout":
				$("#actions").hide();
				$("#login-username").val("");
				$("#login-password").val("");
				$("#loginbox").show();
			break;
			case "login":
				menuIndex = 0;
				$("#actions").show();
				rpc.call('Bob.getusername', [], function (result) {
						$("#loginname").text(result)
					},
					function (error)
					{
						notify_error(error);
					});
				rpc.call('Bob.getbalance', [], function (result) {
						$("#balance").text(result)
					},
					function (error)
					{
						notify_error(error);
					});
			    $("#mainmenu > a").removeClass("active");
				$($("#mainmenu > a").get(0)).addClass("active");
				$("#loginbox").hide();
			break;
		}
	}
	
	$('#mainmenu > a').each(function(i,j){
	 $(this).on('click', menufunctions[i]);
	});
	
	$("body").on("keydown", function(e)
	{	
		if ($("#mainmenu").is(':visible') && !$(".bootbox").is(':visible'))
		{
			if (e.keyCode === 13) {
				//enter
				menufunctions[menuIndex]();
			}
			
			if (e.keyCode === 38) {
				//up
				if (menuIndex != 0)
				{
					menuIndex--;
					$("#mainmenu > a").removeClass("active");
					$($("#mainmenu > a").get(menuIndex)).addClass("active");
				}
			}
			else if (e.keyCode === 40) {
				//down
				if (menuIndex < $("#mainmenu > a").length - 1)
				{
					menuIndex++;
					$("#mainmenu > a").removeClass("active");
					$($("#mainmenu > a").get(menuIndex)).addClass("active");
				}
			}
		}
		else if ($("#extraitemmenu").is(':visible') && !$(".bootbox").is(':visible'))
		{
			if (e.keyCode === 13) {
				//enter
				extrafunctions[extraIndex]();
			}
			
			if (e.keyCode === 38) {
				//up
				if (extraIndex != 0)
				{
					extraIndex--;
					$("#extraitemmenu > a").removeClass("active");
					$($("#extraitemmenu > a").get(extraIndex)).addClass("active");
				}
			}
			else if (e.keyCode === 40) {
				//down
				if (extraIndex < $("#extraitemmenu > a").length -1)
				{
					extraIndex++;
					$("#extraitemmenu > a").removeClass("active");
					$($("#extraitemmenu > a").get(extraIndex)).addClass("active");
				}
			}
		}
	});
});