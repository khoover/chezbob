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



$source_array = array(

    "aqua","blue","brown","darkgreen","gold","green","grey","orange","pink","purple","red","yellow"

);



function add_options($poll_id) {

    global $option_id,$color,$base_path;

    $poll_fp = fopen("$base_path/polldata/$poll_id","a");

    for($i=0; $i < sizeof($option_id); $i++) {

        if (isset($option_id["$i"])) {

            $option_id["$i"] = trim($option_id["$i"]);

            $option_id["$i"] = str_replace("|","",$option_id["$i"]);

        }

        if (!empty($option_id["$i"])) {

            if (get_magic_quotes_gpc()) {

                $option_id["$i"] = stripslashes($option_id["$i"]);

            }

            fwrite($poll_fp,"$option_id[$i]|0|$color[$i]\n");

            $added = 1;

        }

    }

    fclose($poll_fp);

    return (isset($added)) ? "EditOk" : "EditNo";

}



function save($poll_id) {

    global $option_id, $votes, $color, $status, $logging, $timestamp;

    global $question, $exp_time, $expire, $comments, $base_path;

    if (!isset($expire)) {

        $expire=1;

    }

    if (!isset($comments)) {

        $comments=0;

    }

    $exp_time = time()+$exp_time*86400;

    $question = trim($question);

    $question = str_replace("|","",$question);

    if (!empty($question)) {

        if (get_magic_quotes_gpc()) {

            $question = stripslashes($question);

        }

        if (sizeof($option_id) < 2) {

            $message = "EditOp";

        } else {

            $poll_fp = fopen("$base_path/polldata/$poll_id","w");

            fwrite($poll_fp,"$question|$timestamp|$exp_time|$expire|$logging|$status|$comments\n");

            for($i=0; $i < sizeof($option_id); $i++) {

                if (!isset($option_id["$i"])) {

                    continue;

                }

                $option_id["$i"] = trim($option_id["$i"]);

                $option_id["$i"] = str_replace("|","",$option_id["$i"]);

                if (!empty($option_id[$i])) {

                    if (!eregi("^[0-9]+$", $votes[$i])) {

                        $votes[$i] = 0;

                    }

                    if (get_magic_quotes_gpc()) {

                        $option_id[$i] = stripslashes($option_id[$i]);

                    }

                    fwrite($poll_fp,"$option_id[$i]|$votes[$i]|$color[$i]\n");

                }

            }

            fclose($poll_fp);

            $message = "Updated";

        }

    } else {

        $message = "NewNoQue";

    }

    return $message;

}



function create_javascript_array() {

    global $pollvars, $source_array;

    for ($i=0, $java_script=''; $i<sizeof($source_array); $i++) {

        $java_script .= "$source_array[$i] = new Image(); $source_array[$i].src = \"$pollvars[base_gif]/$source_array[$i].gif\";\n";

    }    

    return $java_script;

}



function poll_extend($poll_id) {

    global $CLASS, $source_array, $color_array, $lang, $pollvars, $auth, $base_path;    

    $line = file("$base_path/polldata/$poll_id");

    list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);

    $question = htmlspecialchars($question); 

    $CLASS["template"]->set_templatefiles(array(

        "admin_options" => "admin_options.html"

    ));

    $java_script = create_javascript_array();

    $poll_options = '';

    $i=sizeof($line);

    $end=$i+$pollvars['def_options'];

    for ($i,$k=0; $i<$end; $i++,$k++) {

        $poll_options .=  "    <tr>

                <td width=\"15%\" class=\"td1\">$lang[NewOption] $i</td>

                <td width=\"48%\">

                  <input type=\"text\" name=\"option_id[$k]\" size=\"38\" class=\"input\" maxlength=\"100\">

                </td>

                <td width=\"12%\" class=\"td2\">

                  <select class=\"select\" name=\"color[$k]\" onChange=\"javascript:ChangeBar(options[selectedIndex].value,$k)\">

                    <option value=\"blank\">---</option>\n";

        for ($j=0; $j <sizeof($source_array); $j++) {

            $poll_options .= "<option value=\"$source_array[$j]\">$color_array[$j]</option>\n";

        }

        $poll_options .=  "       </select></td>

            <td width=\"20%\"><img src=\"$pollvars[base_gif]/blank.gif\" name=\"bar$k\" width=35 height=12></td>

        </tr>\n";

    }

    $last_option_id = '';

    $admin_options = $CLASS["template"]->pre_parse("admin_options");

    eval("echo \"$admin_options\";");    

}



