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

    $select_field = "<select name=\"poll_tplset\" class=\"select\">\n<option value=\"\" selected>$lang[Templates]</option>\n";

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



function is_valid_tplset($poll_tplset='') {

    global $base_path;

    if (!empty($poll_tplset) && @is_dir("$base_path/templates/$poll_tplset")) {

        return $poll_tplset;

    } else {

        $tpl_list = get_template_set("$base_path/templates");

        return ($tpl_list) ? reset($tpl_list) : false;            

    }

}



function update_tpl($tpl_path) {

    global $tpl;

    if (is_array($tpl)) {

        reset ($tpl);

        while (list($name, $value) = each($tpl)) {

            if (get_magic_quotes_gpc()) {

                $value = stripslashes($value);

            }

            $fp = fopen("$tpl_path/$name","w") or die("$tpl_path/$name");

            flock($fp, 2);

            fwrite($fp, $value);

            flock($fp, 3);

            fclose($fp);

        }

    }

}



function delete_tplset($tpl_path) {

    $file_list = get_template_files($tpl_path);

    if (isset($file_list)) {

        for($i=0; $i<sizeof($file_list); $i++) {

            unlink("$tpl_path/$file_list[$i]");

        }

    }

    chdir ("../");

    return (rmdir($tpl_path)) ? true : false;

}



function get_template_files($tpl_path) {

    chdir("$tpl_path");

    $hnd = opendir(".");

    while ($file = readdir($hnd)) {

        if (is_file($file)) {

            $file_list[] = $file;

        }

    }

    closedir($hnd);

    return (isset($file_list)) ? $file_list : false;

}



if (!isset($action)) {

    $action ='';

}



if ($action=="delete" and isset($poll_tplset)) {

    delete_tplset("$base_path/templates/$poll_tplset");

}



if ($action=="$lang[tpl_save]" and isset($tplset)) {

    update_tpl("$base_path/templates/$tplset");

    $poll_tplset = $tplset;

} elseif (!isset($poll_tplset)) {

    $poll_tplset ='';

}



$poll_tplset = is_valid_tplset("$poll_tplset");

$poll_tplset_name = $poll_tplset;



if (!$poll_tplset) {

    $tpl_type = "new";

} else {   

    $file_list = get_template_files("$base_path/templates/$poll_tplset");

    for($i=0; $i<sizeof($file_list); $i++) {

        $tpl['title'] = substr($file_list[$i], 0, strlen($file_list[$i])-5);

        $fd = fopen ($file_list[$i], "r");

        $poll_tpl[$tpl['title']] = fread ($fd, filesize ($file_list[$i]));

        fclose ($fd);

        $poll_tpl[$tpl['title']] = htmlspecialchars($poll_tpl[$tpl['title']]);

        $poll_tpl_id[$tpl['title']] = $file_list[$i];

    }

}



if (!isset($tpl_type)) {

    $tpl_type = "display";

}



$select_field = get_tplset();



$CLASS["template"]->set_templatefiles(array(

    "admin_templates" => "admin_tpl_".$tpl_type.".html"

));

$admin_templates = $CLASS["template"]->pre_parse("admin_templates");

no_cache_header();

eval("echo \"$admin_templates\";");



?>