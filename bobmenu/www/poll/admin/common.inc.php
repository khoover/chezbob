<?php

/**

 * ----------------------------------------------

 * Advanced Poll 2.0.2 (PHP)

 * Copyright (c)2001 Chi Kien Uong

 * URL: http://www.proxy2.de

 * ----------------------------------------------

 */



require "../include/config.inc.php";

require "../include/class_session.php";

require "../include/class_template.php";



function no_cache_header() {

    header("Expires: Mon, 26 Jul 1997 05:00:00 GMT");

    header("Last-Modified: " . gmdate("D, d M Y H:i:s") . "GMT");

    header("Cache-Control: no-cache, must-revalidate");

    header("Pragma: no-cache");        

}



if (!isset($PHP_SELF)) {

    $PHP_SELF = $HTTP_SERVER_VARS["PHP_SELF"];

    if (isset($HTTP_GET_VARS)) {

        while (list($name, $value)=each($HTTP_GET_VARS)) {

            $$name=$value;

        }

    }

    if (isset($HTTP_POST_VARS)) {

        while (list($name, $value)=each($HTTP_POST_VARS)) {

            $$name=$value;

        }

    }

    if(isset($HTTP_COOKIE_VARS)){

        while (list($name, $value)=each($HTTP_COOKIE_VARS)){

            $$name=$value;

        }

    }

}



$pollvars['SELF'] = basename($PHP_SELF);

unset($lang);

if (file_exists("$base_path/lang/$pollvars[lang]")) {

    include ("$base_path/lang/$pollvars[lang]");

} else {

    include ("$base_path/lang/english.php");    

}

$CLASS["template"] = new poll_template();

$CLASS["template"]->set_rootdir("$base_path/admin/templates");



$CLASS["session"] = new poll_session("$base_path/polldata");



$auth = $CLASS["session"]->check_session_id();



if (!$auth) {  

    $message = (isset($username) || isset($password)) ? $lang['FormWrong'] : $lang['FormEnter'];

    $CLASS["template"]->set_templatefiles(array(

		"login" => "admin_login.html"

    ));

    $poll_login = $CLASS["template"]->pre_parse("login");

    no_cache_header();

    eval("echo \"$poll_login\";");

    exit();

    

}



?>