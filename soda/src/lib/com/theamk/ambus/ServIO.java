
package com.theamk.ambus;

import java.net.*; 
import java.io.*;
import java.util.*;
import java.lang.*;

/**
   ServIO - the main class that manages the connection to the server
 */

public class ServIO {
	String mServHost;
	int mServPort;
	int mDebugLevel;

	Socket mSock;
	InputStream mSockInput;
	PrintWriter mDataWriter;
	LinkedList mReaderQueue;
	LinkedList mHold;

	/* we have to have a reader thread as I am not sure yet if all IDEs support nio already */
	Thread mReaderThread;
	/* when reader exits, it sets this variable to the excpetion that has occured*/
	RuntimeException mReaderError;

	String mAppName;
	String mServName;
	String mAppVersion;
	int mFlags;

	Map mHandlers;
	Map mVarLists;
		

	/**
	   Create ServIO object and parse the arguments. Does not attempt to establish connection yet.<br>
	   Should not be called when you use ServIORunner/SIOMainApp.<br>
	   Reads enviromental variables SODACTRL_PORT and  SODACTRL_DEBUG for server port and debug level.
	   @param args  string array that was passed to main, or null
	 */
	public ServIO(String args[]) {
		mServHost = "localhost";
		mServPort = 2732;
		mDebugLevel = 50;
		mHandlers = new HashMap();
		try {
			String s = System.getProperty("sodactrl.PORT");
			if (s!=null)  mServPort = Integer.parseInt(s);
		} catch (NumberFormatException s) {};
		try {
			String s = System.getProperty("sodactrl.DEBUG");
			if (s!=null)  mDebugLevel = Integer.parseInt(s);
		} catch (NumberFormatException s) {};
	};


	/**
	   Allow mulitple instances of application to run
	*/
	public static final int ifMULTIPLE = 1;
	/**
	   Accept no messages by default
	*/
	public static final int ifACCEPT_NONE = 2;
	/**
	   Do not gather the config (server-set) variables on startup
	*/
	public static final int ifNO_CONFIG = 4;


	/**
	   Connect to the server and do the initial handshaking.
	   Should not be called when you use ServIORunner/SIOMainApp.
	   @param appname string that contains the application name, usually from the set [A-Z_-]
	   @param version string with application version, example: "0.99"
	   @param flags   one of the flags for init. see ifXXX constants
	   @throws SIOException if server did not like us or any other error occured
	*/
	public void init(String appname, String version, int flags) {
		try {
            mSock = new Socket(mServHost, mServPort);
            mDataWriter = new PrintWriter(mSock.getOutputStream(), true);
			mSockInput = mSock.getInputStream();
		} catch (java.io.IOException e) {
			throw new SIOException(e);
		};		
		mReaderQueue = new LinkedList();
		mHold = new LinkedList();
		mReaderThread = new Thread(new ServReader(), "ServIO-ServReader");
		mReaderThread.start();
		mVarLists = new HashMap();

		mAppName = appname;
		mAppVersion = version;
		mFlags = flags;
		String pid = System.getProperty("java.pid");
		if ((pid == null) || (pid.equals(""))) 
			try {
				BufferedReader bf = new BufferedReader(new FileReader("/proc/self/status"));
				while (true) {
					String s = bf.readLine();
					if (s==null) break;
					//System.out.println("S="+s);
					if (s.startsWith("Pid:\t")) {
						pid = s.substring(5);
						break;
					}
				}
			} catch (IOException e) {
				System.err.println("Cannot get PID: "+e);
			};
		
		String sflags = "";
		if ((flags & ifMULTIPLE) == 0) sflags = sflags + "u";
		if ((flags & ifACCEPT_NONE) == 0) sflags = sflags + "a";

		writeData("SYS-INIT", new String[]{"0:"+sflags, appname, version, pid, "japp"});
		Msg m = recv(-1);
		if (m.is("SYS-WELCOME")) {
			mServName = m.get(1);
		} else if (m.is("SYS-NOTWELCOME")) {
			throw new SIOException("Server did not like us\n"+m.get(2));
		} else {
			throw new SIOException("Server responded with JUNK\n" + m);
		};

		if ((flags & ifNO_CONFIG) == 0) {
			getVars("", 1); // do not issue GET's, as the SYS-SETs are already queued
			// all SYS-SET on us would be claimed, and the SYS-SET on controller will terminate the list.
			recv(10000);				
		};
	};

	
	/**
	   Report the exit code and close the connection to the server.
	   Should not be called when you use ServIORunner/SIOMainApp, as it will be called for you.
	   @param errcode integer error code or signal number. Use small positive integer if there is no numeric error code available.
	   @param errmsg the error message, a name of the failed function, or any other error-related information.
	 */
	public void close(int errcode, String errmsg) {
		try {
			writeData("SYS-DONE", new String[]{mAppName, ""+errcode, errmsg});
		} catch (SIOException s) {
		};

		try {
			// this shoud kill the thread
			mSock.shutdownInput();
			mDataWriter.close();
			mSock.close();
		} catch (java.io.IOException e) {
			throw new SIOException(e);
		};		
		mSock = null;
	};

