package com.theamk.ambus;

import java.util.*;

/**
   This class represents a set of server-local variables for the specified server.
   It watches for SYS-SET messages so that any updates to the variables on the server are reflected in local copies.
   <p>
   Internally, each variable is a Map of Arrays 
 */

public class VarList {
	ServIO sio;

	int mFlags;
	String mAppname;
	Object mFilter;
	Handler mHandler;

	/**
	   Internal variables hash. 
	   Map[String(varname)] of Map[String(keyname)] of Vector(values)
	 */
	Map mVariables;

	/**	
	   private constructor. Use ServIO.getVars from the user code.
	 */
	VarList(ServIO servio, String appname, int flags) {
		mFlags = flags;
		mAppname = appname;
		mFilter = null;
		mVariables = new TreeMap();
		sio = servio;
		mHandler = new Handler();
		sio.watchMessage(ServIO.join(new String[]{ "SYS-SET", mAppname }), mHandler);
		sio.watchMessage(ServIO.join(new String[]{ "SYS-UNSET", mAppname }), mHandler);
	};

	/**
	   Asks the server for the values of all variables.  Redundant unless automatic variable watching is disabled.
	 */
	public void refreshAll() {
		// clean up all old variables first...
		mVariables = new TreeMap();

		String anj = ServIO.join( new String[]{  "", mAppname} );
		sio.writeData("SYS-GET" + anj);
		Msg resp = sio.recv(10000, "SYS-VALUE" + anj);
		if (resp == null) throw new SIOException("SYS-GET on "+mAppname+ " timed out");
		for (int i=4; i<resp.count(); i++) {
			String name = resp.get(i);
			if (isArray(name)) {
				sio.writeData("SYS-GET", new String[]{  mAppname, name, "" });
				Msg r2 = sio.recv(10000, "SYS-VALUE"+anj);
				if (resp == null) throw new SIOException("SYS-GET on "+mAppname+ "." + name +" timed out");				
				//for (j=3; j<r2.count(); j++) {
				//};
			} else {
				sio.writeData("SYS-GET", new String[]{  mAppname, name, "" });
				Msg r2 = sio.recv(10000, "SYS-VALUE"+anj);
				if (resp == null) throw new SIOException("SYS-GET on "+mAppname+ "." + name +" timed out");				
				mHandler.handle(r2, null);
			};
		};
	};

	/**
	   Get the set of the names of all variables.
	   @return Set of all variable names
	 */
	public Set getNames() {
		return Collections.unmodifiableSet(mVariables.keySet());
	};

	/**
	   returns true if variable name refers to an array
	*/
	public boolean isArray(String name) {
		return name.endsWith("%");
	};

	/**
	   Get the set of the array keys of given array
	   @param array  array name. If % on the end is omitted, it is addded automatically.
	   @return Set of all array elements, or null if there is no such array
	*/
	public Set getArrayKeys(String array) {
		if (!array.endsWith("%")) array = array + "%";
		Map keys = (Map)mVariables.get(array);
		if (keys == null)
			return null;
		return Collections.unmodifiableSet(keys.keySet());
	};

	/**
	   Get the number of the fields in the value
	   @param name  variable or array name (% will be appended if not found and key is not null)
	   @param key   array key or undef for variables
	   @return field count. -1 if variable or key was not found.
	 */
	public int getCount(String name, String key) {
		if ((key != null) && !name.endsWith("%")) name = name + "%";
		Map keys = (Map)mVariables.get(name);
		if (keys == null)
			return -1;
		Vector values = (Vector)keys.get((key==null)?"":key);
		if (values == null)
			return -1;
		return values.size();
	};

	/**
	   Get a field in the array element or a string value.
	   @param name  variable or array name (% will be appended if not found and key is not null)
	   @param key   array key or undef for variables
	   @param field  the field in the value, from 0 to getCount -1 
	   @return string value of a field, or empty string if variable not found/key/field invalid
	*/
	public String get(String name, String key, int field) {
		if ((key != null) && !name.endsWith("%")) name = name + "%";
		Map keys = (Map)mVariables.get(name);
		if (keys == null)
			return "";
		Vector values = (Vector)keys.get((key==null)?"":key);
		if (values == null)
			return "";
		if ((field<0) || (field>=values.size()))
			return "";
		return (String)values.get(field);
	};

	/**
	   Set the watch on the variable.
	   UNIMPLEMENTED
	 */
	void watchVariable(String varname, MsgHandler handler) {
	};


	/**
	   Change the variable value. 
	   Updates the internal cache and representaion on server.
	   If the value being set is the same as a vcurrent value, no message is sent to the server - thus, 
	   you can call this function often without performance penalty.
	   @param name  variable or array name (% will be appended if not found and key is not null)
	   @param key   array key or undef for variables. Can not be empty string for arrays.
	   @param val   array of strings - new value.
	*/
	public void set(String name, String key, String[] val) {
		if ((key != null) && !name.endsWith("%")) name = name + "%";

		Map keys = (Map)mVariables.get(name);
		if (keys == null) {
			keys = new TreeMap();
			mVariables.put(name, keys);
		};

		boolean same_as_old = false;
		if (key==null) key="";
		Vector values = (Vector)keys.get(key);
		if (values != null) {
			same_as_old = (values.size() == val.length);
			if (same_as_old) {
				for (int i=0; i<values.size(); i++)
					if (!values.get(i).equals(val[i]))
						same_as_old = false;
			}
		};		
		if (same_as_old) return;

		values = new Vector();
		for (int i=0; i<val.length; i++)
			values.add(val[i]);
		keys.put(key, values);
		sio.writeData(ServIO.join(new String[]{  "SYS-SET", mAppname, name, key, "" }) + ServIO.join(val));
	};

	/**
	   Set a simple variable - same as set(name, null, { val });
	 */
	public void set(String name, String val) {
		set(name, null, new String[]{ val });
	};

	/**
	   Notify user of variable change. Called after the value has been written.	   
	 */
	void doNotify(Msg m, String var, String key) {
	};
	
	class Handler implements MsgHandler {		
		/**
		   This can be also called manually with SYS-VALUE, so do not rely on args....
		 */
		public boolean handle(Msg m, String[] args) {
			if (m.count() < 3) return false; // malformed
			String name = m.get(2);
			Map old = (Map)mVariables.get(name);

			if (m.is("SYS-UNSET")) {
				if (args.length == 1) {
					if (old != null) {
						mVariables.remove(name);
						doNotify(m, name, null);
					};
				} else {
					for (int i=3; i<m.count(); i++) {
						String key =m.get(3);
						if (old.get(key) != null) {
							old.remove(key);
							doNotify(m, name, key);
						};
					};
				};
			} else { // must be SYS-SET or SYS-VALUE
				if (m.count() < 4) return false; // malformed
				String key = m.get(3);
				if (old == null) {
					old = new TreeMap();
					mVariables.put(name, old);
					if (!key.equals("")) doNotify(m, key, null);
				};
				Vector v = new Vector(m.count() - 4);
				for (int i=4; i<m.count(); i++)
					v.add(m.get(i));
				old.put(key, v);
				doNotify(m, key, key.equals("")?null:key);
			};
		return true;
		};
	};
};
