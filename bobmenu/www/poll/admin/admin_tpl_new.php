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



function get_tplset() {

    global $base_path, $lang;

    $tpl_list = get_template_set("$base_path/templates");

    $select_field = "<select name=\"poll_tplset\" class=\"select\">\n<option selected>$lang[Templates]</option>\n";

    if ($tpl_list) {

        sort($tpl_list);        

        for ($i=0; $i<sizeof($tpl_list); $i++) {

            $select_field .= "<option value=\"$tpl_list[$i]\">$tpl_list[$i]</option>\n";

        }

    }

    $select_field .= "</select>\n";

    return $select_field;

}



function get_template_set($path) {

    chdir("$path");

    $hnd = opendir(".");

    while ($file = readdir($hnd)) {

        if (is_dir("$file") && $file != "." && $file != "..") {

            $tpl_list[] = $file;

        }

    }

    closedir($hnd);

    return (isset($tpl_list)) ? $tpl_list : false;

}



function strip_bad_chars($strg) {

    $bad_chars = array("/","\\","\"","'","?","#","+","~","<",">","*","|",":");

    for($i=0; $i<sizeof($bad_chars); $i++) {

        $strg = str_replace($bad_chars[$i],"",$strg);

    }

    return $strg;

}



function new_tplset($new_tplsetname) {

    global $base_path, $lang;

    $tpls = array("comment","display_head","display_loop","display_foot","result_head","result_loop","result_foot");

    if (@is_dir("$base_path/templates/$new_tplsetname")) {

        return $lang['tpl_exist'];

    } else {

        mkdir("$base_path/templates/$new_tplsetname", 0777);

        for ($i=0; $i<sizeof($tpls); $i++) {            

            $fp = fopen("$base_path/templates/$new_tplsetname/$tpls[$i].html","w") or die("Unable to create $base_path/templates/$new_tplsetname/$tpls[$i].html");

            fclose($fp);

        }

        return $lang['tpl_succes'];

    }

}





if (!isset($new_tplsetname)) {

    $new_tplsetname = '';

} else {

    $new_tplsetname = trim(strip_bad_chars($new_tplsetname));

}



if (empty($new_tplsetname) && isset($action)) {

    $message = $lang['tpl_bad'];

} elseif (!empty($new_tplsetname) && isset($action)) {

    $message = new_tplset($new_tplsetname);                    

} else {

    $message = $lang['tpl_new'];

}



$select_field = get_tplset();



$CLASS["template"]->set_templatefiles(array(

    "admin_tpl_new" => "admin_tpl_new.html"

));

$admin_templates = $CLASS["template"]->pre_parse("admin_tpl_new");

no_cache_header();

eval("echo \"$admin_templates\";");



?>