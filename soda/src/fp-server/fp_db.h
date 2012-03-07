#ifndef FP_DB_H
#define FP_DB_H

#include <sqlite3.h>
#include <vector>

// create table fingerprints(username varchar, fingerprint varchar);

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
