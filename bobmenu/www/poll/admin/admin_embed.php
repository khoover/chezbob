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

 

require "./common.inc.php";



$status='';

if (isset($poll_id)) {

    if (file_exists("$base_path/polldata/$poll_id")) {

        $line = file("$base_path/polldata/$poll_id");

        list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);

    }

}

if (!isset($poll_id) || $status=="2") {

    $redirect = "index.php?session=$auth[session]&uid=$auth[uid]";

    header ("Location: $redirect");

    exit();

}



$path = $base_path;

if (eregi("WIN",PHP_OS)) {

    $path = str_replace("\\","/",$path);

}

if (ereg("^3.",PHP_VERSION)) {

    $include_statement = "include";

} else {

    $version = ereg_replace("([^0-9])", "", PHP_VERSION);

    $version = $version / pow (10, strlen($version) - 1);

    $include_statement = ($version >= 4.02) ? "include_once" : "include";

}

$question = htmlspecialchars($question);



$CLASS["template"]->set_templatefiles(array(

    "admin_embed" => "admin_embed.html"

));

$admin_embed = $CLASS["template"]->pre_parse("admin_embed");

no_cache_header();

eval("echo \"$admin_embed\";");



?>