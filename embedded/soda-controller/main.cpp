
#include "ch.hpp"
#include "hal.h"

#include "string.h"
#include "usbcfg.h"
#include "chprintf.h"

#include <stdarg.h>
#include <string.h>
#include <stdlib.h>
#include <memory>

using namespace chibios_rt;

SerialUSBDriver SDU1;

#define TXDONE_EVENT 2

static uint16_t txbuffer[32];
static uint16_t pendingData[32];

uint8_t calculateChecksum(uint16_t* array, size_t length)
{
    uint8_t sum = 0;

    for (size_t i = 0; i < length; i++)
    {
        sum += array[i];
    }

    return sum;
}

#define MDB_CASHLESS0_ADDRESS 0x10

#define MDB_CASHLESS_RESET 0
#define MDB_CASHLESS_SETUP 1
#define MDB_CASHLESS_SETUP_CONFIGDATA 0
#define MDB_CASHLESS_POLL 2
#define MDB_CASHLESS_VEND 3
#define MDB_CASHLESS_VEND_REQUEST 0
#define MDB_CASHLESS_VEND_CANCEL 1
#define MDB_CASHLESS_VEND_SUCCESS 2
#define MDB_CASHLESS_VEND_FAIL 3
#define MDB_CASHLESS_VEND_COMPLETE 4
#define MDB_CASHLESS_READER 4
#define MDB_CASHLESS_READER_DISABLE 0
#define MDB_CASHLESS_READER_ENABLE 1
#define MDB_CASHLESS_READER_CANCEL 2
#define MDB_CASHLESS_REVALUE 5
#define MDB_CASHLESS_EXPANSION 7
#define MDB_CASHLESS_EXPANSION_REQUESTID 0

#define CASHLESS0_STATE 0
#define VMC_CASHLESS_STATE_RESET    0
#define VMC_CASHLESS_STATE_ENABLED  1
#define VMC_CASHLESS_STATE_VSESSION 2
#define VMC_CASHLESS_STATE_VSESSIONIDLE 3
#define VMC_CASHLESS_STATE_CONFIGURED 4
#define VMC_CASHLESS_STATE_VAPPROVED 5
#define VMC_CASHLESS_STATE_VDENIED 6
#define VMC_CASHLESS_STATE_VSESSIONEND 7
#define VMC_CASHLESS_STATE_DISABLED 8
#define VMC_CASHLESS_STATE_CANCEL 9

#define MDB_CASHLESS_POLLRESPONSE_JUSTRESET 0x0
#define MDB_CASHLESS_POLLRESPONSE_CONFIGDATA 0x1
#define MDB_CASHLESS_POLLRESPONSE_BEGINSESSION 0x3
#define MDB_CASHLESS_POLLRESPONSE_VAPPROVED 0x5
#define MDB_CASHLESS_POLLRESPONSE_VDENIED 0x6
#define MDB_CASHLESS_POLLRESPONSE_ENDSESSION 0x7
#define MDB_CASHLESS_POLLRESPONSE_CANCELLED 0x8

class VMCThread : public BaseStaticThread<8192> {
    protected:
        Semaphore sendSem;
        uint8_t state[2];
        
        char toReceive;
        char pendingCmd;
        char pendingDevice;
        uint16_t pendingSubcommand;
        char pendingDataSize;
        char pendingDataCounter;

        void SynchornousVMCSend(uint16_t* array, size_t length)
        {
            array[length] = calculateChecksum(array, length);
            array[length] |= 0x100;
            
            //take a tx lock
            chSemWait(&this->sendSem);
            uint16_t c;
            do {
                uartStartSend(&UARTD2, length+1, array);
                //wait until the uart send completes.
                chEvtWaitAny((eventmask_t) TXDONE_EVENT);
            //release the tx lock
                 
                c = chIQGetTimeout(&this->inputQueue, TIME_INFINITE) << 8;
                c |= chIQGetTimeout(&this->inputQueue, TIME_INFINITE);
                } while (c == 0xAA); //resend if requested.
            chSemSignal(&this->sendSem);
            
        }

