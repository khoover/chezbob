#include <mysql/mysql.h>
#include <pthread.h>
#include <servio.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "fpserv.h"
#include <VFinger.h>


pthread_mutex_t sql_mutex = PTHREAD_ERRORCHECK_MUTEX_INITIALIZER_NP;

#define SQL_LOCK()    pthread_mutex_lock(&sql_mutex)
#define SQL_UNLOCK()    pthread_mutex_unlock(&sql_mutex)

// mysql connection object
MYSQL * db_conn;

void fpdb_init() {
  // init MYSQL database
  db_conn = mysql_init(0);
  char * sql_host = "";
  char * sql_user = 0; 
  char * sql_passwd = 0;
  char * sql_db = 0;
  // todo: read fromtext-based config file?
  if (!sql_user   || !*sql_user)   sql_user   = strdup("fp_serv");
  if (!sql_db     || !*sql_db)     sql_db     = strdup("soda_auth");
  //sio_getvar("sql_conninfo", ":ssss", &sql_host, &sql_user, &sql_passwd, &sql_db);

  if (!sql_passwd || !*sql_passwd) sql_passwd = strdup("dKBo0Snp2dhw7R2ZEWMt");
  if (!mysql_real_connect(db_conn, sql_host, sql_user, sql_passwd, sql_db, 0, NULL, 0)) {
	char * msg =  strdup(mysql_error(db_conn));
	sio_close(14, msg);
	//abort();
	exit(15);
  };
};

void fpdb_close() {
  mysql_close(db_conn);
};


int fpdata_save(unsigned char * featdata, int featsize, int life) {

  SQL_LOCK();

  char * qbuff = (char*)malloc(featsize*2 + 512);
  int g = VFFeatGetG(featdata);

  int qsize = sprintf(qbuff, 
		      "INSERT INTO fp_fingers SET fp_g=%d, rec_expires=NOW() + INTERVAL %d HOUR, rec_added=NOW(), fp_data='", 
		      g, life ? 7*24 : 2);

  qsize += mysql_real_escape_string(db_conn, qbuff + qsize, (char*)featdata, featsize);
  qbuff[qsize++]='\'';
  qbuff[qsize]=0;

  int rv = mysql_real_query(db_conn, qbuff, qsize);
  free(qbuff);

  if (rv < 0) {
    SQL_UNLOCK();
    sio_write(SIO_ERROR, "FP save failed: err='%s', rv=%d", mysql_error(db_conn), rv);
    return 0;
  };
  
  int id = mysql_insert_id(db_conn);;
  sio_write(SIO_DEBUG, "FP save ok, id=%d, len=%d sql_len=%d g=%d", id, featsize, qsize, g);

  SQL_UNLOCK();

  return  id;
};

int  fpdata_match(unsigned char * featdata, int featsize, 
				  std::string & uid, std::string & finger, int & rel) {

  SQL_LOCK();
  int g = VFFeatGetG(featdata);

  char bf[256]; 

  int rv = sprintf(bf, "SELECT fp_data, fp_id, rec_uid, rec_finger FROM fp_fingers "
				   "WHERE m_ok=1 ORDER BY ABS(fp_g-%d), m_count, m_last_time", g);
  rv = mysql_real_query(db_conn, bf, rv);
  
  if (rv < 0) {
    SQL_UNLOCK();
	sio_write(SIO_ERROR, "FP record select failed: error %s (for %s)", mysql_error(db_conn), bf);
	return 0;
  };

  MYSQL_RES * res = mysql_use_result(db_conn);
  if (!res) {
    SQL_UNLOCK();
	sio_write(SIO_ERROR, "FP record select failed at use-result: error %s (for %s)", mysql_error(db_conn), bf);
	return 0;
  };

  VFMatchDetails md;
  md.Size = sizeof(VFMatchDetails);
  
  VFSetParameter(VFP_MATCHING_THRESHOLD, thresh_match, vfcont); 
  VFIdentifyStart (featdata, vfcont);

  char ** row = 0;
  int best = 0;
  while ((row = mysql_fetch_row(res)) != 0) {
	//unsigned long * lens = mysql_fetch_lengths(res);
	int64 t = time64();
	rv = VFIdentifyNext ((unsigned char*)row[0], &md, vfcont);
	t = time64() - t;
	// keep best result...
	if ( (rv==VFE_OK) || (best < md.Similarity )) {
	  	uid = std::string(row[2]);
	  	finger = std::string(row[3]);
		rel = md.Similarity;
		best = rel;
	};

	if (rv == VFE_FAILED) {     // nomatch
	  //sio_write(SIO_DEBUG, "FP no-match: fpid=%s uid=%s fng=%s, simularity: %d, time %lldu", row[1], row[2], row[3], md.Similarity, t);
	} else if (rv == VFE_OK) {  // match
	  break;
	} else {	  // error
	  sio_write(SIO_ERROR, "FP match failed: %d (fpid=%s uid=%s fng=%s), time=%lldu", rv, row[1], row[2], row[3], t);
	  row = 0;
	  break;
	};
  };
  VFIdentifyEnd(vfcont);
  int fpid = 0;
  if (row) {
	fpid = atoi(row[1]);
  };
  mysql_free_result(res);

  if (fpid) {
	sprintf(bf, "UPDATE fp_fingers SET m_count=m_count+1, m_last_time=NOW(), m_last_sim=%d, m_last_g=%d WHERE fp_id=%d",
			md.Similarity, g, fpid);
	rv = mysql_query(db_conn, bf);

	// we had a match
	sio_write(SIO_DEBUG, "FP match: with fpid=%d uid=%s fng=%s, similarity=%d, sql=%d", fpid, uid.c_str(), finger.c_str(), md.Similarity, rv);
  };
  SQL_UNLOCK();
  return fpid;
};

