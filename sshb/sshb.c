#include <stdio.h>
#include <signal.h>

#define PROMPT "login to beowulf as: "
#define BEOWULF_IP "132.239.55.100"

void
main(int argc, char **argv, char **envp)
{
  char *args[3];
  char u[9];

  /*
  ** trap int signal
  */
  signal(SIGINT, SIG_IGN);

  args[0] = BEOWULF_IP;
  args[1] = "-l";
  do {
    printf(PROMPT);
    while (fgets(u, 9, stdin) == NULL) {
      *u = '\0';
    }
    if (u[strlen(u)-1] == '\n') {
      u[strlen(u)-1] = '\0';
    }

  } while (strlen(u) == 0 || *u < 'a' || *u > 'z');
  args[2] = u;

  execve("/usr/local/bin/ssh", args, envp);
}
