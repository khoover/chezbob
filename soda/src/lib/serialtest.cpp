#include <stdio.h>
#include "sercom.h"

int main (int argc, char** argv)
{
	char* port = "/dev/ttyS0";
	SER_HANDLE srh = ser_open(port, SER_M9N1 | SER_LOWLATENCY | SER_B9600);
	if (!srh) {printf("Serial open failed.\n");}

	while (1)
	{	
	int c;
	c = ser_getc(srh, 2000);
	printf("c = %d\n", c);
	}

	return 0;

}
