<?php
/**
 * ----------------------------------------------
 * Advanced Poll 2.0.2 (PHP)
 * Copyright (c)2001 Chi Kien Uong
 * URL: http://www.proxy2.de
 * ----------------------------------------------
 */

class plist extends pollcomment {

    var $poll_list_html = array();
    var $plist_data = array();
    var $list_index = '';
    var $list_page_html = '';
    var $poll_records = '';
    var $plist_id_arr = array();

    function plist() {
        global $HTTP_GET_VARS, $HTTP_POST_VARS;
        $this->list_index = (isset($HTTP_GET_VARS['l_page'])) ? trim($HTTP_GET_VARS['l_page']) : 0;
        $this->list_index = (isset($HTTP_POST_VARS['l_page'])) ? trim($HTTP_POST_VARS['l_page']) : $this->list_index;
        if (empty($this->list_index) || $this->list_index<0) {
            $this->list_index = 0;
        }
        $this->pollcomment();
    }

    function get_poll_list_data() {
        if (sizeof($this->plist_data)<1) {
            $record = ($this->poll_records>0) ? $this->poll_records : $this->pollvars['polls_pp'];
            $this->plist_id_arr = $this->get_poll_list();
            if (sizeof($this->plist_id_arr)>0) {
                for ($i=0; $i<sizeof($this->plist_id_arr); $i++) {
                    $line = file("$this->include_path/polldata/".$this->plist_id_arr[$i]);
                    if (ereg(".*\\|[0-9]+\\|[0-9]+\\|[0-9]{1}\\|[0-9]{1}\\|[0-9]{1}\\|[0-9]{1}",$line[0])) {
                        list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);
                        $comments = chop($comments);
                        $poll_id_arr[] = $this->plist_id_arr[$i];
                        $question_arr[] = $question;
                        $timestamp_arr[] = $timestamp;
                        $exp_time_arr[] = $exp_time;
                        $expire_arr[] = $expire;
                        $comments_arr[] = $comments;
                    }
                }                                
                $this->plist_data['poll_id'] = $poll_id_arr;
                $this->plist_data['question'] = $question_arr;
                $this->plist_data['timestamp'] = $timestamp_arr;
                $this->plist_data['exp_time'] = $exp_time_arr;
                $this->plist_data['expire'] = $expire_arr;
                $this->plist_data['comments'] = $comments_arr;
            } else {
                $this->plist_data = array();
            }
        }
        return $this->plist_data;
    }

    function view_poll_list() {
        global $HTTP_SERVER_VARS;
        $PHP_SELF = $HTTP_SERVER_VARS['PHP_SELF'];
        if (!isset($this->poll_list_html[$this->comment_tpl])) {            
            $filename = "$this->include_path/templates/$this->comment_tpl.html";
            $fd = fopen ($filename, "r");
            $template = fread ($fd, filesize ($filename));
            fclose ($fd);                  
            $template = ereg_replace("\"", "\\\"", $template);
            $list_html = '';            
            if (sizeof($this->plist_data<1)) {
                $this->get_poll_list_data();
            }
            if (sizeof($this->plist_id_arr)<1) {
                $this->plist_id_arr = $this->get_poll_list();
            }
            $record = ($this->poll_records>0) ? $this->poll_records : $this->pollvars['polls_pp'];
            $total_polls = sizeof($this->plist_id_arr);
            $pages = (int) ($total_polls/$record);
            if (($this->list_index>$pages*$record) && $pages>0) {
                $this->list_index = $total_polls-$record;
            }
            if (sizeof($this->plist_data>0)) {
                for ($i=$this->list_index;$i<sizeof($this->plist_data['poll_id']);$i++) {
                    $data['timestamp'] = date($this->date_format,$this->plist_data['timestamp'][$i]+$this->pollvars['time_offset']*3600);
                    $data['exp_time'] = date($this->date_format,$this->plist_data['exp_time'][$i]+$this->pollvars['time_offset']*3600);                    
                    $data['poll_id'] = $this->plist_data['poll_id'][$i];
                    $data['question'] = htmlspecialchars($this->plist_data['question'][$i]);
                    $data['comments'] = $this->plist_data['comments'][$i];
                    $data['expire'] = $this->plist_data['expire'][$i];
                    eval("\$list_html .= \"$template\";");
                    if ($i==($this->list_index+$record-1)) {
                        break;
                    }
                }
                $this->poll_list_html[$this->comment_tpl] = $list_html;
            } else {
                $this->poll_list_html[$this->comment_tpl] = '';
            }
        }
        return $this->poll_list_html[$this->comment_tpl];
    }

    function set_polls_per_page($records) {
        if (is_integer($records) && $records>0) {
            $this->poll_records = $records;
            return true;
        } else {
            return false;
        }
    }

    function get_total_polls() {
        if (sizeof($this->plist_id_arr)<1) {
            $this->plist_id_arr = $this->get_poll_list();
        }
        return sizeof($this->plist_id_arr);    
    }

    function get_list_pages($max_pages=10, $separate=" | ") {
        if (empty($this->list_page_html)) {
            $record = ($this->poll_records>0) ? $this->poll_records : $this->pollvars['polls_pp'];
            $total_polls = $this->get_total_polls();
            if ($total_polls>0) {
                $this->list_page_html = $this->get_pages($total_polls, $this->list_index, $record, "l_page", $max_pages, $separate);
            } else {
                $this->list_page_html = '';
            }
        }
        return $this->list_page_html;        
    }

}

?>