	/**
	   get the server name, as returned by the server in SYS-WELCOME message
	*/
	public String getServName() {
		return mServName;
	};

	/**
	   get the appname, as specified at creation of object.
	*/
	public String getAppName() {
		return mAppName;
	};


	/**
	   Send the log information to server. The message will appear in the log and will be preserved for a long time.
	   @param msg    string to send
	   @throws SIOException  if the network error occured, including...
	   @throws SIODoneException if the server has disappeared
	*/
	public void writeLog(String msg) {
		System.out.println("S: "+msg);
		writeData("SYS-LOG\t"+mAppName+"\t"+msg);
	};


	/**
	   Send the debug information to server and to the console. <br>
	   This function should be used in place of the System.out.println, as during the production run, the console would not be available.
	   @param level  debug level - all messages less than a current level are NOT sent to a server.
	   @param msg    message to send	
	 */
	public void writeDebug(int level, String msg) {
		System.out.println("D["+level+"]: "+msg);
		if (level >= mDebugLevel) {
			writeData("SYS-DEBUG\t"+mAppName+"\t"+level+"\t"+msg);
		};
	};

	/**
	   write the debug message using default debug level (50)
	   @param msg   message to send
	*/
	public void writeDebug(String msg) {
		writeDebug(50, msg);
	};


	
	/**
	   Send the data to the server. The string must be tab-separated, binary-quoted and without newlines.<br>
	   Note that other form of writeData is recommended for general usage.
	   @param msg    string to sent
	   @throws SIOException  if the network error occured, including...
	   @throws SIODoneException if the server has disappeared
	*/
	public void writeData(String msg) {
		mDataWriter.println(msg);
	};

	/**
	   Binary-escape each string if needed, then join using tabs and send to the server.
	   Use like that for maximum beauty:
	   <pre> writeData("SYS-INIT", new String[]{"4:a", appname, version, pid, "japp"}); </pre>
	   @param msg	first element to send
	   @param args  rest of elements to send
	   @throws SIOException
	*/
	public void writeData(String msg, String[] args) {
		writeData(msg+"\t"+join(args, 0, -1));
	};

	/**
	   Binary-escape strings, then join them using tabs.
	   @param args  strings to join
	   @return a joined string
	 */
	public static String join(String[] args) {		
		return join(args, 0, -1);
	};

	/**
	   Binary-escape strings, then join them using tabs.
	   @param args  strings to join
	   @param start index of first emenet to join
	   @param length number of elements to join, -1 to join till last element
	   @return a joined string
	 */
	public static String join(String[] args, int start, int length) {
		StringBuffer result = new StringBuffer();;
		if (length==-1) 
			length=args.length;
		for (int i=start; i<(start+length) && i<args.length; i++) {
			if (i != start) 
				result.append("\t");
			// TODO: binary escape here
			result.append(args[i]);
		};
		return result.toString();
	};

	/** 
		Set a handler for the particular messages. Any incoming messages are passed to each matching handler, most specific first.<br>
		If handler returns <i>true</i>, then the message processing stops, and recv() starts waiting for next message or timeout.
		If handler returns <i>false</i>, then the message passed to next, less specific, handler. 
		If no handlers claim the message, the message is returned to the user.<p>
		Only one message with each mask can exist. To remove the handler, pass <i>null</i> in handler parameter.
		Be careful with handlers for SYS-* messages - if they return true, they might make some methods non-operative.
		@param mask  the mask of the message that will be matched using prefixMath function. Use join() to create.
		@param handler the MsgHandler interface that will handle this message
	*/
	public void watchMessage(String mask, MsgHandler handler) {
		if (handler == null) {
			mHandlers.remove(mask);
		} else {
			mHandlers.put(mask, handler);
		};
	};

	/**
	   Try to recieve a line from server. If m-hold buffer is non-empty, remove and return its first element.
	   Else, recieve the line from the network. Recieved line is first passed to installed handler functions, 
	   and if they claim the message, the message processing is stopped, and the next message is fetched if 
	   there is any time left in the timeout.
	   @param timeout  maximum time to wait, in milliseconds. 
               Use 0 to return immediately if there were no messages.
               Use -1 to wait forever. 
	   @return Msg object if a message was received; <i>null</i> otherwise
	   @throws SIOException
	*/
	public Msg recv(int timeout) {
		return recv(timeout, null);
	};

