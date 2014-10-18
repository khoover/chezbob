#! /usr/bin/env bash

function usage {
  echo "Usage: $0 <postgress sql dump> <output sqlite db>"
  exit -1
}

if [[ $# -ne 2 ]] ;then
  usage
fi

INPUT=$1
OUTPUT=$2

echo "Before running the script make sure you've removed manually"\
" all instances of the '::' operator and of 'ALTER TABLE... ADD CONSTRAINT"

cat $INPUT | awk '
BEGIN { skip_till_semi=0; print "BEGIN;" }
{ 
  if ($0~/^CREATE SEQUENCE.*/) {
    skip_till_semi=1;
  }
  if ($0~/^ALTER SEQUENCE.*/) {
    skip_till_semi=1;
  }
  skip=skip_till_semi;
  if ($0~/.*;.*/) {
    skip_till_semi=0;
  }
  if ($0~/^SET.*/) {
    skip=1;
  }
  if ($0~/^SELECT pg_catalog.setval.*/) {
    skip=1;
  }
  if ($0~/ALTER TABLE.*OWNER.*/) {
    skip=1;
  }
  if ($0~/^GRANT/) {
    skip=1;
  }
  if ($0~/^REVOKE/) {
    skip=1;
  }
  if ($0~/.*ALTER COLUMN.*/) {
    skip=1;
  }
  if (skip==0) {
    gsub("false", "0");
    gsub("true", "1");
    gsub("now\(\)", "CURRENT_TIMESTAMP");
    gsub("timestamp with time zone", "DATETIME");
    gsub("timestamp without time zone", "DATETIME");
    gsub("DEFAULT nextval\([^)]*\)", "AUTO_INCREMENT PRIMARY KEY UNIQUE")
    gsub("ALTER TABLE ONLY", "ALTER TABLE")
    gsub("USING btree", "")
    print ;
  }
}
END { print "END;" }
' > ${OUTPUT}.sql

sqlite3 ${OUTPUT}.sqlite ".read ${OUTPUT}.sql"
