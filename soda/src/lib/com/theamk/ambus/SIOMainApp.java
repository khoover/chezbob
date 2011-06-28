
package com.theamk.ambus;


/**
   This is a special class for ambus-based apps. Application's main class should inherit from this class, implementing the required methods.
  <p>
  Then, the main method should contain only one line:
 <pre>
    public static void main(String args[]) {
		ServIORunner.runMainClass(getClass(), args);
	};
 </pre>
  It is important that main method contains only this line, that the class itself does not change any static variables, and that any threads are killed in cleanup().
  The reason for this is that we might have a automated loader of multiple classes with pseudoserver in the future versions.
*/

public abstract class SIOMainApp {

	/**
	   No-argument constructor. All apps must have this, so that the Class.newInstance() will work.	   
	   Note that for the proper logging, all functions that can cause an exception should be called in the init() method
	 */
	public SIOMainApp() {
	};

	/**
	   Get application name. Default implementation returns uppercased classname.
	   @return Application name (as given to ServIO.init())
	*/
	public String getAppName() {
		String s = this.getClass().getName();
		return s.toUpperCase();
	}; 

	/**
	   Get the application version. Default implementation tries to use reflection ot get package version, and returns 0.10 if ti fails. 
	   @return Application version (as given to ServIO.init())
	*/
	public String getAppVersion() {
		Package p = this.getClass().getPackage();
		if (p == null) return "0.10b";
		String s = p.getImplementationVersion();
		if ( (s==null) || (s.equals("")) ) s = "0.10b";
		return s.toUpperCase();
	}; 

	/**
	   Get the application flags. See ServIO.init for details. Default implmentation returns 0.
	   @return flags
	 */
	public int getAppFlags() {
		return 0;
	};

	/**
	   Initialize the object. This is called after ServIO.init was successful.<br>
	   The default implementation assigne argument to "sio" variable
	   @param conn ServIO object used for server communication 
	 */
	public void init(ServIO conn) {
		sio = conn;
	};

	/**
	   Main method of the class. Will typically contain message-processing loop that could be only exited by exception.
	 */
	public abstract void run();


	/**
	   Cleanup method - will be called after run() exits, with exception or not
	   @param e   if run() exited with exception, the exception object
	 */
	public void cleanup(Throwable e) {
	};

	/**
	   This variable holds the pointer to ServIO object used to communicate with server.
	   It is set by the default implementation of init() method.
	 */
	protected ServIO sio;
};
