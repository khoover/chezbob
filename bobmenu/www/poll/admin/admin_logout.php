<?php
/**
 * ----------------------------------------------
 * Advanced Poll 2.0.2 (PHP)
 * Copyright (c)2001 Chi Kien Uong
 * URL: http://www.proxy2.de
 * ----------------------------------------------
 */

$base_path = dirname(__FILE__);
$base_path = dirname($base_path);
 
require "./common.inc.php";

$CLASS["session"]->generate_new_session_id($uid);

$CLASS["template"]->set_templatefiles(array(
    "login" => "admin_login.html"
));
$message = $lang['FormEnter'];
$poll_login = $CLASS["template"]->pre_parse("login");
no_cache_header();
eval("echo \"$poll_login\";");

?>