#include <string.h>
#include <stdio.h>
#include <signal.h>
#include <unistd.h>

#define SSH_CMD "/usr/local/bin/ssh"
#define PROMPT "login to gradlab as: "
#define REMOTE_IP "132.239.55.107"

int
main(int argc, char **argv, char **envp)
{
  char *args[5];
  char u[9];

  /*
  ** trap int signal
  */
  signal(SIGINT, SIG_IGN);

  args[0] = SSH_CMD;
  args[1] = REMOTE_IP;
  args[2] = "-l";
  do {
    printf(PROMPT);
    while (fgets(u, 9, stdin) == NULL) {
      *u = '\0';
    }
    if (u[strlen(u)-1] == '\n') {
      u[strlen(u)-1] = '\0';
    }

  } while (strlen(u) == 0 || *u < 'a' || *u > 'z');
  args[3] = u;
  args[4] = NULL;

  if (execve(SSH_CMD, args, envp) == -1) {
    perror("execve");
  }

  return (0);
}
