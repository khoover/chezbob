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

function delete_poll($poll_id) {
    if (file_exists("../polldata/$poll_id")) {
        unlink("../polldata/$poll_id");
    }
    if (file_exists("../polldata/$poll_id.ip")) {
        unlink("../polldata/$poll_id.ip");
    }
    if (file_exists("../polldata/$poll_id.log")) {
        unlink("../polldata/$poll_id.log");
    }
    if (file_exists("../polldata/$poll_id.dat")) {
        unlink("../polldata/$poll_id.dat");
    }
}

function rsort_poll($a,$b) {
    if ($a == $b) return 0;
    return ($a > $b) ? -1 : 1;
}

function poll_index() {
    global $CLASS, $auth, $pollvars, $entry, $lang, $weekday, $months, $base_path;
    if(!isset($entry)) {
        $entry = 0;
    }
    $ip = getenv("REMOTE_ADDR");
    $time_offset = $pollvars["time_offset"]*3600;
    list($wday,$mday,$month,$year,$hour,$minutes) = split("( )",date("w j n Y H i",time()+$time_offset));
    $newdate = "$weekday[$wday], $mday ".$months[$month-1]." $year $hour:$minutes";
    $navigation ='';
    $CLASS["template"]->set_templatefiles(array(
        "index" => "admin_index.html",
        "index_tr" => "admin_index_tr.html"
    ));
    $CLASS["template"]->register_vars("index_tr",array(
        "poll_id" => "\$poll_id"
    ));
    $index_tr = $CLASS["template"]->pre_parse("index_tr");
    $admin_index_tr = '';
    chdir("$base_path/polldata");
    $hnd = opendir(".");
    while ($file = readdir($hnd)) {
        if (eregi("([0-9]+$)", $file)) {
            $poll_list[] = $file;
        }
    }
    closedir($hnd);
    if (isset($poll_list)) {
        usort($poll_list,"rsort_poll");
        $total = sizeof($poll_list);        
        $show_max = ($entry+$pollvars['polls_pp']>$total) ? $total : $entry+$pollvars['polls_pp']; 
        for ($i=$entry; $i<$show_max; $i++) {
            $line = file($poll_list[$i]);
            if (eregi("([0-9]+$)", $poll_list[$i], $regs)) {
                $poll_id = $regs[1];
            }
            list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);
            $question = htmlspecialchars($question);
            $date = date("j-M-Y",$timestamp+$time_offset);
            if ($expire==0) {
                $exp_date = "<font color=\"#0000FF\">$lang[IndexNever]</font>";
            } else {
                $exp_date = (time()>$exp_time) ? "<font color=\"#FF6600\">$lang[IndexExpire]</font>" : date("j-M-Y",$exp_time+$time_offset)." (<font color=\"#FF0000\">".round(($exp_time-time())/86400)."</font>)";
            }
            $days = (int) ((time()-$timestamp+$time_offset)/86400);
            if ($status==1) {
                $image = "$pollvars[base_gif]/folder.gif";
                $alt = "$lang[EditOn]";
            } elseif ($status==2) {
                $image = "$pollvars[base_gif]/hidden.gif";
                $alt = "$lang[EditHide]";
            } else {
                $image = "$pollvars[base_gif]/lock.gif";
                $alt = "$lang[EditOff]";
            }
            $alt = htmlspecialchars($alt);
            $image2 = ($logging == 1) ? "$pollvars[base_gif]/log.gif" : "$pollvars[base_gif]/log_off.gif";
            $image3 = ($comments == 1) ? "$pollvars[base_gif]/reply.gif" : "$pollvars[base_gif]/co_dis.gif";
            $image4 = ($status == 2) ? "$pollvars[base_gif]/text_off.gif" : "$pollvars[base_gif]/text.gif";        
            eval("\$admin_index_tr .= \"$index_tr\";");
        }
        $next_page = $entry+$pollvars['polls_pp'];
        $prev_page = $entry-$pollvars['polls_pp'];
        if ($prev_page >= 0) {
            $navigation = "  <img src=\"$pollvars[base_gif]/back.gif\" width=\"16\" height=\"14\">&nbsp;<a href=\"$pollvars[SELF]?session=$auth[session]&uid=$auth[uid]&entry=$prev_page\">$lang[NavPrev]</a>\n";
        }
        if ($next_page < $total) {
            $navigation = $navigation. "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href=\"$pollvars[SELF]?session=$auth[session]&uid=$auth[uid]&entry=$next_page\">$lang[NavNext]</a>&nbsp;<img src=\"$pollvars[base_gif]/next.gif\" width=\"16\" height=\"14\">\n";
        }
    }
    $poll_user = str_replace("\$", "\\\$", $pollvars['poll_username']); 
    $CLASS["template"]->register_vars("index", array(
        "poll_user"      => $poll_user,
        "poll_host"      => $ip
    ));
    $admin_index = $CLASS["template"]->pre_parse("index");
    eval("echo \"$admin_index\";");
}