        virtual msg_t main(void)
        {
            setName("VMCThread");
            
            //init required structures.
            chSemInit(&this->sendSem, 1);
            this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_RESET;
            this->pendingDataSize = 0;
            this->pendingDataCounter = 0;
            toReceive = 0;
            
            while (TRUE) {

                uint16_t c;
                c = chIQGetTimeout(&this->inputQueue, TIME_INFINITE) << 8;
                c |= chIQGetTimeout(&this->inputQueue, TIME_INFINITE);
                   //is this a command? if so, get the specifics and start a read op
                if (c & 0x100)
                {
                    this->pendingDevice = c & 0xF8;
                    this->pendingCmd = c & 0x7;
                    this->pendingSubcommand = 0x100; //this indicates we don't have it yet
                    this->pendingDataSize = 0;
                    this->pendingDataCounter = 0;

                    toReceive = 0;

                    switch (pendingDevice)
                    {
                        case 0x8: //coin changer
                            switch (pendingCmd)
                            {
                                case 0x0:
                                case 0x1:
                                case 0x2:
                                case 0x3:
                                case 0x4:
                                case 0x7:
                                    toReceive = 1;
                                    break;
                                case 0x5:
                                    toReceive = 2;
                                    break;
                            }
                        break;
                        case 0x30: //bill validator
                            switch (pendingCmd)
                            {
                                case 0x0:
                                case 0x1:
                                case 0x3:
                                case 0x7:
                                    toReceive = 1;
                                    break;
                                case 0x2:
                                case 0x6:
                                    toReceive = 3;
                                    break;
                                case 0x4:
                                    toReceive = 4;
                                    break;
                                case 0x5:
                                    toReceive = 1;
                                    break;
                            }
                        break;
                        case 0x10: //cashless #1
                        case 0x60: //cashless #2
                            switch (pendingCmd)
                            {
                                case 0x0:
                                case 0x2:
                                    toReceive = 1;
                                    break;
                                case 0x1:
                                case 0x3:
                                case 0x4:
                                case 0x5:
                                case 0x6:
                                case 0x7:
                                    toReceive = 2;
                                    break;
                            }
                        break;
                    }
                }
                else
                {
                    if (toReceive == 0) { //nothing to read.
                    }
                    else
                    {
                    toReceive--;
                    if (pendingDataSize > 0)
                    {
                        if (pendingDataCounter > 31)
                        {
                            chprintf((BaseSequentialStream*)&SDU1, "ER BUFFER OVERFLOW\r\n");
                        }
                        else
                        {
                            pendingData[pendingDataCounter] = c;
                            pendingDataCounter++;
                        }
                    }

                    if (toReceive == 0)
                    {
                    if (this->pendingDevice == MDB_CASHLESS0_ADDRESS)
                    {
                        switch (this->pendingCmd)
                        {
                            case MDB_CASHLESS_RESET:
                                this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_RESET;
                                this->SynchornousVMCSend(txbuffer, 0);
                                break;
                            case MDB_CASHLESS_SETUP:
                                switch (this->pendingSubcommand)
                                {
                                    case MDB_CASHLESS_SETUP_CONFIGDATA:
                                        txbuffer[0] = 0x1;
                                        txbuffer[1] = 0x2;
                                        txbuffer[2] = 0x0;
                                        txbuffer[3] = 0x1;
                                        txbuffer[4] = 0x1;
                                        txbuffer[5] = 0x2;
                                        txbuffer[6] = 0x10;
                                        txbuffer[7] = 0x7;
                                        this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_CONFIGURED;
                                        this->SynchornousVMCSend(txbuffer, 8);
                                        break;
                                    default:
                                        this->SynchornousVMCSend(txbuffer, 0); //ack
                                        break;
                                }
                                break;
                            case MDB_CASHLESS_POLL:
                                switch (this->state[CASHLESS0_STATE])
                                {
                                    case VMC_CASHLESS_STATE_RESET:
                                        txbuffer[0] = MDB_CASHLESS_POLLRESPONSE_JUSTRESET;
                                        this->SynchornousVMCSend(txbuffer, 1);
                                    break;
                                    case VMC_CASHLESS_STATE_CONFIGURED:
                                        txbuffer[0] = MDB_CASHLESS_POLLRESPONSE_CONFIGDATA;
                                        txbuffer[1] = 0x2;
                                        txbuffer[2] = 0x0;
                                        txbuffer[3] = 0x1;
                                        txbuffer[4] = 0x1;
                                        txbuffer[5] = 0x2;
                                        txbuffer[6] = 0x10;
                                        txbuffer[7] = 0x7;
                                        this->SynchornousVMCSend(txbuffer, 8);
                                    break;
                                    case VMC_CASHLESS_STATE_VSESSION:
                                        txbuffer[0] = MDB_CASHLESS_POLLRESPONSE_BEGINSESSION;
                                        txbuffer[1] = 0xFF;
                                        txbuffer[2] = 0xFF;
                                        txbuffer[3] = 0xFF;
                                        txbuffer[4] = 0xFF;
                                        txbuffer[5] = 0xFF;
                                        txbuffer[6] = 0xFF;
                                        txbuffer[7] = 0x01;
                                        txbuffer[8] = 0x01;
                                        txbuffer[9] = 0;
                                        this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_VSESSIONIDLE;
                                        this->SynchornousVMCSend(txbuffer, 10);
                                    break;
                                     case VMC_CASHLESS_STATE_VDENIED:
                                        txbuffer[0] = MDB_CASHLESS_POLLRESPONSE_VDENIED;
                                        this->SynchornousVMCSend(txbuffer, 1);
                                        this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_VSESSION;
                                    break;
                                    case VMC_CASHLESS_STATE_VAPPROVED:
                                        txbuffer[0] = MDB_CASHLESS_POLLRESPONSE_VAPPROVED;
                                        txbuffer[1] = 0xFF;
                                        txbuffer[2] = 0xFF;
                                        this->SynchornousVMCSend(txbuffer, 3);
                                    break;
                                    case VMC_CASHLESS_STATE_VSESSIONEND:
                                        txbuffer[0] = MDB_CASHLESS_POLLRESPONSE_ENDSESSION;
                                        this->SynchornousVMCSend(txbuffer, 1);
                                        this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_VSESSION;
                                    break;
                                    case VMC_CASHLESS_STATE_CANCEL:
                                        txbuffer[0] = MDB_CASHLESS_POLLRESPONSE_CANCELLED;
                                        this->SynchornousVMCSend(txbuffer, 3);
                                    break;
                                    default:
                                        this->SynchornousVMCSend(txbuffer, 0); //ack
                                    break;
                                }
                                break;
                            case MDB_CASHLESS_VEND:
                                    switch (this->pendingSubcommand)
                                    {
                                        case MDB_CASHLESS_VEND_REQUEST:
                                            this->SynchornousVMCSend(txbuffer, 0); //ack
                                            break;
                                        case MDB_CASHLESS_VEND_COMPLETE:
                                            this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_VSESSIONEND;
                                            this->SynchornousVMCSend(txbuffer, 0); //ack
                                            break;
                                        case MDB_CASHLESS_VEND_SUCCESS:
                                            this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_VSESSIONIDLE;
                                            this->SynchornousVMCSend(txbuffer, 0); //ack
                                            break;
                                        default:
                                            this->SynchornousVMCSend(txbuffer, 0); //ack
                                    }
                                break;
                            case MDB_CASHLESS_READER:
                                    switch (this->pendingSubcommand)
                                    {
                                        case MDB_CASHLESS_READER_ENABLE:
                                            this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_VSESSION; //jump to a session.
                                            this->SynchornousVMCSend(txbuffer, 0); //ack
                                            break;
                                        case MDB_CASHLESS_READER_DISABLE:
                                            this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_DISABLED;
                                            this->SynchornousVMCSend(txbuffer, 0); //ack
                                            break;
                                        case MDB_CASHLESS_READER_CANCEL:
                                            this->state[CASHLESS0_STATE] = VMC_CASHLESS_STATE_CANCEL;
                                            this->SynchornousVMCSend(txbuffer, 0); //ack
                                            break;
                                        default:
                                            this->SynchornousVMCSend(txbuffer, 0); //ack
                                    }
                                break;
                            case MDB_CASHLESS_EXPANSION:
                                    switch (this->pendingSubcommand)
                                    {
                                        case MDB_CASHLESS_EXPANSION_REQUESTID:
                                            memset(txbuffer, 0, 32);
                                            txbuffer[0] = 0x9;
                                            txbuffer[28] = 0x03;
                                            txbuffer[29] = 0;
                                            this->SynchornousVMCSend(txbuffer, 30);
                                            break;
                                        default:
                                            this->SynchornousVMCSend(txbuffer, 0); //ack
                                            break;
                                    }
                                break;
                            default:
                                this->SynchornousVMCSend(txbuffer, 0); //ack
                                break;
                        }
                    }

                if (SDU1.config->usbp->state == USB_ACTIVE)
                {
                    if (pendingSubcommand >= 0x100)
                    {
                        chprintf((BaseSequentialStream*)&SDU1, "S2 %02x %02x\r\n", pendingDevice, pendingCmd);
                    }
                    else
                    {
                        if (pendingDataSize == 0)
                        {
                            chprintf((BaseSequentialStream*)&SDU1, "S2 %02x %02x %02x\r\n", pendingDevice, pendingCmd, pendingSubcommand);
                        }
                        else
                        {
                            chprintf((BaseSequentialStream*)&SDU1, "S2 %02x %02x %02x", pendingDevice, pendingCmd, pendingSubcommand);
                            for (int i =0 ; i < pendingDataSize; i++)
                            {
                                chprintf((BaseSequentialStream*)&SDU1, " %02x", pendingData[i]);
                            }
                            chprintf((BaseSequentialStream*) &SDU1, "\r\n");
                        }
                    }
                }
                    }
                    else if (toReceive == 1 && pendingSubcommand == 0x100)
                    {
                        pendingSubcommand = c;

                        //evaluate subcommand size here
                        switch (pendingDevice)
                        {
                            case 0x10:
                            case 0x60:
                                switch (pendingCmd)
                                {
                                    case 0x0:
                                    break;
                                    case 0x1:
                                        switch(pendingSubcommand)
                                        {
                                            case 0x0:
                                            pendingDataSize = (toReceive = 5) - 1;
                                            break;
                                            case 0x1:
                                            pendingDataSize = (toReceive = 5) - 1;
                                            break;
                                        }
                                    break;
                                    case 0x3:
                                        switch(pendingSubcommand)
                                        {
                                            case 0x0: //vendrequest
                                                pendingDataSize = (toReceive = 5) - 1;
                                            break;
                                            case 0x2: //success
                                                pendingDataSize = (toReceive = 3) - 1;
                                            break;
                                            case 0x5: //cash sale
                                                pendingDataSize = (toReceive = 5) - 1;
                                            break;
                                        }
                                    case 0x4:
                                        switch(pendingSubcommand)
                                        {
                                            case 0x0: //disabled
                                            break;
                                            case 0x1: //enabled
                                            break;
                                            case 0x2: //cancel
                                            break;
                                        }
                                    break;
                                    case 0x7:
                                        switch(pendingSubcommand)
                                        {
                                            case 0x0:
                                                pendingDataSize = (toReceive = 30) - 1;
                                            break;
                                        }
                                    break;
                                }
                                break;
                        }
                    }
                    }
                }

            }
        }
    public:
        uint8_t queueBuffer[8];
        INPUTQUEUE_DECL(inputQueue, &queueBuffer, 8, NULL, NULL);
        
