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

require "$base_path/include/class_poll.php";

require "$base_path/include/class_pollcomment.php";



$CLASS["preview"] = new pollcomment();

$CLASS["preview"]->set_include_path($base_path);



$preview_poll_id = $CLASS["preview"]->get_latest_poll_id();



$CLASS["preview"]->set_template_set("$poll_tplset");

$CLASS["preview"]->form_forward = "#";



switch ($tpl_type) {

    

    case "display":        

        $preview = $CLASS["preview"]->display_poll($preview_poll_id);        

        break;



    case "result":

        $preview = $CLASS["preview"]->view_poll_result($preview_poll_id);

        break;



    case "comment":

        $preview = $CLASS["preview"]->poll_form($preview_poll_id);

        break;

    

    default:

        $preview = '';

}



$preview = str_replace("<form method=\"post\"", "<form method=\"post\" onsubmit=\"return false;\"",$preview);

$preview = str_replace("javascript:void(","#",$preview);

$CLASS["template"]->set_templatefiles(array(

    "admin_preview" => "admin_preview.html"

));

$admin_preview = $CLASS["template"]->pre_parse("admin_preview");

no_cache_header();

eval("echo \"$admin_preview\";");



?>