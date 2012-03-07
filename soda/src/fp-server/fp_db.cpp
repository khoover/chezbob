#include "fp_db.h"

// These should be in a config file somewhere. Probably.
const char* SQLITE_DB = "fingerprints.db";

DB::DB() {
  db = NULL;

  sqlite3_open(SQLITE_DB, &db);
}

DB::~DB() {
  sqlite3_close(db);
}

bool DB::SaveUser(User* u) {
  int ret;

  sqlite3_statement* statement = NULL;

  if( SQLITE_OK !=  sqlite3_prepare(db,
      "insert into fingerprints VALUES(?,?);",
      -1,
      &statement,
      0)) {
    printf("Failed to prepare statement");
    return;
  }


  return false;
}

std::vector<User*> DB::GetUsers() {
  std::vector<User*> v;
  return v;
}

