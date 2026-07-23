package com.cncd.ch04.server;
import java.util.*;
import java.security.*;
import java.io.*;
public class FileDataSource implements DataSource {
    String[] us = {"no connected users"}; // An array of all users.
    boolean userListChanged = true;
    boolean debug = false;
    LinkedList users = new LinkedList();
    LinkedList infoList = new LinkedList();
    String pathSep = System.getProperty("file.separator");
    String fsroot = System.getProperty("user.dir") + pathSep
                        + "chat-data" + pathSep;
    File userFile, infoFile;
    boolean basicWrite = false;
    boolean allWrite = false;
    private final String[] infoComments = {"# Info file for Chat Server",
                             "# Used when the server is running in FileDataSource mode",
                             "# <username> <field> <data>",
                             "# username is the name of the user which the info belongs to"};
                             
    private final String[] userComments = {"# User file for Mihaly Chat Server",
                             "# <username> <password>",
                             "# usernames are in clear text",
                             "# passwords are MD5 hashes"};
     public FileDataSource() {
        System.out.println("FileDataSource init");
        initFileSystem();
        if(allWrite) {
            readFiles();
        }  
    }
    public void printAll() {
        if(debug)System.out.println("\nStaring to print");
        Iterator it = users.iterator();
        while(it.hasNext())
            ((User)(it.next())).printUser();
        it = infoList.iterator();
        while(it.hasNext())
            ((Info)(it.next())).printInfo();
        if(debug)System.out.println("Ending print\n");
    }
    private void initFileSystem() {
        File file = new File(fsroot);
        if(file.exists() && file.isDirectory()) {
            if(debug)System.out.println("FileDataSource home " + fsroot);
            basicWrite = true;
        } else {
            System.out.println("FileDataSource is unable to access home" + 
                                "\nAttempting to create home");
            file.mkdirs();
            if( !(file.exists() && file.isDirectory()) ) 
                System.out.println("FileDataSource is unable to create home @ " 
                        + fsroot + " ex " + file.exists() + " isDir "
                        + file.isDirectory());
            else {
                System.out.println("FileDataSource home created " + fsroot);
                basicWrite = true;
            }
        }
        if(basicWrite) {
            userFile = new File(fsroot + "users");
            infoFile = new File(fsroot + "info");
            if(userFile.exists() && infoFile.exists()) {
                if(userFile.canRead() && userFile.canWrite() 
                    && infoFile.canRead() && infoFile.canWrite()) {
                    if(debug) System.out.println("FileDataSource userfile " + userFile + 
                        "\nFileDataSource infofile " + infoFile);
                    allWrite = true;
                } else {
                    System.out.println("FileDataSource files exist but" +
                        "userFile.read "  + userFile.canRead() +
                        "userFile.write "  + userFile.canWrite() +
                        "infoFile.read "  + infoFile.canRead() +
                        "userFile.write "  + userFile.canWrite());
                }
            } else {
                try {
                    userFile.createNewFile();
                    infoFile.createNewFile();
                    if(userFile.exists() && infoFile.exists()) {
                        if(userFile.canWrite() && infoFile.canWrite()) {
                            if(debug) System.out.println("FileDataSource userfile " 
                                + userFile + "\nFileDataSource infofile " 
                                + infoFile);
                            createFiles();
                            allWrite = true;
                        } else {
                            System.out.println("FileDataSource user/info files " + 
                                "we just created are not writeable :(");
                        }
                    } else {
                        System.out.println("FileDataSource you shouldn't get " +
                            "here but you did. The user/info file that we just" +
                            "created are gone missing");
                    }
                } catch(IOException ioe) {
                    System.out.println("FileDataSource " + ioe.getMessage());
                }
            }
        }      
    }
    private void createFiles() {
        for(int i=0;i<userComments.length;i++)
            appendToUserFile(userComments[i]);        
        
        for(int i=0;i<infoComments.length;i++)
            appendToInfoFile(infoComments[i]);
    }
    private void readFiles() {
        
        Object[] ObjUsers = readLines(userFile);
        Object[] ObjInfo  = readLines(infoFile);
        users = new LinkedList();
        infoList = new LinkedList();
        try {
            for(int i = 0;i<ObjUsers.length;i++) {
                String str = "" + ObjUsers[i];
                String name = str.substring(0, str.indexOf(" "));
                String pass = str.substring(str.indexOf(" ")+1);
                users.add(new User(name,pass));
            }
            for(int i = 0;i<ObjInfo.length;i++) {
                String str = "" + ObjInfo[i];
                String[] infoParts = str.split(" ", 3);
                if(infoParts.length == 3) {
                    infoList.add(new Info(infoParts[0], infoParts[1], infoParts[2]));
                }
            }
        } catch(Exception e) {
            errorInFiles(e);
        } 
    }
    private void appendToUserFile(String str) {
        appendToFile(userFile, str);
    }
    private void appendToInfoFile(String str) {
        appendToFile(infoFile, str);
    }
    private void appendToFile(File e, String str)  {
        try {
            Writer out = new OutputStreamWriter(new FileOutputStream(e,true), "UTF-8");
            out.write(str + "\n");
            out.close();
        } catch(IOException ioe) {
            System.out.println("FileDataSource alot of checks was done when initing " + 
                " " + e + " still it got messed up! This time no checks!");
            ioe.printStackTrace();
        }
    }
    private void removeUserFromFile(String user) {
        try {
            if(allWrite) {
                File f = new File(fsroot + "newUser");
                FileOutputStream fo = new FileOutputStream(f);
                BufferedOutputStream buffOut = new BufferedOutputStream(fo);
                DataOutputStream dataOut = new DataOutputStream(buffOut); 
                for(int i=0;i<userComments.length;i++)
                    dataOut.write((userComments[i] + "\n").getBytes("UTF-8"));
                Iterator it = users.iterator();
                while(it.hasNext()) {
                    User s = (User)it.next();
                    dataOut.write(("" + s.getName() + " " + s.getPass() + "\n").getBytes("UTF-8"));
                }
                dataOut.close();
                buffOut.close();
                fo.close();
                f.renameTo(userFile);
            }
        } catch(IOException ioe ) {
            System.out.println("FileDataSource.removeUserFromFile user " + user);
            ioe.printStackTrace();
        }
    }
    private void removeInfoFromFile(String user, String field, String data) {
    }
    private void errorInFiles(Exception e)  {
        System.out.println("FileDataSoure errorInFiles ");
        e.printStackTrace();
    }
    private Object[] readLines(File f) {
        LinkedList list = new LinkedList();
        try {
            FileInputStream fileIn = new FileInputStream(f);
            InputStreamReader isr = new InputStreamReader(fileIn, "UTF-8");
            BufferedReader dataIn = new BufferedReader(isr);
            String str = "";
            while( (str = dataIn.readLine()) != null ) 
                if(str.length() > 0 && str.charAt(0) != '#')
                    list.add(str);
        } catch(IOException ioe) {
            System.out.println("FileDataSource.readLines(File " + f + "): " + ioe.getMessage());
        } finally {
            return list.toArray();
        }
    }
    public String getMD5(String str) {
        MessageDigest md = null;
        try {
            md = MessageDigest.getInstance("MD5");
            byte[] by = str.getBytes("UTF-8");
            md.update(by);
        } catch(Exception e) {e.printStackTrace();}
        byte[] b = md.digest();
        String strOut = "";
        for(int i=0;i<b.length;i++) strOut += b[i];
        return strOut;
    }
    public synchronized boolean addInfo(String user, String field, String data) {
        if(user == null || field == null || data == null
            || user.equals("") || field.equals("")) return false;
        removeInfoFromMemory(user, field);
        infoList.add(new Info(user, field, data));
        rewriteInfoFile();
        return true;
    }
    public boolean addUser(String user, String pass) {
        if(user == null || pass==null 
            || user.equalsIgnoreCase("") || pass.equalsIgnoreCase("") )
            return false;
        if(verifyUser(user,"")) {
            String md5 = getMD5(pass);
            User tmpUser = new User(user, md5);
            users.add(tmpUser);
            appendToUserFile(user + " " + md5);
            userListChanged = true;
            return true;
        }
        return false;
    }
    public boolean removeUser(String user, String pass) {
        if(user == null || pass==null 
            || user.equalsIgnoreCase("") || pass.equalsIgnoreCase("") )
            return false;
        Iterator it = users.iterator();
        boolean found = false;
        User s = null;
        while(it.hasNext() && !found) {
            s = (User)(it.next());
            if(s.getName().equalsIgnoreCase(user)) {
                found = true;
                if(s.getPass().equalsIgnoreCase(pass)) {
                    users.remove(s);
                    removeUserFromFile(user);
                    return (userListChanged = true);
                }                
            }
        }
        return false;
    }
    public boolean verifyUser(String user, String pass) {
        Iterator it = users.iterator();
        boolean found = false;
        User s = null;
        while(!found && it.hasNext()) {
            s = (User)(it.next());
            if(s.getName().equalsIgnoreCase(user)) {
                found = true;
            }
        }
        if(found) {
            if(s.getPass().equalsIgnoreCase(pass))
                return true;
            else return false;
        }
        return true;
    }
    class User {
        private String n;
        private String p;
        public User(String name, String password) {
            n = name;
            p = password;
        }
        public String getName() {
            return n;
        }
        public String getPass() {
            return p;
        }
        public void printUser() {
            System.out.println("FileDataSource.User registered user " + n);
        }
    }
    class Info {
        String user;
        String field;
        String data;
        public Info(String user, String field, String data) {
            this.user = user;
            this.field = field;
            this.data = data;
        }
        public void printInfo() {
            System.out.println("FileDataSource.Info registered info " + 
                               " \n\tuser " + user + " field " + field + " data " + data);
        }
    }
    public static void main(String args[]) {
        FileDataSource fd = new FileDataSource();
        fd.printAll();
        System.out.println("verify mihaly " + fd.verifyUser("mihaly", ""));
        System.out.println("addUser mihaly/thuglife " + fd.addUser("mihaly", "thuglife"));
        System.out.println("addUser outlaw/2Pac " + fd.addUser("outlaw", "2Pac"));
        System.out.println("verify mihaly/thuglife " + fd.verifyUser("mihaly", fd.getMD5("thuglife")));
        System.out.println("verify mihaly/Thuglife " + fd.verifyUser("mihaly", fd.getMD5("Thuglife")));
        System.out.println("verify outlaw/2Pac " + fd.verifyUser("outlaw", fd.getMD5("2Pac")));
        fd.printAll();
        System.out.println("remove mihaly/thuglife " + fd.removeUser("mihaly", fd.getMD5("thuglife")));
        fd.printAll();
    }
    public String[] getUserList() {
        int usSize = users.size();
        if(userListChanged && usSize>0) {
            us = new String[usSize];
            Iterator it = users.iterator();
            for(int i=0;it.hasNext();i++) 
                us[i] = "" + ((User)(it.next())).getName();
            userListChanged = false;
        }
        return us;
    }
    public synchronized String[] getAllUserInfo(String user) {
        LinkedList result = new LinkedList();
        Iterator it = infoList.iterator();
        while(it.hasNext()) {
            Info info = (Info)it.next();
            if(info.user.equalsIgnoreCase(user)) {
                result.add(info.field + "=" + info.data);
            }
        }
        if(result.size() == 0) result.add("暂无资料");
        String[] arr = new String[result.size()];
        for(int i = 0; i < arr.length; i++) arr[i] = "" + result.get(i);
        return arr;
    }
    public synchronized boolean removeInfo(String user, String field, String info) {
        removeInfoFromMemory(user, field);
        rewriteInfoFile();
        return true;
    }
    private void removeInfoFromMemory(String user, String field) {
        Iterator it = infoList.iterator();
        while(it.hasNext()) {
            Info one = (Info)it.next();
            if(one.user.equalsIgnoreCase(user) && one.field.equalsIgnoreCase(field)) {
                it.remove();
            }
        }
    }
    private void rewriteInfoFile() {
        try {
            Writer out = new OutputStreamWriter(new FileOutputStream(infoFile, false), "UTF-8");
            for(int i=0;i<infoComments.length;i++) out.write(infoComments[i] + "\n");
            Iterator it = infoList.iterator();
            while(it.hasNext()) {
                Info info = (Info)it.next();
                out.write(info.user + " " + info.field + " " + info.data + "\n");
            }
            out.close();
        } catch(Exception ioe) {
            System.out.println("FileDataSource.rewriteInfoFile: " + ioe.getMessage());
        }
    }
}
