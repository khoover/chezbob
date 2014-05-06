
#include "ch.hpp"
#include "hal.h"

#include "string.h"
#include "usbcfg.h"
#include "chprintf.h"

#include "iwdg.h"

#include <stdarg.h>
#include <string.h>
#include <stdlib.h>
#include <memory>

using namespace chibios_rt;

SerialUSBDriver SDU1;

static Semaphore printSem;

int channelno = 0;

class VMCThread : public BaseStaticThread<8192> {
    protected:
        virtual msg_t main(void)
        {
            setName("VMCThread");
     
            return 0;
        }
    public:
        VMCThread(void) : BaseStaticThread<8192> () {

        }
};

class FlipThread : public BaseStaticThread<4096> {
    protected:
        virtual msg_t main(void)
        {
            setName("FlipThread");
			//Flip the high channel every 200ms when nothing is active.
			
			//PE4 is channel 0, PE5 is channel 1
			
			//PE6 = A
			//PE7 = B
			//PE8 = C
			//PE9 = D
			//PE10 = E
			
			int selected = 0;
			while (TRUE)
			{
				switch (channelno)
				{
					case 0:
						channelno = 1;
						palClearPad(GPIOE, 5);
						palSetPad(GPIOE, 4);
						chThdSleepMilliseconds(100); //wait for things to stabilize
						
						if (palReadPad(GPIOE, 6))
						{
							selected = 1;
						}
						else if (palReadPad(GPIOE, 7))
						{
							selected = 2;
						}
						else if (palReadPad(GPIOE, 8))
						{
							selected = 3;
						}
						else if (palReadPad(GPIOE, 9))
						{
							selected = 4;
						}
						else if (palReadPad(GPIOE, 10))
						{
							selected = 5;
						}
						break;
					case 1:
						channelno = 0;
						palClearPad(GPIOE, 4);
						palSetPad(GPIOE, 5);
						chThdSleepMilliseconds(100); //wait for things to stabilize
						
						if (palReadPad(GPIOE, 6))
						{
							selected = 6;
						}
						else if (palReadPad(GPIOE, 7))
						{
							selected = 7;
						}
						else if (palReadPad(GPIOE, 8))
						{
							selected = 8;
						}
						else if (palReadPad(GPIOE, 9))
						{
							selected = 9;
						}
						else if (palReadPad(GPIOE, 10))
						{
							selected = 10;
						}
						break;
				}
				
				
				if (selected)
				{
					chprintf((BaseSequentialStream*)&SDU1, "B%02x\r\n", selected);
					
					palClearPad(GPIOE, 4);
					palClearPad(GPIOE, 5);
					
					chThdSleepMilliseconds (1000); //debounce for one second
					 
					 selected = 0;
				}
				
				chThdSleepMilliseconds(200);
			}
            return 0;
        }
    public:
        FlipThread(void) : BaseStaticThread<4096> () {

        }
};

static VMCThread vmcThread;

class ShellThread : public BaseStaticThread<8192> {

protected:
  char inputBuf[16];
  
  void exec(char* cmd, int argc, char** argv)
  {
		if (strcmp(cmd, "V") == 0)
		{
			int vendopt = 0;
			if(argc > 1)
			{
				vendopt= strtol(argv[1], NULL, 16);
			}
			
			//PE11 = 1
			//PE12 = 2
			//PE13 = 4
			
			switch(vendopt)
			{
				case 1:
					//palSetPad(GPIOE, 11);
					break;
				case 2:
					//turn on outputs and go forward
					palClearPad(GPIOE, 12);
					//only enable coke for now
					palSetPad(GPIOE, 11);
					break;
				case 4:
					palSetPad(GPIOE, 13);
					break;
			}
			
			//wait for 3 seconds
			chThdSleepMilliseconds (2500);
			
			//reverse
			palSetPad(GPIOE, 12);
			chThdSleepMilliseconds (1500);

			palClearPad(GPIOE, 11);
			palClearPad(GPIOE, 12);
			palClearPad(GPIOE, 13);
			//check if the vend sensor went off.
			
			
			chprintf((BaseSequentialStream*)&SDU1, "F%02x\r\n", vendopt);
		}
  }
  
