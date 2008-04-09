package com.theamk.ambus;
/**	
   Message handler interface.
   See ServIO.watchMessage for expanation
*/
public interface MsgHandler {
	/**
	   Handler for the message or variable change.
	   @param message   the message that caused the invocation
	   @param value     the non-prefix part (i.e. the tokens after the match prefix)
	   @return true to claim the message and stop further processing, false if it should be passed to next handlers/user.
	 */
	public boolean handle(Msg message, String[] value);
};
