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



function get_valid_tpl_id($poll_tpl='') {

    global $base_path;    

    if (!empty($poll_tpl) && file_exists("$base_path/templates/$poll_tpl")) {

        return $poll_tpl;

    } else {

        chdir("$base_path/templates");

        $hnd = opendir(".");

        while ($file = readdir($hnd)) {

            if (is_file("$file") && eregi(".+\\.html$",$file)) {

                $tpl_list[] = $file;

            }

        }

        closedir($hnd);

        if (sizeof($tpl_list)>0) {

            sort($tpl_list);

            return $tpl_list[0];

        } else {

            return false;

        }

    }

}



function update_tpl($poll_tpl_id) {

    global $base_path, $poll_tpl; 

    if (isset($poll_tpl) && file_exists("$base_path/templates/$poll_tpl_id")) {

        if (get_magic_quotes_gpc()) {

            $poll_tpl = stripslashes($poll_tpl);

        }

        $fp = fopen("$base_path/templates/$poll_tpl_id","w");

        flock($fp, 2);

        fwrite($fp, $poll_tpl);

        flock($fp, 3);

        fclose($fp);

    }

}



if (!isset($action)) {

    $action ='';

}



if ($action=="delete" and isset($poll_tpl_id)) {

    unlink("$base_path/templates/$poll_tpl_id");

}



if ($action=="$lang[tpl_save]" and isset($poll_tpl)) {

    update_tpl($poll_tpl_id);

}



$tpl_id = (isset($poll_tpl_id_select)) ? $poll_tpl_id_select : '';

if (empty($tpl_id)) {

    $tpl_id = (isset($poll_tpl_id)) ? $poll_tpl_id : '';

}



$poll_tpl_id = get_valid_tpl_id($tpl_id);



if (!$poll_tpl_id) {

    $tpl_type = "new";

    $message = $lang['tpl_new'];

} else {

    if (isset($poll_tpl) && !empty($poll_tpl) && $action=="$lang[tpl_save]") {

        $tpl['template'] = htmlspecialchars(stripslashes($poll_tpl));

        $tpl['title'] = htmlspecialchars($poll_tpl_id);

        $tpl['title'] = str_replace(".html", "", $tpl['title']);

        $tpl['tpl_id'] = htmlspecialchars($poll_tpl_id);   

    } else {

        $fd = fopen ("$base_path/templates/$poll_tpl_id", "r");

        $tpl['template'] = fread ($fd, filesize ("$base_path/templates/$poll_tpl_id"));

        fclose ($fd);    

        $tpl['template'] = htmlspecialchars($tpl['template']);

        $tpl['title'] = htmlspecialchars($poll_tpl_id);

        $tpl['title'] = str_replace(".html", "", $tpl['title']);

        $tpl['tpl_id'] = htmlspecialchars($poll_tpl_id);

    }

}



if (!isset($tpl_type)) {

    $tpl_type = "edit";

}



$select_field = get_tpl();



$CLASS["template"]->set_templatefiles(array(

    "admin_templates" => "admin_tpl_misc_".$tpl_type.".html"

));

$admin_templates = $CLASS["template"]->pre_parse("admin_templates");

no_cache_header();

eval("echo \"$admin_templates\";");



?>