        uint8_t getState(uint8_t device)
        {
            return this->state[CASHLESS0_STATE];
        }
        
        void setState(uint8_t device, uint8_t state)
        {
            this->state[CASHLESS0_STATE] = state;
        }
        VMCThread(void) : BaseStaticThread<8192> () {

        }
};

static VMCThread vmcThread;

static void txend1 (UARTDriver *uartp)
{

}

static void txend2 (UARTDriver *uartp)
{
    chSysLockFromIsr();
        vmcThread.signalEventsI((eventmask_t) TXDONE_EVENT);
    chSysUnlockFromIsr();
}

static void rxerr(UARTDriver *uartp, uartflags_t e)
{
}

static void rxchar(UARTDriver *uartp, uint16_t c)
{
    chSysLockFromIsr();
        //MSB first into the input queue.
        chIQPutI(&vmcThread.inputQueue, (c >> 8) & 0xFF);
        chIQPutI(&vmcThread.inputQueue, c & 0xFF);
    chSysUnlockFromIsr();

}

static void rxend(UARTDriver *uartp)
{
}

static UARTConfig uart_cfg_2 = {
  txend1,
  txend2,
  rxend,
  rxchar,
  rxerr,
  9600,
  USART_CR1_M, //9 data bits
  0,
  0
};


