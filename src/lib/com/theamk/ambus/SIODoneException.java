package com.theamk.ambus;

/**
   This exception is thrown by ServIO functions when the server connection goes away or server uses SYS-SIGNAL to kill the process.
   It does not indicate the error.

 */
public class SIODoneException extends SIOException {

	SIODoneException()  { 
		super("server closed connection");
	}

    SIODoneException(String msg) {
        super(msg);
    }
}