// store UID in fp's entry, and mark it persistend and matchable.
// input:  fpid,  uid
// output: -1 for error, >0 for success
int  fpdata_persists(int fpid, const std::string uid, const std::string finger) {
  char buff[1024];
  SQL_LOCK();
  strcpy(buff, "UPDATE fp_fingers SET rec_expires=NULL, m_ok=1, rec_uid='");
  mysql_real_escape_string(db_conn, strchr(buff, 0), uid.c_str(), uid.length());
  strcat(buff, "', rec_finger='");
  mysql_real_escape_string(db_conn, strchr(buff, 0), finger.c_str(), finger.length());
  sprintf(strchr(buff, 0), "' WHERE fp_id=%d", fpid);
  int rv = mysql_query(db_conn, buff);
  SQL_UNLOCK();
  if (rv < 0) {
	sio_write(SIO_ERROR, "FP PERSISTS failed: error %s (for %s)", mysql_error(db_conn), buff);
	return -1;
  };
  return 1;
};


// try to generalize one or more fingerpints
// input: array of ints, 0-terminated
// output: fpid of result, if any
// RV:   >0  - match went fine, this is the similarity 
//        0  - values did not match
//       -1  - mysql error
//       -2  - some input was not found
//       -3  - other error
int  fpdata_generalize(int * fpid_in, std::string& exinfo) {
  char buff[1024];

  sprintf(buff, "SELECT fp_data FROM fp_fingers WHERE fp_id IN (");
  char * log_val = strchr(buff, '('); 
  int cnt = 0;
  while ((cnt<10) && (fpid_in[cnt])) { // max 10 features...
	sprintf(strchr(buff, 0), "%c %d", (cnt==0)?' ':',', fpid_in[cnt]);
	cnt++;
  };
  strcat(buff, ")");

  if (cnt < 2) {
	sio_write(SIO_ERROR, "FP generalize called with ouly %d features %s", cnt, log_val);
	return -3;
  };

  SQL_LOCK();
  
  int rv = mysql_query(db_conn, buff);  
  if (rv < 0) {
	sio_write(SIO_ERROR, "FP generalize select failed: error %s (for %s)", mysql_error(db_conn), buff);
	SQL_UNLOCK();

	return -1;
  };
  MYSQL_RES * msres = mysql_store_result(db_conn);
  int actcnt = (msres==0)?-1: (int)mysql_num_rows(msres);
  if (actcnt != cnt) {
    SQL_UNLOCK();
	sio_write(SIO_ERROR, "FP generalize select did not find everything: got %d instead of %d recs, error %s, stmt '%s", 
			  actcnt, cnt, mysql_error(db_conn), log_val);
	return -2;
  };
  
  unsigned char ** feat_in = (unsigned char**)malloc(sizeof(char*)*cnt);
  for (int i=0; i<cnt; i++) {
	char** res = mysql_fetch_row(msres);
	unsigned long * reslen = mysql_fetch_lengths(msres);
	if ((reslen[0] <= 1) || (res[0] == 0)) {
	  sio_write(SIO_ERROR, "ERROR! mysql_fetch_row failed (len=%d for i=%d/%d) %s", reslen[0], i, cnt, log_val);
	  SQL_UNLOCK();
	  return -1;
	};
	feat_in[i] = (unsigned char*)malloc(reslen[0]);
	memcpy(feat_in[i], res[0], reslen[0]);
  };
  mysql_free_result(msres);
  SQL_UNLOCK();

  unsigned char nfeat[VF_MAX_FEATURES_SIZE];
  DWORD fsize = sizeof(nfeat);
  
  rv = VFGeneralize(cnt, feat_in, nfeat, &fsize, vfcont);

  for (int i=0; i<cnt; i++) free(feat_in[i]);
  free(feat_in);

  if (rv == VFE_FAILED) {     // nomatch
	sio_write(SIO_DEBUG, "FP generalize no-match: %s", log_val);
	return 0;
  } else if (rv >= 0) {  // match
	int id = fpdata_save(nfeat, fsize, 0);;
	sio_write(SIO_DEBUG, "FP generalize success: rv=%d, id=%d, %s", rv, id, log_val);
	return id;
  } else {	  // error
	sio_write(SIO_ERROR, "FP generalize failed: %d, %s", rv, log_val);
	return -3;
  };
};


