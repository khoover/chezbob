package com.theamk.ambus;

/**
   The RuntimeException that is thrown when something is wrong with the server.

   The program is expected to exit as soon as possible after receiving this exception.
 */
public class SIOException extends RuntimeException {

	SIOException() { }

    SIOException(String msg) {
        super(msg);
    }

    SIOException(Exception x) {
        super(x);
    }
}