uint16_t testbuffer[4];
class MDBThread : public BaseStaticThread<8192> {

protected:
  virtual msg_t main(void) {

    setName("MDBThread");

while (true)
{

    chEvtWaitAny((eventmask_t) TXDONE_EVENT);
    testbuffer[0] = 0x108;
    testbuffer[1] = 0x008;
    uartStartSend(&UARTD3, 2, testbuffer);

    uint16_t c;
    c = chIQGetTimeout(&this->inputQueue, TIME_INFINITE) << 8;
    c |= chIQGetTimeout(&this->inputQueue, TIME_INFINITE);
    
    chprintf((BaseSequentialStream*)&SDU1, "S3 %02x\r\n", c);
}

}
public:
    uint8_t queueBuffer[8];
    INPUTQUEUE_DECL(inputQueue, &queueBuffer, 8, NULL, NULL);
    MDBThread(void) : BaseStaticThread<8192>() {
      }
};

static MDBThread mdbThread;

static void tx3end1 (UARTDriver *uartp)
{

}

static void tx3end2 (UARTDriver *uartp)
{
     chSysLockFromIsr();
     mdbThread.signalEventsI((eventmask_t) TXDONE_EVENT);
     chSysUnlockFromIsr();

}

static void rx3err(UARTDriver *uartp, uartflags_t e)
{

}