	/**
	   Receive a specific line from server. <br>
	   If there are any messages in the m-hold buffer that match filter, removes and returns this message. 
	   Else, receives line from the server.
	   Any line recieved is first passed to all installed handler functions, and then matched against the filter 
	   (unless the handler has claimed the message)
	   If filter accepts it, the message is returned to the user.
	   If it does not, the message is put in the m-hold buffer, and next time recv() is called, those messages would
	   @param timeout  maximum time to wait, see recv(timeout) for details
	   @param filter   a filter to match against messages. See Msg.match for details.
	   @return Msg object if a matching  message was received; <i>null</i> otherwise
	   @throws SIOException
	*/
	public Msg recv(int timeout, Object filter) {
		Msg m = null;
		long tstop = System.currentTimeMillis() + timeout;
		long tleft = (timeout==-1) ? 100000 : timeout;
		synchronized(mReaderQueue) {
			if (mHold.size() > 0) {
				for (ListIterator l=mHold.listIterator(0); l.hasNext(); ) {
					m = (Msg)l.next();
					if ((filter == null) || m.match(filter, 0, -1)) {
						l.remove();
						return m;
					};
				};
			};
		};
		while (true) {
			m = null;
			try {
				synchronized(mReaderQueue) {
					if (mReaderError != null) throw mReaderError;
					if ((tleft > 0) && (mReaderQueue.size() == 0)) {
						if (timeout == -1)
							mReaderQueue.wait();
						else
							mReaderQueue.wait(tleft);
					};
					if (mReaderQueue.size() != 0) { // did we win?
						m = (Msg)mReaderQueue.removeFirst();
					};
					if ((filter != null) && !m.match(filter, 0, -1)) {
						mHold.addLast(m);
						m = null;
					};
				};
			} catch (InterruptedException e) {
				throw new SIOException(e);
			};
		
			if (m != null) {
				if (handleMessage(m)) {
					m = null;
				};
			};

			tleft = tstop - System.currentTimeMillis();
			//writeDebug("done, m="+m+" tleft="+tleft);			

			if ((m!=null) || ((timeout >= 0) && (tleft <= 0)))
				return m;
		}
	}


	/**
	   Get the VarList object for the variables. Those objects could be used to get or set the variables on the server. 
	   If object has existed before, the existing instance is returned. If the instance had a different filter value, the exception is thrown.
	   Else, the object is created and the server is queried for current values of each variable. Additionally, the handlers 
	   are installed so that any change of the variable on the server will update the local copy.
	   @param appname string with application name; if it is null or empty string, returns the VarList for the current application
	   @param flags   the initial flags for this VarList. None are defined so far, so pass 0.
	   @return VarList object that could be used to access those vars.
	 */
	public VarList getVars(String appname, int flags) {
		if ((appname==null) || (appname.equals(""))) {
			appname = mAppName;
		};
		VarList v = (VarList)mVarLists.get(appname);
		if (v == null) {
			v = new VarList(this, appname, flags);
			if ((flags & 1) == 0)
				v.refreshAll();
			mVarLists.put(appname, v);
		};
		return v;
	};


	/**
	   Try to handle the message internally. 
	   @return true if the message is consumed, false if the message needs to be given to the user
	 */
	boolean handleMessage(Msg m) {		
		for (int i=m.count(); i>=1; i--) {
			String sub = m.sliceStr(0, i);
			MsgHandler mh = (MsgHandler)mHandlers.get(sub);
			if (mh != null) {
				String args[] = new String[m.count()-i];
				for (int j=0; j<args.length; j++)
					args[j] = m.get(j+i);
				boolean res = mh.handle(m, args);
				if (res)
					return true;
			};
		};
		return false;
	};

    private class ServReader implements Runnable {
		public void run() {
			RuntimeException rexp;
			try {
				BufferedReader mDataReader = new BufferedReader(new InputStreamReader(mSockInput));
				while (true) {
					String s = mDataReader.readLine();
					Msg m = new Msg(s);
					synchronized(mReaderQueue) {
						mReaderQueue.addLast(m);
						mReaderQueue.notifyAll();
					}
				}
			} catch (Exception e) {
				if (e instanceof RuntimeException) {
					rexp = (RuntimeException)e;
				} else {
					rexp = new RuntimeException(e);
				};
			};
			synchronized(mReaderQueue) {
				mReaderError = rexp;
				mReaderQueue.notifyAll();
			};
		};
	};
}





