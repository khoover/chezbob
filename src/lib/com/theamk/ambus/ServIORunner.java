package com.theamk.ambus;

public class ServIORunner {
	
	/**
	   Connects to server, then instantiates the given class and runs its run() method.
	   The cname must extend SIOMainApp.
	   @param  classname   the name of the class to load
	   @param  args        args given to main
	 */
	public static void runMainClass(String classname, String[] args) {
		SIOMainApp ma = null;
		boolean init_ok = false;
		ServIO s = new ServIO(args);

		try {
			Class c = Class.forName(classname);
			ma = (SIOMainApp)c.newInstance();
		} catch (Exception e) {		
			java.io.PrintStream log = System.err;

			log.println("Cannot instantiate class "+classname+":");
			if (e instanceof ClassNotFoundException)
				log.println("Class not found: "+e.getMessage());
			else if (e instanceof InstantiationException)
				log.println("InstantiationException: "+e.getMessage());
			else if (e instanceof IllegalAccessException)
				log.println("Illegal access (are class and constructor public?): "+e.getMessage());
			else
				e.printStackTrace(log);
			System.exit(1);
		};

		Throwable ex = null;
		try {

			String app = ma.getAppName();
			String ver = ma.getAppVersion();
			int flg = ma.getAppFlags();

			s.init(app, ver, flg);
			ma.init(s);
			init_ok = true;
			ma.run();			
		} catch (Throwable e) {
			ex = e;
		};

		if (init_ok) ma.cleanup(ex);
		if (ex == null)
			s.close(0, ex+"");
		else
			s.close(3, ex+"");

		System.out.println("--EXITING--\n" + ex);
	};

	/**
	   main argument - allows loading of arbitrary SIOMainApp classes even if they do not have the main() method.
	   Takes the class name from the last argument. 
	   Example (in bash assuming jar is in ../lib): <pre>
	   export CLASSPATH=../lib/ServIO.jar:.
	   java  com.theamk.ambus.ServIORunner test1
	   </pre>
	 */
    public static void main(String args[]) {
		if (args.length == 0) {
			System.err.println("You need to specify main class name");
			System.exit(1);
		};
		runMainClass(args[args.length-1], args);
	};
};