static void rx3char(UARTDriver *uartp, uint16_t c)
{
    chSysLockFromIsr();
        //MSB first into the input queue.
        chIQPutI(&vmcThread.inputQueue, (c >> 8) & 0xFF);
        chIQPutI(&vmcThread.inputQueue, c & 0xFF);
    chSysUnlockFromIsr();
}

static void rx3end(UARTDriver *uartp)
{

}

static UARTConfig uart_cfg_3 = {
  tx3end1,
  tx3end2,
  rx3end,
  rx3char,
  rx3err,
  9600,
  USART_CR1_M, //9 data bits
  0,
  0
};

class ShellThread : public BaseStaticThread<8192> {

protected:
  char inputBuf[16];
  
  void exec(char* cmd, int argc, char** argv)
  {
        //todo - seperate this out into functions
        if (strcmp(cmd, "S2?") == 0)
        {
            //just indicate that the current state is
            chprintf((BaseSequentialStream*)&SDU1, "S2? %02x\r\n", vmcThread.getState(CASHLESS0_STATE));
        }
        else if (strcmp(cmd, "S2S") == 0)
        {
            //sets the current state of the vmc
            uint8_t state = atoi(argv[1]);
            vmcThread.setState(CASHLESS0_STATE, state);
            chprintf((BaseSequentialStream*)&SDU1, "S2S %02x\r\n", state);
        }
  }
  
  unsigned short readline()
  {
    unsigned short bufPointer = 0;
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

        chprintf((BaseSequentialStream*)&SDU1, "ChezBob Vending Machine Shell\r\n");
        
        while (true)
        {
            if (readline())
            {
                //echo the command.
                chprintf((BaseSequentialStream*)&SDU1, "UE %s\r\n", inputBuf);
                
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
    }
public:
    ShellThread(void) : BaseStaticThread<8192>() {
      }
};

static ShellThread shellThread;

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

  sduObjectInit(&SDU1);
  sduStart(&SDU1, &serusbcfg);

  usbDisconnectBus(serusbcfg.usbp);
  chThdSleepMilliseconds(1000);
  usbStart(serusbcfg.usbp, &usbcfg);
  usbConnectBus(serusbcfg.usbp);

  uartStart(&UARTD2, &uart_cfg_2);
  palSetPadMode(GPIOA, 2, PAL_MODE_ALTERNATE(7));
  palSetPadMode(GPIOA, 3, PAL_MODE_ALTERNATE(7));

  uartStart(&UARTD3, &uart_cfg_3);
  palSetPadMode(GPIOD, 8, PAL_MODE_ALTERNATE(7));
  palSetPadMode(GPIOD, 9, PAL_MODE_ALTERNATE(7));

  shellThread.start(NORMALPRIO);
  vmcThread.start(NORMALPRIO);
  mdbThread.start(NORMALPRIO);
  

  while (TRUE)
  {
     chThdSleepMilliseconds (1000);
  }
  
  return 0;
}
