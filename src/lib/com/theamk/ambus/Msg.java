package com.theamk.ambus;


	public class Msg {
		/**
		   Construct the message from the tab-separated string
		*/
		public Msg(String rawMsg) {
			mRawMsg = rawMsg;
			mFields = mRawMsg.split("\t");
			// TODO: binary unescape
		};
		
		/**
		   @return tab-separated message as recieved from the server
		*/
		public String getRawMsg() {
			return mRawMsg;
		};
		
		/**
		   Select sub-fields of the message joined by the tab character.
		   @param start    index of first field (0-based)
		   @param length   number of fields to include, or -1 to include until the end of string
		   @return a string with given fields		   
		 */
		public String sliceStr(int start, int length) {
			return ServIO.join(mFields, start, length);
		};

		/**
		   Match the give string prefix against the message.
		   This is almost like startsWith, except that the match must end on the token boundary. 
		   Thus, "UI-RELOAD{tab}1" would match "UI-RELOAD{tab}1" and "UI-RELOAD{tab}1{tab}none", but not "UI-RELOAD{tab}100
		   @param str prefix string to match against
		   @return true if matches, false otherwise.
		*/
		public boolean prefixMatch(String str) {
			return match(str, 0, -1);
		};

		/**
		   Match the given object against the message. If Object is a String, then prefixMatch is used. If object is null, it always matches.
		   In the future, the support for vectors or regular expressions might me added.
		   @param obj  the match object of one of the supported types
		   @param offset the first field to match on. Use 0 to match on whole message
		   @param length the number of fields to match on. Use -1 to match until the message end.
		   @return true if matches
		   @throws ClassCastException if the object is not one of the supported types
		 */
		public boolean match(Object obj, int offset, int length) {
			if (obj == null)
				return true;
			String payload;
			if ((offset==0) && ((length==-1) || (length>=mFields.length))) {
				payload = mRawMsg;
			} else {
				payload = sliceStr(offset, length);
			};
			if (obj instanceof String) {
				String str = (String)obj;
				return payload.equals(str) ||
					payload.startsWith(str + "\t");			
			};
			throw  new ClassCastException(obj.getClass().getName() + " can not be used in Msg.match function");
		};


		/**
		   Get the value of one of the fields in the message
		   @param i  field index (0 - message type, 1+ - arguments)
		   @return field value, or empty string if index is out of bounds
		 */
		public String get(int i) {
			if (i<0 || i>=mFields.length)
				return "";
			return mFields[i];
		};

		/**
		   Get the number of fields in the message
		   @return number of fields (at least 1)
		*/
		public int count() {
			return mFields.length;
		};

		/**
		   Compare the message type (first token) to goven string
		   @return true if the same
		*/
		public boolean is(String t0) {
			return get(0).equals(t0);
		};

		/**
		   Compare first two tokens of the message to the given strings
		*/
		public boolean is(String t0, String t1) {
			return get(0).equals(t0) && get(1).equals(t1);
		};

		/**
		   Returns string represntation of the message in the nice, human-readable format:
		   <pre> [ SYS-ACCEPT | * ] </pre>
		*/
		public String toString () {
			StringBuffer sb = new StringBuffer();
			sb.append("[ ");
			for (int i=0; i<count(); i++) {
				if (i!=0) sb.append(" | ");
				sb.append(get(i));
			};
			sb.append(" ]");
			return sb.toString();
		};

		String mRawMsg;
		String[] mFields;
	};

