<?php
session_start();
function login () {
  loggedIn = 0;
  $conn = mysql_connect("localhost", "group18", "common1234");
  mysql_select_db("group18",$conn);
  if(!$result = mysql_query("SELECT * from user where username = ", $conn)) {
    loginFailure = "Please try again.";
    session_register("loginFailure");
    readfile("login_html");   
  }
  else {
    mysql_free_result ($result);
    loggedIn = 1;
    session_register("loggedIn");
    echo "<html><head><title>Users</title></head><body>\n";
    echo "<a href='loggedIn.php?<?=SID?>'>Welcome</a>\n";
    echo "</body></html>\n";
  }
}
login();
?>
