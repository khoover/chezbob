
var rpc = new $.JsonRpcClient({ajaxUrl: '/api'});
var menuIndex = 0;
var extraIndex = 0;
var extrafunctions = [];
var menufunctions = [soda_login, add_money, extra_items, buy_other, message, logout, transactions, my_chez_bob, transfer, barcode_id, nickname, password];

var shortcutmap = {
	"83": 0, //s
	"65": 1, //a
	"69": 2, //e
	"66": 3, //b
	"77": 4, //m
	"76": 5, //l
	"84": 6, //t
	"89": 7, //y
	"82": 8, //r
	"67": 9, //c
	"73": 10, //i
	"80": 11 //p
};
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
						//make sure the result is a money type
		//do purchase here.
					rpc.call('Bob.deposit', [result], function (result) {
							//grab new balance
							rpc.call('Bob.getbalance', [], function (result) {
									$("#balance").text(result)
								},
								function (error)
								{
									notify_error(error);
								});
							bootbox.alert("Deposit successful.");
						},
						function (error)
						{
							bootbox.alert("An error occured while making the deposit");
						});
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
			if(result['name'] === undefined)
			{
				bootbox.alert("Unrecognized barcode " + barcode + ".");
			}
			else
			{
			bootbox.confirm("Really purchase item " + result['name'] + " for " + result['price'] + "?", function (res) {
				if (res)
				{
					//do purchase here.
					rpc.call('Bob.purchasebarcode', [barcode], function (result) {
							//grab new balance
							rpc.call('Bob.getbalance', [], function (result) {
									$("#balance").text(result)
								},
								function (error)
								{
									notify_error(error);
								});
							bootbox.alert("Purchase successful.");
						},
						function (error)
						{
							bootbox.alert("An error occured while making the purchase.");
						});
				}
			});
			}
		},
		function (error)
		{
			bootbox.alert("Unrecognized barcode " + barcode + ".");
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
				$("#extraitemmenu").append('<a href="#" class="list-group-item">' + item['name'] + '<span class="badge pull-right">' + item['price'] + '</span></a>');
				$($("#extraitemmenu > a").get(i)).on('click', extrafunction);
			});
			
			var closefunction = function()
			{
				$("#extra-actions").hide();
				$("#actions").show();
			};
			extrafunctions.push(closefunction);
			$("#extraitemmenu").append('<a href="#" class="list-group-item">Done</a>')
            $($("#extraitemmenu > a").get($("#extraitemmenu > a").length - 1)).on('click',closefunction);
			$($("#extraitemmenu > a").get(0)).addClass("active");
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
     bootbox.prompt("What is the purchase price of the item?", function (result)
{
	if (result === null) {}
	else
	{
		//make sure the result is a money type
		//do purchase here.
					rpc.call('Bob.purchaseother', [result], function (result) {
							//grab new balance
							rpc.call('Bob.getbalance', [], function (result) {
									$("#balance").text(result)
								},
								function (error)
								{
									notify_error(error);
								});
							bootbox.alert("Purchase successful.");
						},
						function (error)
						{
							bootbox.alert("An error occured while making the purchase.");
						});
	}
}
);
}

function message()
{
     bootbox.alert("This function will be restored soon!");
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
					};
				extrafunctions[i] = extrafunction;
				$("#extraitemmenu").append('<a href="#" class="list-group-item">' + item['xacttype'] + '<span class="badge pull-right">' + item['xactvalue'] + '</span></a>');
			});
			
			var closefunction = function()
			{
				$("#extra-actions").hide();
				$("#actions").show();
			};
			extrafunctions.push(closefunction);
			$("#extraitemmenu").append('<a href="#" class="list-group-item">Done</a>');
            $($("#extraitemmenu > a").get($("#extraitemmenu > a").length - 1)).on('click',closefunction);
			$($("#extraitemmenu > a").get(0)).addClass("active");
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
     bootbox.alert("This function will be restored soon!");
}

function transfer()
{
     bootbox.alert("This function will be restored soon!");
}

function barcode_id()
{
     bootbox.alert("This function will be restored soon!");
}

function nickname()
{
     bootbox.alert("This function will be restored soon!");
}

function password()
{
     bootbox.alert("This function will be restored soon!");
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
	
	//was the username all numbers
	if (!isNaN(username))
	{
	rpc.call('Bob.barcodelogin', [username], function(result) {
			//login success. webevent should detect login can call handler.
		},
		function (error)
		{
			bootbox.alert("Authentication error.");
		});
	}
	else
	{
		//silly crypt will require that we get the crypted password first for a salt.
		var salt = ""
		rpc.call('Bob.getcrypt', [username], function (result) {
			var cryptedPassword;
			if (password == "") { cryptedPassword = ""; } //for users without passwords.
			else {cryptedPassword = unixCryptTD(password, result);}
			
			rpc.call('Bob.passwordlogin', [username, cryptedPassword], function(result) {
				//login success. webevent should detect login can call handler.
			},
			function (error)
			{
				bootbox.alert("Authentication error.");
			});
		},
		function (error)
		{
			bootbox.alert("Authentication error.");
		}
		);
	}
}

var bcodeinput = false;
var bcodebuffer = "";

$(document).ready(function() {
	$("#btn-login").on("click", handle_login);
	$("#login-username").focus();
    var source = new EventSource('/stream');
	source.onmessage = function(e) {
		switch(e.data)
		{
			case "refresh":
				window.location.reload();
				break;
			case "logout":
				$("#actions").hide();
				$("#login-username").val("");
				$("#login-password").val("");
				$("#loginbox").show();
				$("#login-username").focus();
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
		if ($("#loginbox").is(':visible') && !$(".bootbox").is(':visible'))
		{
			if (e.keyCode === 13) {
					//enter
					handle_login();
			}
		}
		
		if ($("#mainmenu").is(':visible') && !$(".bootbox").is(':visible'))
		{
			if (shortcutmap[parseInt(e.keyCode)] !== undefined)
			{
				//move to this key
				menuIndex = shortcutmap[parseInt(e.keyCode)]
				$("#mainmenu > a").removeClass("active");
				$($("#mainmenu > a").get(menuIndex)).addClass("active");
			}
			
			if (e.keyCode === 81) {
				//logout
				logout();
			}
			
			if (e.keyCode === 13) {
				if (bcodeinput)
				{
					purchase_item(bcodebuffer);
					bcodeinput = false;
				}
				else
				{
					//enter
					menufunctions[menuIndex]();
				}
			}
			
			if (e.keyCode >= 48 && e.keyCode <= 57)
			{
				//number
				if (!bcodeinput) {bcodeinput = true; bcodebuffer = "";}
				bcodebuffer += parseInt(e.keyCode - 48); //keycode to number conversion
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