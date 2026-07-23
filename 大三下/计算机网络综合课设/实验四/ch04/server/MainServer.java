package com.cncd.ch04.server;
import java.net.*;
import java.io.*;
public class MainServer extends Thread {
    public static final String DISCONNECTED = "Software caused connection abort";
    public static final String DISCONNECTED_CLIENT = "Socket closed";
    public static final String PORT_USED_ERROR = "Address already in use: JVM_Bind";
    public static long uptime = 0; 
    public static long connects = 0;
    public static final char MSGENDCHAR = 0xff;
    int port = 1984;
    int clients = 8;
    private boolean newPort = true;
    private ServerSocket sSock;
    private Socket sock;
    public ConnectionKeeper ck;
    public static DataSource ds;
    public static CommandParser cp;
    public MainServer(int port) {
        this.port = port;
        ck = new ConnectionKeeper(MainServer.cp);
        MainServer.uptime = System.currentTimeMillis();
        start();
    }
    public void run() {
        while(true) {
            try {
                sSock = new ServerSocket(port);
                if(newPort) {
                    System.out.println("Server Listening at port: " + sSock.getLocalPort());
                    newPort = false;
                }
                while(true) {
                    sock = sSock.accept();
                    ck.add(sock);
                }
            } catch(Exception e) {
                String message = e.getMessage();
                if(message != null && message.startsWith(MainServer.PORT_USED_ERROR)) {
                    System.out.println("Port " + port + " is already used, Attempting to use " + (port+=1));
                    newPort = true;
                } else {
                    e.printStackTrace();
                    System.exit(1);
                }
            }
        }
    }
    public static void sleep(int time) {
        try {
            Thread.sleep(time);
        } catch(Exception e) {}
    }
    public static void main(String arg[]) {
        int port = 0;
        MainServer ms;
        MainServer.ds = new FileDataSource();
        MainServer.cp = new BroadcastCommandParser();
        MainServer.cp.setDataSource(MainServer.ds);
        if(arg.length!=1) {
            ms = new MainServer(3500);
            System.out.println("Usage: java jchat.server.MainServer <port>\nAttempting to use default port 3500");
        } else {
            try {
                port = Integer.parseInt(arg[0]);
            } catch(NumberFormatException nfe) {
                System.out.println("Attempting to use default port 3500");
                port = 3500;
            } finally {
                ms = new MainServer(port);
            }
        }
    }
}
