<?php

/**

 * ----------------------------------------------

 * Advanced Poll 2.0.2 (PHP)

 * Copyright (c)2001 Chi Kien Uong

 * URL: http://www.proxy2.de

 * ----------------------------------------------

 */



class poll {



    var $pollvars = array();

    var $poll_view_html = array();

    var $poll_result_html = array();

    var $include_path = '.';

    var $form_forward = '';

    var $template_set = '';

    var $poll_array = array();

    var $color_array = array();

    var $total_votes = '';

    var $question = '';

    var $poll_question = array(); 

    var $comments = '';

    var $ip = '';



    function poll() {

        global $pollvars, $HTTP_SERVER_VARS;

        if (isset($HTTP_SERVER_VARS['HTTP_X_FORWARDED_FOR']) && eregi("^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$",$HTTP_SERVER_VARS['HTTP_X_FORWARDED_FOR'])) {

            $this->ip = $HTTP_SERVER_VARS['HTTP_X_FORWARDED_FOR'];

        } else {

            $this->ip = getenv("REMOTE_ADDR");

        }

        $this->pollvars = $pollvars;

        $this->template_set = "default";

        $this->form_forward = basename($HTTP_SERVER_VARS['PHP_SELF']);

        $this->include_path = dirname(dirname(__FILE__));

    }



    function set_template_set($template_set='') {

        if (empty($template_set) || !file_exists("$this->include_path/templates/$template_set/display_foot.html")) {

            $this->template_set = "default";

        } else {

            $this->template_set = $template_set;

        }

        return $this->template_set;

    }

    

    function set_include_path($path) {

        if (!@is_dir($path)) {

            return false;

        }

        $this->include_path = $path;

        return true;

    }



    function set_display_order($order='') {

        switch ($order) {

            case "asc":

                $this->pollvars['result_order'] = "asc";

                break;

            case "desc":

                $this->pollvars['result_order'] = "desc";

                break;

            default:

                $this->pollvars['result_order'] = "";

                return false;

        }

        return true;

    }



    function set_display_result($result='') {

        switch ($result) {

            case "votes":

                $this->pollvars['type'] = "votes";

                break;

            case "percent":

                $this->pollvars['type'] = "percent";

                break;

            default:

                return false;

        }

        return true;

    }



    function set_max_bar_length($max_bar_length='') {

        if ($max_bar_length && $max_bar_length>0) {

            $this->pollvars['img_length'] = $max_bar_length;

            return true;

        } else {

            return false;

        }

    }



    function set_max_bar_height($max_bar_height='') {

        if ($max_bar_height && $max_bar_height>0) {

            $this->pollvars['img_height'] = $max_bar_height;

            return true;

        } else {

            return false;

        }

    }

    

    function get_poll_tpl($tpl) {

        $filename = "$this->include_path/templates/$this->template_set/$tpl.html";

        if (file_exists("$filename")) {

            $fd = fopen ($filename, "r");

            $template = fread ($fd, filesize ($filename));

            fclose ($fd);

            $template = ereg_replace("\"", "\\\"", $template);

            return $template;

        } else {

            return false;

        }

    }



    function set_max_bar_length($max_bar_length='') {

        if ($max_bar_length && $max_bar_length>0) {

            $this->pollvars['img_length'] = $max_bar_length;

        }

        return $this->pollvars['img_length'];

    }



    function lock_poll_ip($poll_id) {

        $this_time = time();

        if (file_exists("$this->include_path/polldata/$poll_id.ip")) {

            $ip_array = file("$this->include_path/polldata/$poll_id.ip");

            $ip_table = fopen("$this->include_path/polldata/$poll_id.ip","wb");

            flock($ip_table, 2);

            for ($i=0; $i<sizeof($ip_array); $i++) {

                list ($ip_addr, $time_stamp) = split("\\|",$ip_array[$i]);

                if ($this_time < ($time_stamp+3600*$this->pollvars['lock_timeout'])) {

                    if ($ip_addr == $this->ip) {

                        continue;

                    }

                    fwrite($ip_table,"$ip_addr|$time_stamp");

                }

            }

            fwrite($ip_table,"$this->ip|$this_time\n");

            flock($ip_table, 3);

            fclose($ip_table);

        } else {

            $ip_table = fopen("$this->include_path/polldata/$poll_id.ip","wb");

            fwrite($ip_table,"$this->ip|$this_time\n");

            fclose($ip_table);

        }

    }



    function log_vote($poll_id) {

        $this_time = date("j-M-Y H:i",time());

        $host = @gethostbyaddr($this->ip);

        $agent = @getenv("HTTP_USER_AGENT");

        $log_table = fopen("$this->include_path/polldata/$poll_id.log","a");

        flock($log_table, 2);

        fwrite($log_table,"$this_time|$this->ip|$host|$agent\n");

        flock($log_table, 3);

        fclose($log_table);

    }