function poll_new($message) {
    global $CLASS, $auth, $pollvars, $lang, $color_array;
    $source_array = array(
        "aqua","blue","brown","darkgreen","gold","green","grey","orange","pink","purple","red","yellow"
    );
    for ($i=0,$java_script='';$i<sizeof($source_array); $i++) {
        $java_script .= "$source_array[$i] = new Image(); $source_array[$i].src = \"$pollvars[base_gif]/$source_array[$i].gif\";\n";
    }
    for ($i=1,$poll_options=''; $i < $pollvars['def_options']+1; $i++) {
        $poll_options .= "        <tr>
                 <td width=\"25%\" class=\"td1\">$lang[NewOption] $i</td>
                 <td width=\"40%\">
                   <input type=\"text\" name=\"option_id[$i]\" size=\"38\" class=\"input\" maxlength=\"100\">
                 </td>
                 <td class=\"td2\" width=\"10%\">
                   <select class=\"select\" name=\"color[$i]\" onChange=\"javascript:ChangeBar(options[selectedIndex].value,$i)\">
                    <option value=\"blank\">---</option>\n";
        for ($j=0; $j <sizeof($source_array); $j++) {
            $poll_options .= "<option value=\"$source_array[$j]\">$color_array[$j]</option>\n";
        }
        $poll_options .= "       </select></td>
            <td width=\"25%\" align=\"left\"><img src=\"$pollvars[base_gif]/blank.gif\" name=\"bar$i\" width=\"35\" height=\"12\"></td>
            </tr>\n";
    }
    $CLASS["template"]->set_templatefiles(array(
        "admin_new" => "admin_new.html"
    ));
    $admin_new = $poll_login = $CLASS["template"]->pre_parse("admin_new");
    eval("echo \"$admin_new\";");
}

function create_poll() {
    global $logging, $expire, $exp_time, $status, $comments, $base_path;
    global $option_id, $question, $color;
    $timestamp = time();
    if (!isset($expire)) {
        $expire=1;
    }
    if (!isset($comments)) {
        $comments=0;
    }
    if (!isset($exp_time)) {
        $exp_time = $timestamp;
    } else {
        $exp_time = $timestamp+$exp_time*86400;
    }
    if (get_magic_quotes_gpc()) {
        $question = stripslashes($question);
    }
    chdir("$base_path/polldata");
    $hnd = opendir(".");
    while ($file = readdir($hnd)) {
        if (eregi("([0-9]+$)", $file)) {
            $poll_list[] = $file;
        }
    }
    closedir($hnd);
    if (isset($poll_list)) {
        usort($poll_list,"rsort_poll");
        $new_id = $poll_list[0]+1;
    } else {
        $new_id = 1;
    }
    $poll_fp = fopen("$base_path/polldata/$new_id","w");
    fwrite($poll_fp,"$question|$timestamp|$exp_time|$expire|$logging|$status|$comments\n");
    for($i=1; $i <= sizeof($option_id); $i++) {
        $option_id[$i] = trim($option_id[$i]);
        $option_id[$i] = str_replace("|","",$option_id[$i]);
        if (!empty($option_id[$i])) {
            if (get_magic_quotes_gpc()) {
                $option_id[$i] = stripslashes($option_id[$i]);
            }
            fwrite($poll_fp,"$option_id[$i]|0|$color[$i]\n");
        }
    }
    fclose($poll_fp);
}

if (!isset($action)) {
    $action='';
}

no_cache_header();

switch ($action) {

    case "new":
        $message = $lang["NewTitle"];
        poll_new("$message");
        break;

    case "show":
        poll_index();
        break;

    case "delete":
        if (isset($id)) {
            delete_poll($id);
        }
        poll_index();
        break;

    case "create":
        $question = trim($question);
        if (!empty($question)) {
            create_poll();            
            poll_index();
        } else {
            $message = $lang["EditMis"];
            poll_new("$message");
        }
        break;

    default:
        poll_index();
        break;
}

?>