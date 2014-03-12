
var rpc = new $.JsonRpcClient({ajaxUrl: '/api'});

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
		bootbox.alert(e.data);
	}
});