    function get_poll_data($poll_id) {

        $this->total_votes=0;

        if (file_exists("$this->include_path/polldata/$poll_id")) {

            $line = file("$this->include_path/polldata/$poll_id");

            if (ereg(".*\\|[0-9]+\\|[0-9]+\\|[0-9]{1}\\|[0-9]{1}\\|[0-9]{1}\\|[0-9]{1}",$line[0])) {

                list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);

                $this->question = htmlspecialchars($question);

                $this->comments = chop($comments);

                $this->poll_array = '';

                $this->color_array = '';

                for ($i=1; $i<sizeof($line); $i++) {

                    list($name,$vote,$gif_color) = split("\\|",$line[$i]);

                    $this->poll_array[$name] = $vote;

                    $this->color_array[$name] = chop($gif_color);

                    $this->total_votes += $vote;

                }

                for (reset($this->poll_array),$this->maxvote=0; $key=key($this->poll_array); next($this->poll_array)) {

                    $this->maxvote = ($this->poll_array[$key]>$this->maxvote) ? $this->poll_array[$key] : $this->maxvote;

                }

                return true;

            }

        } else {

            return false;

        }

    }



    function get_poll_stat($poll_id) {

        $line = file("$this->include_path/polldata/$poll_id");

        list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);

        $comments = chop($comments);

        return (sizeof($line)>0) ? array(

            "question"  => "$question",

            "timestamp" => "$timestamp",

            "exp_time"  => "$exp_time",

            "expire"    => "$expire",

            "logging"   => "$logging",

            "status"    => "$status",

            "comments"  => "$comments"

        ) : false;

    }



    function get_poll_list() {

        $hnd = opendir("$this->include_path/polldata");

        while ($file = readdir($hnd)) {

            if (eregi("([0-9]+$)", $file)) {

                $poll_list[] = $file;

            }

        }

        closedir($hnd);

        if (isset($poll_list)) {

            usort($poll_list,"rsort_poll");

            for ($i=0; $i<sizeof($poll_list); $i++) {

                $line = file("$this->include_path/polldata/$poll_list[$i]");

                list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);

                if ($status==0 || $status==1) {

                    if (eregi("([0-9]+$)", $poll_list[$i], $regs)) {

                        $available_polls[] = $regs[1];

                    }

                }

            }

        }

        return (isset($available_polls)) ? $available_polls : false ;

    }



    function update_poll($poll_id,$option_id) {

        if (get_magic_quotes_gpc()) {

            $option_id = stripslashes($option_id);

        }

        if ($this->pollvars['check_ip'] == 2) {

            $this->lock_poll_ip($poll_id);

        }

        $stat_array = $this->get_poll_stat($poll_id);

        if ($stat_array['logging'] == 1) {

            $this->log_vote($poll_id);

        }

        $line = file("$this->include_path/polldata/$poll_id");

        $count_dat = fopen("$this->include_path/polldata/$poll_id","w");

        flock($count_dat, 2);

        $line[0] = chop($line[0]);

        fwrite($count_dat,"$line[0]\n");

        for ($i=1; $i<sizeof($line); $i++) {

            list($name,$vote,$gif_color) = split("\\|",$line[$i]);

            if ($name == $option_id) {

                $vote += 1;

            }

            $gif_color = chop($gif_color);

            fwrite($count_dat,"$name|$vote|$gif_color\n");

        }

        flock($count_dat, 3);

        fclose($count_dat);

    }



    function get_poll_question($poll_id) {

        if (!isset($this->poll_question[$poll_id]) && file_exists("$this->include_path/polldata/$poll_id")) {           

            $line = file("$this->include_path/polldata/$poll_id");

            if (ereg(".*\\|[0-9]+\\|[0-9]+\\|[0-9]{1}\\|[0-9]{1}\\|[0-9]{1}\\|[0-9]{1}",$line[0])) {

                list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);

                $this->poll_question[$poll_id] = htmlspecialchars($question);

            } else {

                $this->poll_question[$poll_id] = '';

            }            

        } else {

            $this->poll_question[$poll_id] = '';

        }

        return $this->poll_question[$poll_id];

    }



    function display_poll($poll_id) {

        if (!isset($this->poll_view_html[$poll_id]) || !isset($this->poll_view_html[$poll_id][$this->template_set])) {

            if ($this->get_poll_data($poll_id)) {

                $pollvars = $this->pollvars;

                $question = $this->question;

                eval("\$display_html = \"".$this->get_poll_tpl("display_head")."\";");

                $loop_html = $this->get_poll_tpl("display_loop");

                for (reset($this->poll_array); $key=key($this->poll_array); next($this->poll_array)) {

                    $key = htmlspecialchars($key);

                    eval("\$display_html .= \"$loop_html\";");

                }

                eval("\$display_html .= \"".$this->get_poll_tpl("display_foot")."\";");

                $this->poll_view_html[$poll_id][$this->template_set] = $display_html;

            } else {

                return '';

            }        

        }

        return $this->poll_view_html[$poll_id][$this->template_set];

    }



    function view_poll_result($poll_id,$vote_stat=0) {

        if (!isset($this->poll_result_html[$poll_id]) || !isset($this->poll_result_html[$poll_id][$this->template_set])) {

            if ($this->get_poll_data($poll_id)) {

                $pollvars = $this->pollvars;

                $question = $this->question;

                eval("\$result_html = \"".$this->get_poll_tpl("result_head")."\";");

                $loop_html = $this->get_poll_tpl("result_loop");

                if (count($this->poll_array)) {                

                    if ($this->pollvars['result_order'] == "asc") {

                        uasort($this->poll_array,"sort_poll");

                    } elseif ($this->pollvars['result_order'] == "desc") {

                        uasort($this->poll_array,"rsort_poll");

                    }

                    $top_pos = (int) ($this->maxvote);

                }

                $total = ($this->total_votes<=0) ? 1 : $this->total_votes;

                $top_pos = ($this->total_votes==0) ? 1 : (int) ($this->maxvote);

                for (reset($this->poll_array); $key=key($this->poll_array); next($this->poll_array)) {

                    $vote_val = ($this->pollvars['type']=="percent") ? sprintf("%.1f",($this->poll_array[$key]*100/$total))."%" : $this->poll_array[$key];

                    $vote_percent = sprintf("%.2f",($this->poll_array[$key]*100/$total));

                    $vote_count = $this->poll_array[$key];

                    $img_width = (int) ($this->poll_array[$key]*$this->pollvars['img_length']/$top_pos);

                    $image = $this->color_array[$key];

                    $key_val = htmlspecialchars($key);                

                    eval("\$result_html .= \"$loop_html\";");

                }

                $VOTE = ($vote_stat==1) ? $this->pollvars['voted'] : '';

                $COMMENT = ($this->comments==1) ? "<a href=\"javascript:void(window.open('$pollvars[base_url]/comments.php?action=send&amp;id=$poll_id&amp;template_set=$this->template_set','$poll_id','width=230,height=320,toolbar=no,statusbar=no'))\">".$this->pollvars['send_com']."</a>" : '';

                eval("\$result_html .= \"".$this->get_poll_tpl("result_foot")."\";");

                $this->poll_result_html[$poll_id][$this->template_set] = $result_html;

            } else {

                return '';

            }

        }

        return $this->poll_result_html[$poll_id][$this->template_set];

    }



    function get_random_poll_id() {

        $hnd = opendir("$this->include_path/polldata");

        while ($file = readdir($hnd)) {

            if (eregi("([0-9]+$)", $file)) {

                $poll_list[] = $file;

            }

        }

        closedir($hnd);

        if (isset($poll_list)) {

            usort($poll_list,"sort_poll");

            for ($i=0; $i<sizeof($poll_list); $i++) {

                $line = file("$this->include_path/polldata/$poll_list[$i]");

                list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);

                if (($status==1 && $expire==0) || ($status==1 && $exp_time>time())) {

                    if (eregi("([0-9]+$)", $poll_list[$i], $regs)) {

                        $poll_id_arr[] = $regs[1];

                    }

                }

            }

        }

        if (!isset($poll_id_arr)) {

            return 0;

        }

        $available = sizeof($poll_id_arr)-1;

        srand((double) microtime() * 1000000);

        $random_id = ($available>0) ? rand(0,$available) : 0;

        return $poll_id_arr[$random_id];

    }



    function get_latest_poll_id() {

        $poll_ids = $this->get_poll_list();

        if (!$poll_ids) {

            return 0;

        }

        return $poll_ids[0];

    }



    function is_valid_poll_id($poll_id) {

        if ($poll_id>0) {

            if (!file_exists("$this->include_path/polldata/$poll_id")) {

                return false;

            } else {

                $stat_array = $this->get_poll_stat($poll_id);

                return ($stat_array["status"]==2) ? false : true;

            }

        } else {

            return false;

        }

    }



    function has_voted($poll_id) {

        global $HTTP_COOKIE_VARS;

        $pollcookie = "AdvancedPoll".$poll_id;

        if (isset($HTTP_COOKIE_VARS[$pollcookie])) {

            return true;

        }

        if ($this->pollvars['check_ip']==2) {

            $found=false;

            if (file_exists("$this->include_path/polldata/$poll_id.ip")) {

                $ip_array = file("$this->include_path/polldata/$poll_id.ip");

                $this_time = time();

                for ($i=0; $i<sizeof($ip_array); $i++) {

                    list ($ip_addr, $time_stamp) = split("\\|",$ip_array[$i]);

                    if ($this_time < ($time_stamp+3600*$this->pollvars['lock_timeout'])) {

                        if ($this->ip == $ip_addr) {

                            $found=true;

                            break;

                        }

                    }

                }

            }

            return $found;

        } else {

            return false;

        }

    }



    function is_active_poll_id($poll_id) {

        if ($poll_id>0) {

            if (!file_exists("$this->include_path/polldata/$poll_id")) {

                return false;

            } else {

                $stat_array = $this->get_poll_stat($poll_id);

                if ($stat_array["expire"]==0) {

                    return true;

                }

                return ($stat_array['exp_time']<time()) ? false : true;

            }

        } else {

            return false;

        }

    }



    function get_query_strg($self) {

        global $HTTP_SERVER_VARS;

        if (isset($HTTP_SERVER_VARS['QUERY_STRING']) && !empty($HTTP_SERVER_VARS['QUERY_STRING'])) {

            if (ereg("($self=[0-9]+)",$HTTP_SERVER_VARS['QUERY_STRING'],$regs)) {

                $HTTP_SERVER_VARS['QUERY_STRING'] = str_replace($regs[1], "", $HTTP_SERVER_VARS['QUERY_STRING']);                                

            }

            $HTTP_SERVER_VARS['QUERY_STRING'] = str_replace("$self=", "", $HTTP_SERVER_VARS['QUERY_STRING']);

            if (empty($HTTP_SERVER_VARS['QUERY_STRING'])) {

                $append = $HTTP_SERVER_VARS['PHP_SELF']."?";

            } else {

                $query_vars = explode("&",$HTTP_SERVER_VARS['QUERY_STRING']);

                $append = $HTTP_SERVER_VARS['PHP_SELF']."?";

                for ($i=0; $i<sizeof($query_vars); $i++) {

                    if (!empty($query_vars[$i])) {

                        $append .= $query_vars[$i]."&";        

                    }

                }

            }

        } else {

            $append = $HTTP_SERVER_VARS['PHP_SELF']."?";

        }

        return $append;

    }



    function poll_process($poll_id='') {

        global $HTTP_GET_VARS, $HTTP_POST_VARS;        

        $register_poll_vars = array("poll_ident","option_id","action");

        for ($i=0;$i<sizeof($register_poll_vars);$i++) {

            if (isset($HTTP_POST_VARS[$register_poll_vars[$i]])) {

                eval("\$$register_poll_vars[$i] = \"".trim($HTTP_POST_VARS[$register_poll_vars[$i]])."\";");      

            } elseif (isset($HTTP_GET_VARS[$register_poll_vars[$i]])) {

                eval("\$$register_poll_vars[$i] = \"".trim($HTTP_GET_VARS[$register_poll_vars[$i]])."\";");      

            } else {

                eval("\$$register_poll_vars[$i] = '';");               

            }

        }

        if ($poll_id=="random") {

            $poll_id = (empty($poll_ident)) ? $this->get_random_poll_id() : $poll_ident;

        } elseif ($poll_id=="newest") {

            $poll_id = $this->get_latest_poll_id();

        }

        if ($this->is_valid_poll_id($poll_id)) {

            $voted = $this->has_voted($poll_id);

            $is_active = $this->is_active_poll_id($poll_id);

            if ($action=="results" && $poll_id==$poll_ident) {

                return $this->view_poll_result($poll_id,0);

            } elseif (!$is_active) {

                return $this->view_poll_result($poll_id,0);

            } elseif ($is_active && $voted) {

                return $this->view_poll_result($poll_id,1);

            } elseif (!$voted && isset($option_id) && $action=="vote" && $poll_id==$poll_ident) {

                $this->update_poll($poll_id,$option_id);

                return $this->view_poll_result($poll_id,0);

            } else {

                return $this->display_poll($poll_id);

            }

        } else {

            $error = "<b>Poll ID <font color=red>$poll_id</font> does not exist.</b>";

            return $error;

        }

    }



}



function sort_poll($a,$b) {

    if ($a == $b) return 0;

    return ($a > $b) ? 1 : -1;

}

    

function rsort_poll($a,$b) {

    if ($a == $b) return 0;

    return ($a > $b) ? -1 : 1;

}



?>