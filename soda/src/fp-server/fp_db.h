#ifndef FP_DB_H
#define FP_DB_H

#include <stdlib.h>
#include <stdio.h>

#include <sqlite3.h>
#include <vector>
#include <libfprint/fprint.h>

// create table fingerprints(username varchar, fingerprint blob);

class User;

class DB {
 public:
   DB();
   ~DB();

  bool SaveUser(User* u);
  std::vector<User*> GetUsers();
 private:
  sqlite3* db;
};

#endif