function poll_edit($poll_id,$message) {

    global $CLASS, $auth, $pollvars, $color_array, $source_array, $lang, $base_path;       

    $line = file("$base_path/polldata/$poll_id");

    list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);

    $question = htmlspecialchars($question);

    $use_opt = sizeof($line);

    for ($i=1; $i<$use_opt; $i++) {

        list($name,$vote,$gif_color) = split("\\|",$line[$i]);

        $option_text[] = $name;

        $votes[] = $vote;

        $color[] = chop($gif_color);

    }

    $java_script = create_javascript_array();

    $poll_options = '';

    $status_0 = ($status == 0) ? "selected" : "";

    $status_1 = ($status == 1) ? "selected" : "";

    $status_2 = ($status == 2) ? "selected" : "";

    $logging_0 = ($logging == 0) ? "selected" : "";

    $logging_1 = ($logging == 1) ? "selected" : "";

    $poll_comments = ($comments == 1) ? "checked" : "";

    $poll_expire = ($expire == 0) ? "checked" : "";

    for ($i=0,$k=1; $i<$use_opt-1; $i++,$k++) {

        $option_text[$i] = htmlspecialchars($option_text[$i]);

        $poll_options .= "         <tr>

                  <td width=\"20%\" class=\"td1\">$lang[NewOption] $k</td>

                  <td width=\"49%\">

                    <input type=\"text\" name=\"option_id[$i]\" size=\"35\" class=\"input\" value=\"$option_text[$i]\">

                  </td>

                  <td width=\"11%\" class=\"td2\">

                    <input type=\"text\" name=\"votes[$i]\" class=\"input2\" size=\"10\" value=\"$votes[$i]\">

                  </td>

                  <td width=\"11%\" class=\"td2\">

                   <select name=\"color[$i]\" class=\"select\" onChange=\"javascript:ChangeBar(options[selectedIndex].value,$i)\">

                   <option value=\"blank\">---</option>\n";

        for ($j=0; $j<sizeof($source_array); $j++) {

            if ($color[$i] == $source_array["$j"]) {

                $poll_options .= "<option value=\"$source_array[$j]\" selected>$color_array[$j]</option>\n";

            } else {

                $poll_options .= "<option value=\"$source_array[$j]\">$color_array[$j]</option>\n";

            }

        }

        $poll_options .= "          </select>

                  </td>

                  <td width=\"9%\"><img src=\"$pollvars[base_gif]/$color[$i].gif\" name=\"bar$i\" width=35 height=12></td>

                </tr>\n";

    }

    $expiration = round (($exp_time-time())/86400);

    if ($expiration<=0) {

        $expiration = 0;

    }

    $CLASS["template"]->set_templatefiles(array(

        "admin_edit" => "admin_edit.html"

    ));

    $admin_edit = $CLASS["template"]->pre_parse("admin_edit");

    eval("echo \"$admin_edit\";");

}



function is_valid_poll_id($poll_id) {

    global $base_path;

    if ($poll_id>0) {

        if (file_exists("$base_path/polldata/$poll_id")) {

            return true;

        } else {

            return false;

        }

    } else {

        return false;

    }

}



if (!isset($poll_id) || !is_valid_poll_id($poll_id)) {

    $redirect = "index.php?session=$auth[session]&uid=$auth[uid]";

    header ("Location: $redirect");

    exit();

}



if (!isset($action)) {

    $action='';

}



no_cache_header();



switch ($action) {



    case "save":

        $message = save($poll_id);

        poll_edit($poll_id,"$lang[$message]");

        break;



    case "extend":

        poll_extend($poll_id);

        break;



    case "add":

        $message = add_options($poll_id,$last_id);

        $message = $lang[$message];

        poll_edit($poll_id,"$message");

        break;



    default:

        $message = $lang["EditText"];

        poll_edit($poll_id,"$message");

}





?>