int  fpdata_db_cleanup() {
  SQL_LOCK();
  char buff[1000] = "DELETE FROM fp_fingers WHERE rec_expires>0 AND rec_expires<NOW()";
  int rv = mysql_query(db_conn, buff);  
  if (rv < 0) {
    SQL_UNLOCK();
    sio_write(SIO_ERROR, "FP cleanup failed: error %s (for %s)", mysql_error(db_conn), buff);
    return -1;
  };
  int afr = (int)mysql_affected_rows(db_conn);
  SQL_UNLOCK();
  if (afr == 0)
	return 0;
  sio_write(SIO_LOG, "FP database cleanup: %d rows deleted", afr);
  return 1;
};

int fpdata_unpersist(int fpid) {
  char buff[1000];
  SQL_LOCK();
  sprintf(buff, "UPDATE fp_fingers SET rec_expires=NOW() + INTERVAL 10 HOURS, m_ok=0 WHERRE fpid='%d'", fpid);
  int rv = mysql_query(db_conn, buff);  
  if (rv < 0) {
    SQL_UNLOCK();
    sio_write(SIO_ERROR, "FP unpersist failed: error %s (for %s)", mysql_error(db_conn), buff);
    return -1;
  };
  int afr = (int)mysql_affected_rows(db_conn);
  SQL_UNLOCK();
  if (afr == 0)
	return 0;
  sio_write(SIO_LOG, "FP unpersists: %d rows unperitssed with id=%d", afr, fpid);
  return 1;
};

int fpdata_list(const char* queryid, const char * mode, const char * arg1, const char* arg2) {

  SQL_LOCK();

  char buff[8192];
  sprintf(buff, "SELECT fp_id, rec_uid, rec_finger, 0, CONCAT(IF(!UNIX_TIMESTAMP(rec_expires), 'p', ''), IF(m_ok, 'm', '')), "
		  "  fp_g, length(fp_data), UNIX_TIMESTAMP(rec_added), m_count, UNIX_TIMESTAMP(m_last_time), m_last_sim "
		  "  FROM fp_fingers ");
  if (strcmp(mode, "user")==0) {
	// TODO: FIX (normal quoting)
	sprintf(strchr(buff, 0), "WHERE m_ok=1 AND rec_uid='%s'", arg1);
  } else if (strcmp(mode, "persists")==0) {
	strcat(buff, "WHERE m_ok=1");
  } else if (strcmp(mode, "fpid")==0) {
	// TODO: FIX (normal quoting)
	sprintf(strchr(buff, 0), "WHERE fp_id='%s'", arg1);
  } else if (strcmp(mode, "temp")==0) {
	strcat(buff, "WHERE m_ok=0");
  } else if (strcmp(mode, "all")==0) {
	strcat(buff, "");
  } else {
	sio_write(SIO_WARN, "Invalid mode to fpdata_list: %s", arg1);
	buff[0] = 0;
  };

  MYSQL_RES *  msres = 0;
  if (*buff) {
	int rv = mysql_query(db_conn, buff);  
	if (rv < 0) {
	  sio_write(SIO_ERROR, "FPdata_list failed: error %s (for %s)", mysql_error(db_conn), buff);
	} else {
	  msres = mysql_store_result(db_conn);
	};
  };
  
  while (msres!=NULL) {
	char** res = mysql_fetch_row(msres);
	if (!res) break;
	int bflen = sizeof(buff);
	int count = mysql_num_fields(msres);
	buff[0] = 0;
	for (int i=0; i<count; i++) {
	  if ((strlen(buff)+256+1) >= sizeof(buff)) break;
	  if (i!=0) 	  strcat(buff, "\t");
	  strcat(buff, res[i]?res[i]:"");
	};
	sio_write(SIO_DATA, "FP-LIST-DATA\t%s\t%s", queryid, buff);
  };
  if (msres)
	mysql_free_result(msres);

  sio_write(SIO_DATA, "FP-LIST-DATA\t%s", queryid);
  SQL_UNLOCK();

};
