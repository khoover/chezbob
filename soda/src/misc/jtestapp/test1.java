
import com.theamk.ambus.*;
import java.io.*;
import java.util.*;



public class test1 extends SIOMainApp {

    public static void main(String args[]) {
		ServIORunner.runMainClass("test1", args);
	};

	void dumpVarList(String pref, VarList vl) {

		for (Iterator ni = vl.getNames().iterator(); ni.hasNext(); ) {
			String name = (String)ni.next();
			if (vl.isArray(name)) {
				sio.writeDebug(0, pref+" "+name+" is an array");
			} else {
				for (int i=0; i<vl.getCount(name, null); i++) {
					sio.writeDebug(0, pref+" "+name+((i>0)?(" ["+i+"]"):"")+" = "+vl.get(name, null, i));
				};
			};
		};
		sio.writeDebug(0, pref+" **end**");
	};

	VarList myVars;

	public void run() {
		
		myVars = sio.getVars(null, 0);
		dumpVarList("Startup-vars:", myVars);
		dumpVarList("FPSERV-vars:", sio.getVars("FPSERV", 0));

		sio.watchMessage("UI-READY", new FatalMsgHandler());
		sio.watchMessage("T1", new FatalMsgHandler());

		sio.watchMessage("T2", new LoggingMsgHandler());
		sio.watchMessage("T2\t1", new MsgHandler(){
				public boolean  handle(Msg m, String[] args) {
					sio.writeDebug(0, "This is interesting! someone have called T2 with argument 1");
					return (args.length > 1); // eat message if > 1 extra args						
				};
			});
		sio.watchMessage("T2\t2", new MsgHandler(){
				public boolean  handle(Msg m, String[] args) {
					dumpVarList("OWN-vars:", sio.getVars(null, 0));
					myVars.set("t2-called", "1");
					return true;
				};
			});
		sio.watchMessage("T3\t1\t5", new LoggingMsgHandler());

		// the code goes here
		while (true) {
			Msg m = sio.recv(30000); // 30 second timeout
			if (m == null) {
				sio.writeDebug(0, "I am idle");
				continue;
			};
			if (m.is("SYS-SET", "CONTROLLER") && m.get(2).equals("_apps%")) {
				sio.writeDebug(0, "Application in slot "+m.get(3)+" started with name "+m.get(4));
			} else if (m.is("SYS-UNSET", "CONTROLLER") && m.get(2).equals("_apps%")) {
				sio.writeDebug(0, "Application in slot "+m.get(3)+" exited");
			}
		}
	}
	

	class LoggingMsgHandler implements MsgHandler {
		public boolean handle(Msg message, String[] value) {
			sio.writeDebug("Received a message\t" + message);
			for (int i=0; i<value.length; i++)
				sio.writeDebug(" ... arg[" + (i) + "] is " + value[i]);
			return true;
		}
	}
};
