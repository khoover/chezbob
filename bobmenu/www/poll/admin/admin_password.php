<?php
/**
 * ----------------------------------------------
 * Advanced Poll 2.0.2 (PHP)
 * Copyright (c)2001 Chi Kien Uong
 * URL: http://www.proxy2.de
 * ----------------------------------------------
 */

$include_path = dirname(__FILE__);
$base_path = dirname($include_path);

require "$base_path/include/class_text_cfg.php";

require "./common.inc.php";

function update_user($poll_user,$poll_pass) {
    global $base_path;
    include ("$base_path/include/config.inc.php");
    $poll_pass = md5($poll_pass);
    $CLASS["text_cfg"] = new text_cfg();
    $CLASS["text_cfg"]->set_rootdir("$base_path/include");
    $pollvars['poll_username'] = $poll_user;
    $pollvars['poll_password'] = $poll_pass;
    $result = $CLASS["text_cfg"]->update_cfg("pollvars",$pollvars);    
    return ($result) ? "Updated" : "NoUpdate";
}

if (!isset($action)) {
    $action='';
}

if ($action== "update_pwd") {
    if (!empty($NEWadmin_name)) {
        $username = trim($NEWadmin_name);
    }
    if (!empty($NEWadmin_pass)) {
        $userpass = trim($NEWadmin_pass);
        if (get_magic_quotes_gpc()) {
            $userpass = stripslashes($userpass);
        }
    }
    $lang_mes = update_user($username,$userpass);
    include ("$base_path/include/config.inc.php");
} else {
    $lang_mes = "PwdText";
}

$CLASS["template"]->set_templatefiles(array(
    "admin_password" => "admin_password.html"
));

$message = $lang[$lang_mes];
$username = htmlspecialchars($pollvars['poll_username']);
$password_settings = $CLASS["template"]->pre_parse("admin_password");
no_cache_header();
eval("echo \"$password_settings\";");

?>