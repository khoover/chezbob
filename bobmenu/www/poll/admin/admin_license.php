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



$CLASS["template"]->set_templatefiles(array(

    "admin_license" => "admin_license.html"

));

$admin_license = $CLASS["template"]->pre_parse("admin_license");

no_cache_header();

eval("echo \"$admin_license\";");



?>