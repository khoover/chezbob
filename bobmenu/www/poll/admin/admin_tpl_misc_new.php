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



function get_tpl() {

    global $base_path, $lang;

    chdir("$base_path/templates");

    $hnd = opendir(".");

    while ($file = readdir($hnd)) {

        if (is_file("$file") && eregi(".+\\.html$",$file)) {

            $tpl_list[] = $file;

        }

    }

    closedir($hnd);

    $select_field = "<select name=\"poll_tpl_id_select\" class=\"select\">\n<option value=\"\" selected>$lang[Templates]</option>\n";

    for($i=0;$i<sizeof($tpl_list);$i++) {

        $tpl_id = htmlspecialchars($tpl_list[$i]);

        $tpl_name = str_replace(".html", "", $tpl_id);

        $select_field .= "<option value=\"$tpl_id\">$tpl_name</option>\n";

    }

    $select_field .= "</select>\n";

    return $select_field;

}



function strip_bad_chars($strg) {

    $bad_chars = array("/","\\","\"","'","?","#","+","~","<",">","*","|",":");

    for($i=0; $i<sizeof($bad_chars); $i++) {

        $strg = str_replace($bad_chars[$i],"",$strg);

    }

    return $strg;

}



function new_tpl($new_tplname) {

    global $base_path, $new_poll_tpl;

    if (!isset($new_poll_tpl)) {

        $new_poll_tpl = '';

    }

    if (get_magic_quotes_gpc()) {

        $new_poll_tpl = stripslashes($new_poll_tpl);

    }

    $fp = fopen("$base_path/templates/$new_tplname.html","w");

    flock($fp, 2);

    fwrite($fp, $new_poll_tpl);

    flock($fp, 3);

    fclose($fp);  

    return true;

}





if (!isset($new_tplname)) {

    $new_tplname = '';

} else {

    $new_tplname = trim(strip_bad_chars($new_tplname));

}



if ((empty($new_tplname) && isset($action)) || ($new_tplname == "display_head" || $new_tplname == "display_loop" || $new_tplname == "result_loop" || $new_tplname == "result_head") && isset($action)) {

    $message = $lang['tpl_bad'];

} elseif (!empty($new_tplname) && isset($action)) {

    if (file_exists("$base_path/templates/$new_tplname")) {

        $message = $lang['tpl_exist'];

    } else {

        new_tpl($new_tplname);

        $message = $lang['tpl_succes'];

    }

} else {

    $message = "Add a new template";

}



$select_field = get_tpl();



$CLASS["template"]->set_templatefiles(array(

    "admin_tpl_misc_new" => "admin_tpl_misc_new.html"

));

$admin_templates = $CLASS["template"]->pre_parse("admin_tpl_misc_new");

no_cache_header();

eval("echo \"$admin_templates\";");



?>