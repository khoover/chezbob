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



function delete_comment($poll_id,$message_id) {

    global $base_path;

    $comment_array = file("$base_path/polldata/$poll_id.dat");

    if (sizeof($comment_array)>0) {

        $poll_comment = fopen("$base_path/polldata/$poll_id.dat","w");

        for ($i=0; $i<sizeof($comment_array); $i++) {

            if ($i != $message_id) {

                fwrite($poll_comment,"$comment_array[$i]");

            }

        }

        fclose($poll_comment);

    }

}



if (!isset($action)) {

    $action='';

}

if ($action=="delete" and isset($mess_id) and isset($poll_id)) {

    delete_comment($poll_id,$mess_id);

}



$time_offset = $pollvars["time_offset"]*3600;

$line = file("$base_path/polldata/$poll_id");

list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);

$question = htmlspecialchars($question);

if (file_exists("$base_path/polldata/$poll_id.dat")) {

    $comment_array = file("$base_path/polldata/$poll_id.dat");

    $total = sizeof($comment_array);

} else {

    $total = 0;

}

if(!isset($entry)) {

    $entry = 0;

}

$next_page = $entry+$pollvars["entry_pp"];

$prev_page = $entry-$pollvars["entry_pp"];

$navigation ='';

if ($prev_page >= 0) {

    $navigation = "   <img src=\"$pollvars[base_gif]/back.gif\" width=\"16\" height=\"14\">&nbsp;<a href=\"$pollvars[SELF]?session=$auth[session]&uid=$auth[uid]&poll_id=$poll_id&entry=$prev_page\">$lang[NavPrev]</a>\n";

}

if ($next_page < $total) {

    $navigation = $navigation. " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href=\"$pollvars[SELF]?session=$auth[session]&uid=$auth[uid]&poll_id=$poll_id&entry=$next_page\">$lang[NavNext]</a>&nbsp;<img src=\"$pollvars[base_gif]/next.gif\" width=\"16\" height=\"14\">\n";

}



$CLASS["template"]->set_templatefiles(array(

    "admin_comment"    => "admin_comment.html",

    "admin_comment_tr" => "admin_comment_tr.html"

));

$CLASS["template"]->register_vars("admin_comment_tr",array(

    "message" => "\$message",

    "browser" => "\$browser",

    "name"    => "\$name",

    "host"    => "\$host",

    "com_id"  => "\$i"

));

$admin_comment_tr = '';

$comment_tr = $CLASS["template"]->pre_parse("admin_comment_tr");



if ($total >0) {

    $start = $total-1-$entry;

    $finish = $total-$entry-$pollvars['entry_pp'];

    if ($finish <=0) {

        $finish=0;

    }

    for ($i=$start; $i>=$finish; $i--) {

        if (ereg("^[0-9]+¡.+¡.*¡.+¡.*¡.+",$comment_array[$i])) {

            list($post_time,$host,$browser,$name,$email,$message) = split("¡",$comment_array[$i]);

            $date = date("j-M-Y H:i",$post_time+$time_offset);

            $email = ($email) ? "<a href=\"mailto:$email\"><img src=\"$pollvars[base_gif]/email.gif\" width=\"15\" height=\"15\" border=\"0\" alt=\"$email\"></a>\n" : "";

            if (eregi("Opera",$browser)) {

                $image = "$pollvars[base_gif]/opera.gif";

            } elseif (eregi("MSIE",$browser)) {

                $image = "$pollvars[base_gif]/msie.gif";

            } elseif (eregi("Mozilla",$browser)) {

                $image = "$pollvars[base_gif]/netscape.gif";

            } else {

                $image = "$pollvars[base_gif]/unknown.gif";	

            }

            eval("\$admin_comment_tr .= \"$comment_tr\";");

        }        

    }

}



$comments = $CLASS["template"]->pre_parse("admin_comment");

no_cache_header();

eval("echo \"$comments\";");



?>