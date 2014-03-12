
bob_login = new easyXDM.Rpc({
	remote: 
}, {
});
function handle_login()
{
	//capture username and password
	var username = $("#login-username").text();
	var password = $("#login-password").text();
	
	//silly crypt will require that we get the crypted password first for a salt.
	var salt = ""
	var cryptedPassword = unixCryptTD(password, salt)
	
}

$(document).ready(function() {
	$("#btn-login").on("click", handle_login);
});