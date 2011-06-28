package com.theamk.ambus;
/**
   Sample message handler. Throws SIODoneException when asked to handle anything.
   Convinient to use for emergency program exit.
*/
public class FatalMsgHandler implements MsgHandler {
	String mMsg;
	/**
	   default constructor
	*/
	public FatalMsgHandler() {
		mMsg = "Exiting due to fatal message: ";
	};

	/**
	   @param msg  message to die with when handling
	*/
	public FatalMsgHandler(String msg) {
		mMsg = msg;
	};

	public boolean handle(Msg message, String[] value) {
		throw new SIODoneException(mMsg + message);
	};
};
