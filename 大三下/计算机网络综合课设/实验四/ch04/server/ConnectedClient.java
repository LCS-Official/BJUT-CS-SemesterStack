package com.cncd.ch04.server;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.net.Socket;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.LinkedList;

public class ConnectedClient {
    private ConnectionKeeper ck;
    public String uid;
    public String nick;
    public Date connectedTime;
    public String ipNumber;
    public int portNumber;
    public boolean verifyedBoolean = false;
    public int verifyedCount = 0;
    public String tmpNick = "";
    private ServerMsgSender msgSend;
    private ServerMsgListener msgList;
    private Socket sock;
    public boolean printMsg = false;

    public ConnectedClient(Socket sock, ConnectionKeeper ck) {
        this.ck = ck;
        ipNumber = sock.getInetAddress().getHostAddress();
        portNumber = sock.getPort();
        uid = "u" + Long.toHexString(System.nanoTime()) + Integer.toHexString(portNumber);
        this.sock = sock;
        msgSend = new ServerMsgSender(this.sock, this);
        msgList = new ServerMsgListener(this.sock, this);
        nick = "User" + portNumber;
    }

    public ConnectionKeeper getConnectionKeeper() {
        return ck;
    }

    public String getNick() {
        return nick;
    }

    public String getUid() {
        return uid;
    }

    public void sendMessage(String str) {
        msgSend.addMessage(str);
    }

    public void sendTo(String user, String msg) {
        ck.sendTo(this, user, msg);
    }

    public void broadcastMessage(String str) {
        if (!isSpam(str))
            ck.broadcast(str);
    }

    public void dropClient() {
        msgList.closeConnection();
        msgSend.closeConnection();
        ck.remove(this);
    }

    public void runCommand(String str) {
        ck.runCommand(this, str);
    }

    private boolean isSpam(String str) {
        return false;
    }

    public static void main(String arg[]) {
        MainServer ms = new MainServer(1984);
    }

    public void whoAmI() {
        String str = "<br>UID: " + uid + "<br>Connected Port: " + portNumber + "<br>" + "Nick: " + nick + "<br>";
        sendMessage(str);
    }
}

class ServerMsgSender extends Thread {
    private Socket sock;
    private LinkedList<String> msgList;
    private ConnectedClient cc;
    private boolean running = true;

    public ServerMsgSender(Socket sock, ConnectedClient cc) {
        this.sock = sock;
        this.cc = cc;
        collectInfo();
        msgList = new LinkedList<String>();
        start();
    }

    public synchronized void addMessage(String str) {
        if (cc.printMsg)
            System.out.println("MsgSender.addMessage: " + str);
        msgList.addLast(str);
    }

    private void collectInfo() {
    }

    public void run() {
        try {
            DataOutputStream dataOut = new DataOutputStream(sock.getOutputStream());
            while (running) {
                while (msgList.size() > 0) {
                    String toSend = msgList.removeFirst();
                    dataOut.write(toSend.getBytes(StandardCharsets.UTF_8));
                    dataOut.write(MainServer.MSGENDCHAR);
                    dataOut.flush();
                    if (cc.printMsg)
                        System.out.println("MsgSender.run: Sending: " + toSend);
                    sleep(10);
                }
                sleep(10);
            }
        } catch (Exception e) {
            String msg = e.getMessage();
            if (msg != null && (msg.startsWith(MainServer.DISCONNECTED) || msg.startsWith(MainServer.DISCONNECTED_CLIENT))) {
                System.out.println("MsgSender.run Client disconnected nick: " + cc.nick);
                cc.dropClient();
            } else {
                System.out.println("MsgSender.run: Msg: " + msg);
                e.printStackTrace();
                cc.dropClient();
            }
        }
    }

    public void closeConnection() {
        running = false;
    }
}

class ServerMsgListener extends Thread {
    private Socket sock;
    private ConnectedClient cc;
    private boolean running = true;

    public ServerMsgListener(Socket s, ConnectedClient cc) {
        sock = s;
        this.cc = cc;
        start();
    }

    public void closeConnection() {
        running = false;
    }

    public void run() {
        try {
            BufferedInputStream buffIn = new BufferedInputStream(sock.getInputStream());
            DataInputStream dataIn = new DataInputStream(buffIn);
            while (running) {
                int c;
                boolean didRun = false;
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                sleep(10);
                while ((c = dataIn.read()) != 0xff) {
                    if (c == -1)
                        throw new SocketException("Connection reset");
                    bytes.write(c);
                    if (!didRun)
                        didRun = true;
                }
                if (didRun) {
                    String text = new String(bytes.toByteArray(), StandardCharsets.UTF_8);

                    if (text.trim().length() == 0) {
                        continue;
                    }
                    boolean isAttachment = text.startsWith("file ") || text.startsWith("/file ")
                            || text.startsWith("image ") || text.startsWith("/image ");
                    if (!isAttachment && text.length() > 5000) {
                        text = text.substring(0, 5000) + "...(truncated)";
                    }

                    boolean isCommand = false;

                    if (text.startsWith("/")) {
                        cc.runCommand(text.substring(1));
                        isCommand = true;
                    } else {
                        String[] commands = {"login", "register", "search", "nick", "users", "msg", "gmsg", "friend", "profile", "file", "image", "whoami", "help", "stats", "exit"};
                        for (String cmd : commands) {
                            if (text.startsWith(cmd) && 
                                (text.length() == cmd.length() || text.charAt(cmd.length()) == ' ')) {
                                cc.runCommand(text);
                                isCommand = true;
                                break;
                            }
                        }
                    }

                    if (!isCommand) {
                        String toSend = "@CHAT2 " + cc.uid + "|" + cc.nick + "|public|全部|" + text;
                        ServerChatLog.chat("全部", cc.nick, text);
                        cc.broadcastMessage("@AVATAR2 " + cc.uid + "|" + cc.nick + "|" + avatarOf(cc.uid));
                        cc.broadcastMessage(toSend);
                    }
                }
            }
        } catch (SocketException se) {
            if (se.getMessage().startsWith("Connection reset"))
                cc.dropClient();
        } catch (Exception e) {
            e.printStackTrace();
            cc.dropClient();
        }
    }

    private String avatarOf(String user) {
        if (MainServer.ds == null) return "";
        for (String info : MainServer.ds.getAllUserInfo(user)) {
            if (info.startsWith("avatar=")) return info.substring("avatar=".length());
        }
        return "";
    }
}
