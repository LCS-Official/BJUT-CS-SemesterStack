package com.cncd.ch04.server;

import java.net.Socket;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;

public class ConnectionKeeper {
    private final LinkedList<ConnectedClient> clientList;
    private final CommandParser cp;

    public ConnectionKeeper(CommandParser parser) {
        this.cp = parser;
        clientList = new LinkedList<ConnectedClient>();
    }

    public synchronized void add(Socket s) {
        MainServer.connects++;
        ConnectedClient client = new ConnectedClient(s, this);
        clientList.addLast(client);
        client.sendMessage("@SYSTEM connected to chat server, please set your nickname.");
        notifyUsers();
    }

    public synchronized void remove(ConnectedClient cc) {
        clientList.remove(cc);
        if (cc.verifyedBoolean) broadcast("@SYSTEM " + cc.nick + " is offline");
        notifyUsers();
    }

    public synchronized LinkedList<ConnectedClient> users() {
        return new LinkedList<ConnectedClient>(clientList);
    }

    public void runCommand(ConnectedClient cc, String str) {
        cp.runCommand(cc, str);
    }

    public synchronized ConnectedClient findUser(String user) {
        for (ConnectedClient receiver : clientList) {
            if (user.equalsIgnoreCase(receiver.uid) || user.equalsIgnoreCase(receiver.nick)) {
                return receiver;
            }
        }
        return null;
    }

    public void sendTo(ConnectedClient sender, String user, String msg) {
        ConnectedClient receiver = findUser(user);
        if (receiver == null) {
            sender.sendMessage("@SYSTEM online user not found: " + user);
            return;
        }
        receiver.sendMessage(msg);
    }

    public synchronized void broadcast(String msg) {
        for (ConnectedClient cc : clientList) {
            cc.sendMessage(msg);
        }
    }

    public synchronized void notifyUsers() {
        List<String> names = new ArrayList<String>();
        for (ConnectedClient cc : clientList) {
            if (!cc.verifyedBoolean) continue;
            names.add(cc.uid + "|" + cc.nick);
        }
        broadcast("@USERS " + String.join(",", names));
    }
}