  unsigned short readline()
  {
    unsigned short bufPointer = 0;
    memset(inputBuf,0,16);
    do
    {
        char in = chSequentialStreamGet((BaseSequentialStream*)&SDU1);
        
        switch (in)
        {
            case 0: //ignore NULL
                break;
            case '\r':
            case '\n':
                inputBuf[bufPointer] = 0; // NULL terminated
                return bufPointer;
            case 0x8:
            case 0x7F:
                if (bufPointer != 0) {
                    inputBuf[bufPointer - 1] = 0;
                    bufPointer--;
                }
                break;
            default:
                if (bufPointer < 14)
                {
                    inputBuf[bufPointer] = in;
                    bufPointer++;
                }
        } 
        
    } while (TRUE);
  }
  
  virtual msg_t main(void) {
        setName("Shell");

        chSemWait(&printSem);
        chprintf((BaseSequentialStream*)&SDU1, "ChezBob Vending Machine Shell\r\n");
        chSemSignal(&printSem);
        while (true)
        {
            if (readline())
            {
                //echo the command.
                //chSemWait(&printSem);
                chprintf((BaseSequentialStream*)&SDU1, "UE %s\r\n", inputBuf);
               //chSemSignal(&printSem);
                
                unsigned short argc = 0;
                char* argv[9];
                char* pch = (char*) inputBuf;
                char* end = (char*) inputBuf + 16;
                
                while (pch < end)
                {
                    argv[argc] = pch;
                    argc++;
                    
                    while (pch < end)
                    {
                        pch++;
                        if (*pch == 0x20)
                        {
                            *pch = 0;
                            pch++;
                            break;
                        }
                    }
                }
                
                if (argc)
                {
                    exec(argv[0], argc, argv);
                }
            }
        }
        
        return 0;
    }
public:
    ShellThread(void) : BaseStaticThread<8192>() {
        memset(inputBuf,0,16);
      }
};

static ShellThread shellThread;
static FlipThread flipThread;
/*
 * Application entry point.
 */
int main(void) {

  /*
   * System initializations.
   * - HAL initialization, this also initializes the configured device drivers
   *   and performs the board-specific initializations.
   * - Kernel initialization, the main() function becomes a thread and the
   *   RTOS is active.
   */
  halInit();
  System::init();
  //iwdgInit();
  //iwdgStart(&IWDGD, &iwdg_cfg);
  sduObjectInit(&SDU1);
  sduStart(&SDU1, &serusbcfg);
  chSemInit(&printSem, 1);
   
  usbDisconnectBus(serusbcfg.usbp);
  chThdSleepMilliseconds(1000);
  usbStart(serusbcfg.usbp, &usbcfg);
  usbConnectBus(serusbcfg.usbp);

  palSetPadMode(GPIOE, 4, PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOE, 5, PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOE, 6, PAL_MODE_INPUT);
  palSetPadMode(GPIOE, 7, PAL_MODE_INPUT);
  palSetPadMode(GPIOE, 8, PAL_MODE_INPUT);
  palSetPadMode(GPIOE, 9, PAL_MODE_INPUT);
  palSetPadMode(GPIOE, 10, PAL_MODE_INPUT);
  
  //ensure that outputs are off before and after
  
  			palClearPad(GPIOE, 11);
			palClearPad(GPIOE, 12);
			palClearPad(GPIOE, 13);
			
  palSetPadMode(GPIOE, 11, PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOE, 12, PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOE, 13, PAL_MODE_OUTPUT_PUSHPULL);
  
  			palClearPad(GPIOE, 11);
			palClearPad(GPIOE, 12);
			palClearPad(GPIOE, 13);
  //uartStart(&UARTD3, &uart_cfg_3);
  //palSetPadMode(GPIOD, 8, PAL_MODE_ALTERNATE(7));
  //palSetPadMode(GPIOD, 9, PAL_MODE_ALTERNATE(7));

  shellThread.start(NORMALPRIO);
  flipThread.start(NORMALPRIO);
 // mdbThread.start(NORMALPRIO);
  

  while (TRUE)
  {
     chThdSleepMilliseconds (1000);
  }
  
  return 0;
}
