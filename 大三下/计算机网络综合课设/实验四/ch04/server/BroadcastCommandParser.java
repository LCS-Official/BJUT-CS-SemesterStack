package com.cncd.ch04.server;

import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.LinkedList;
import java.util.Map;
import java.util.Set;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.security.MessageDigest;

public class BroadcastCommandParser implements CommandParser {
    private DataSource ds;
    private final Map<String, Set<String>> friends = new HashMap<String, Set<String>>();
    private final Set<String> pendingFriends = new HashSet<String>();

    public BroadcastCommandParser() {
        System.out.println("BroadcastCommandParser");
    }

    public void runCommand(ConnectedClient cc, String str) {
        try {
            if (ds == null) {
                cc.sendMessage("@SYSTEM data source not initialized.");
                return;
            }
            String[] parts = str.split(" ", 3);
            String command = parts[0].toLowerCase();

            if ("login".equals(command)) {
                require(parts, 3, "Usage: /login <id> <password>");
                login(cc, parts[1], parts[2]);
            } else if ("register".equals(command)) {
                require(parts, 3, "Usage: /register <nickname> <password>");
                register(cc, parts[1], parts[2]);
            } else if ("search".equals(command)) {
                require(parts, 2, "Usage: /search <id>");
                search(cc, parts[1]);
            } else if ("nick".equals(command)) {
                require(parts, 2, "Usage: /nick <name>");
                setNick(cc, parts[1].trim());
            } else if ("users".equals(command)) {
                cc.getConnectionKeeper().notifyUsers();
            } else if ("msg".equals(command)) {
                require(parts, 3, "Usage: /msg <user> <message>");
                if (parts[2].trim().length() == 0) {
                    cc.sendMessage("@SYSTEM message cannot be empty.");
                    return;
                }
                privateMsg(cc, parts[1], parts[2]);
            } else if ("gmsg".equals(command)) {
                require(parts, 3, "Usage: /gmsg <user1,user2> <message>");
                if (parts[2].trim().length() == 0) {
                    cc.sendMessage("@SYSTEM message cannot be empty.");
                    return;
                }
                groupMsg(cc, parts[1], parts[2]);
            } else if ("friend".equals(command)) {
                require(parts, 3, "Usage: /friend add <user> or /friend accept <user>");
                friend(cc, parts[1], parts[2]);
            } else if ("profile".equals(command)) {
                profile(cc, parts);
            } else if ("file".equals(command) || "image".equals(command)) {
                require(parts, 3, "Usage: /" + command + " <user> <filename>|<base64>");
                if (parts[2].trim().length() == 0) {
                    cc.sendMessage("@SYSTEM attachment content cannot be empty.");
                    return;
                }
                attachment(cc, command, parts[1], parts[2]);
            } else if ("whoami".equals(command)) {
                cc.whoAmI();
            } else if ("help".equals(command)) {
                String helpMsg = 
                    "<b>===== Chat Commands =====</b><br>"
                    + "<br>"
                    + "<b>-- Basic --</b><br>"
                    + "/login &lt;id&gt; &lt;password&gt; - login<br>"
                    + "/register &lt;nickname&gt; &lt;password&gt; - create account<br>"
                    + "/search &lt;id&gt; - search user<br>"
                    + "/nick &lt;name&gt; - set or change nickname<br>"
                    + "/users - show online users<br>"
                    + "/whoami - show your info<br>"
                    + "/stats - server status<br>"
                    + "/exit - disconnect<br>"
                    + "<br>"
                    + "<b>-- Chat --</b><br>"
                    + "/msg &lt;user&gt; &lt;msg&gt; - send private message<br>"
                    + "/gmsg &lt;user1,user2&gt; &lt;msg&gt; - send group message<br>"
                    + "<br>"
                    + "<b>-- Friend --</b><br>"
                    + "/friend add &lt;user&gt; - send friend request<br>"
                    + "/friend accept &lt;user&gt; - accept friend request<br>"
                    + "<br>"
                    + "<b>-- Profile --</b><br>"
                    + "/profile set &lt;field&gt;=&lt;value&gt; - save profile<br>"
                    + "/profile view &lt;user&gt; - view profile<br>"
                    + "<br>"
                    + "<b>-- File --</b><br>"
                    + "/file &lt;user&gt; &lt;name&gt;|&lt;base64&gt; - send file<br>"
                    + "/image &lt;user&gt; &lt;name&gt;|&lt;base64&gt; - send image";
                cc.sendMessage("@SYSTEM " + helpMsg);
            } else if ("stats".equals(command)) {
                stats(cc);
            } else if ("exit".equals(command)) {
                cc.sendMessage("@SYSTEM disconnected.");
                cc.dropClient();
            } else {
                cc.sendMessage("@SYSTEM unknown command: " + str);
            }
        } catch (IllegalArgumentException e) {
            cc.sendMessage("@SYSTEM " + e.getMessage());
        } catch (Exception e) {
            System.out.println("CommandParser: " + e.getMessage());
            cc.sendMessage("@SYSTEM command failed: " + str);
        }
    }

    private void require(String[] parts, int len, String usage) {
        if (parts.length < len)
            throw new IllegalArgumentException(usage);
    }

    private void login(ConnectedClient cc, String id, String password) {
        id = cleanId(id);
        if (!accountExists(id) || !ds.verifyUser(id, md5(password))) {
            cc.sendMessage("@AUTH_FAIL id or password is wrong.");
            return;
        }
        String nick = infoOf(id, "nick");
        if (nick.length() == 0) nick = id;
        cc.uid = id;
        cc.nick = nick;
        cc.verifyedBoolean = true;
        cc.sendMessage("@LOGIN_OK " + cc.uid + "|" + cc.nick);
        cc.sendMessage("@ME " + cc.uid + "|" + cc.nick);
        cc.getConnectionKeeper().broadcast("@AVATAR2 " + cc.uid + "|" + cc.nick + "|" + avatarOf(cc.uid));
        sendKnownAvatars(cc);
        cc.getConnectionKeeper().notifyUsers();
    }

    private synchronized void register(ConnectedClient cc, String nick, String password) {
        nick = nick.trim();
        if (nick.length() == 0 || nick.indexOf('|') >= 0 || nick.indexOf(',') >= 0 || password.trim().length() == 0) {
            cc.sendMessage("@AUTH_FAIL nickname/password invalid.");
            return;
        }
        String id = nextAccountId();
        if (!ds.addUser(id, password)) {
            cc.sendMessage("@AUTH_FAIL register failed.");
            return;
        }
        ds.addInfo(id, "nick", nick);
        cc.uid = id;
        cc.nick = nick;
        cc.verifyedBoolean = true;
        cc.sendMessage("@REGISTERED " + id + "|" + nick);
        cc.sendMessage("@LOGIN_OK " + id + "|" + nick);
        cc.sendMessage("@ME " + id + "|" + nick);
        cc.getConnectionKeeper().broadcast("@AVATAR2 " + cc.uid + "|" + cc.nick + "|" + avatarOf(cc.uid));
        cc.getConnectionKeeper().notifyUsers();
    }

    private void search(ConnectedClient cc, String id) {
        id = cleanId(id);
        if (!accountExists(id)) {
            cc.sendMessage("@SEARCH_FAIL " + id);
            return;
        }
        String nick = infoOf(id, "nick");
        if (nick.length() == 0) nick = id;
        cc.sendMessage("@SEARCH " + id + "|" + nick + "|" + isFriend(cc.uid, id));
    }

    private void setNick(ConnectedClient cc, String nick) {
        if (nick.length() == 0 || nick.indexOf('|') >= 0 || nick.indexOf(',') >= 0) {
            cc.sendMessage("@SYSTEM nickname cannot be empty or contain | or ,");
            return;
        }
        if (!isNickFree(cc, nick)) {
            cc.sendMessage("@SYSTEM nickname " + nick + " is already taken.");
            return;
        }
        String old = cc.nick;
        cc.nick = nick;
        ds.addInfo(cc.uid, "nick", nick);
        cc.verifyedBoolean = true;
        cc.sendMessage("@ME " + cc.uid + "|" + cc.nick);
        cc.sendMessage("@SYSTEM your nickname is now " + nick);
        cc.getConnectionKeeper().broadcast("@SYSTEM " + old + " changed name to " + nick);
        cc.getConnectionKeeper().broadcast("@AVATAR2 " + cc.uid + "|" + cc.nick + "|" + avatarOf(cc.uid));
        sendKnownAvatars(cc);
        cc.getConnectionKeeper().notifyUsers();
        notifyFriendsOnline(cc);
    }

    private boolean isNickFree(ConnectedClient cc, String nick) {
        LinkedList<ConnectedClient> users = cc.getConnectionKeeper().users();
        for (ConnectedClient comp : users) {
            if (comp != cc && nick.equalsIgnoreCase(comp.getNick()))
                return false;
        }
        return true;
    }

    private void privateMsg(ConnectedClient cc, String user, String msg) {
        ConnectedClient receiver = cc.getConnectionKeeper().findUser(user);
        if (receiver == null) {
            cc.sendMessage("@SYSTEM User [" + user + "] is offline, message not delivered.");
            return;
        }
        String payload = "@CHAT2 " + cc.uid + "|" + cc.nick + "|" + receiver.uid + "|" + receiver.nick + "|" + msg;
        ServerChatLog.chat(privateTarget(cc.nick, receiver.nick), cc.nick, msg);
        sendAvatar(receiver, cc);
        sendAvatar(cc, cc);
        receiver.sendMessage(payload);
        if (receiver != cc)
            cc.sendMessage(payload);
    }

    private void groupMsg(ConnectedClient cc, String csvUsers, String msg) {
        Set<ConnectedClient> receivers = new LinkedHashSet<ConnectedClient>();
        Set<String> names = new LinkedHashSet<String>();
        List<ConnectedClient> members = new ArrayList<ConnectedClient>();
        members.add(cc);
        for (String name : csvUsers.split(",")) {
            ConnectedClient receiver = cc.getConnectionKeeper().findUser(name.trim());
            if (receiver == null) {
                cc.sendMessage("@SYSTEM User [" + name.trim() + "] is offline, skipped.");
                continue;
            }
            if (receiver != cc) {
                if (!isFriend(cc.uid, receiver.uid)) {
                    cc.sendMessage("@SYSTEM " + receiver.nick + " is not your friend, skipped.");
                    continue;
                }
                if (!members.contains(receiver)) members.add(receiver);
                receivers.add(receiver);
                names.add(receiver.nick);
            }
        }
        if (receivers.isEmpty()) {
            cc.sendMessage("@SYSTEM no valid group recipients.");
            return;
        }
        Set<String> groupNames = new LinkedHashSet<String>();
        groupNames.add(cc.nick);
        groupNames.addAll(names);
        String target = "群聊(" + String.join(",", groupNames) + ")";
        String targetId = "group:" + groupId(members);
        String payload = "@CHAT2 " + cc.uid + "|" + cc.nick + "|" + targetId + "|" + target + "|" + msg;
        ServerChatLog.chat(target, cc.nick, msg);
        for (ConnectedClient receiver : receivers) {
            sendAvatar(receiver, cc);
            receiver.sendMessage(payload);
        }
        sendAvatar(cc, cc);
        cc.sendMessage(payload);
    }

    private void friend(ConnectedClient cc, String action, String target) {
        ConnectedClient online = cc.getConnectionKeeper().findUser(target);
        if (online == null) {
            cc.sendMessage("@SYSTEM user " + target + " is offline.");
            return;
        }
        if (online == cc) {
            cc.sendMessage("@SYSTEM cannot add yourself as friend.");
            return;
        }
        if ("add".equalsIgnoreCase(action)) {
            if (isFriend(cc.uid, online.uid)) {
                cc.sendMessage("@SYSTEM " + online.nick + " is already your friend.");
                return;
            }
            if (pendingFriends.remove(friendKey(online.uid, cc.uid))) {
                makeFriends(cc, online);
                return;
            }
            pendingFriends.add(friendKey(cc.uid, online.uid));
            cc.sendMessage("@SYSTEM friend request sent to " + online.nick + ".");
            online.sendMessage("@FRIEND_REQUEST " + cc.uid + "|" + cc.nick);
            return;
        }
        if ("accept".equalsIgnoreCase(action)) {
            if (!pendingFriends.remove(friendKey(online.uid, cc.uid))) {
                cc.sendMessage("@SYSTEM no pending friend request from " + online.nick + ".");
                return;
            }
            makeFriends(cc, online);
            return;
        }
        cc.sendMessage("@SYSTEM Usage: /friend add <user> or /friend accept <user>");
    }

    private String friendKey(String from, String to) {
        return from.toLowerCase() + "->" + to.toLowerCase();
    }

    private boolean isFriend(String a, String b) {
        Set<String> mine = friends.get(a.toLowerCase());
        return mine != null && mine.contains(b.toLowerCase());
    }

    private void makeFriends(ConnectedClient a, ConnectedClient b) {
        friends.computeIfAbsent(a.uid.toLowerCase(), k -> new HashSet<String>()).add(b.uid.toLowerCase());
        friends.computeIfAbsent(b.uid.toLowerCase(), k -> new HashSet<String>()).add(a.uid.toLowerCase());
        a.sendMessage("@FRIEND_ACCEPTED " + b.uid + "|" + b.nick);
        b.sendMessage("@FRIEND_ACCEPTED " + a.uid + "|" + a.nick);
    }

    private void notifyFriendsOnline(ConnectedClient online) {
        for (ConnectedClient cc : online.getConnectionKeeper().users()) {
            Set<String> mine = friends.get(cc.uid.toLowerCase());
            if (mine != null && mine.contains(online.uid.toLowerCase()) && cc != online) {
                cc.sendMessage("@SYSTEM friend " + online.nick + " is now online.");
            }
        }
    }

    private void profile(ConnectedClient cc, String[] parts) {
        if (parts.length == 1) {
            sendProfile(cc, cc.uid);
            return;
        }
        if ("view".equalsIgnoreCase(parts[1])) {
            String target = parts.length >= 3 ? parts[2].trim() : cc.uid;
            sendProfile(cc, target);
            return;
        }
        require(parts, 3, "Usage: /profile set <field>=<value> or /profile view <user>");
        if (!"set".equalsIgnoreCase(parts[1])) {
            cc.sendMessage("@SYSTEM Usage: /profile set <field>=<value> or /profile view <user>");
            return;
        }
        int eq = parts[2].indexOf('=');
        if (eq <= 0) {
            cc.sendMessage("@SYSTEM format should be <field>=<value>, e.g. /profile set city=Beijing");
            return;
        }
        String field = parts[2].substring(0, eq).trim();
        String value = parts[2].substring(eq + 1).trim();

        if (field.indexOf('|') >= 0 || field.indexOf(',') >= 0 || value.indexOf('|') >= 0
                || value.indexOf(',') >= 0) {
            cc.sendMessage("@SYSTEM profile field or value cannot contain | or ,");
            return;
        }

        ds.addInfo(cc.uid, field, value);
        if ("avatar".equalsIgnoreCase(field)) {
            cc.getConnectionKeeper().broadcast("@AVATAR2 " + cc.uid + "|" + cc.nick + "|" + value);
        }
        cc.sendMessage("@SYSTEM profile saved: " + field + "=" + value);
    }

    private void sendProfile(ConnectedClient cc, String user) {
        ConnectedClient online = cc.getConnectionKeeper().findUser(user);
        String id = online == null ? cleanId(user) : online.uid;
        String nick = online == null ? infoOf(id, "nick") : online.nick;
        if (nick.length() == 0) nick = id;
        String[] info = ds.getAllUserInfo(id);
        String visibleId = (id.equalsIgnoreCase(cc.uid) || isFriend(cc.uid, id)) ? id : "";
        cc.sendMessage("@PROFILE2 " + visibleId + "|" + nick + "|" + String.join(";", info));
    }

    private void attachment(ConnectedClient cc, String type, String target, String body) {
        int pos = body.indexOf('|');
        if (pos <= 0) {
            cc.sendMessage("@SYSTEM invalid attachment format.");
            return;
        }
        ConnectedClient receiver = cc.getConnectionKeeper().findUser(target);
        if (receiver == null) {
            cc.sendMessage("@SYSTEM user " + target + " is offline, attachment not sent.");
            return;
        }
        String payload = ("image".equals(type) ? "@IMAGE " : "@FILE ") + cc.nick + "|" + body;
        ServerChatLog.attachment(privateTarget(cc.nick, receiver.nick), cc.nick, type, body.substring(0, pos));
        sendAvatar(receiver, cc);
        sendAvatar(cc, cc);
        receiver.sendMessage(payload);
        if (receiver != cc)
            cc.sendMessage(payload);
    }

    private void stats(ConnectedClient cc) {
        long runningTime = (System.currentTimeMillis() - MainServer.uptime) / 1000;
        cc.sendMessage("@SYSTEM server uptime: " + runningTime + " seconds, total connects: " + MainServer.connects);
    }

    public void setDataSource(DataSource ds) {
        this.ds = ds;
    }

    private String privateTarget(String a, String b) {
        return a.compareToIgnoreCase(b) <= 0 ? "私聊(" + a + "," + b + ")" : "私聊(" + b + "," + a + ")";
    }

    private void sendKnownAvatars(ConnectedClient cc) {
        for (ConnectedClient user : cc.getConnectionKeeper().users()) {
            sendAvatar(cc, user);
        }
    }

    private void sendAvatar(ConnectedClient cc, ConnectedClient user) {
        cc.sendMessage("@AVATAR2 " + user.uid + "|" + user.nick + "|" + avatarOf(user.uid));
    }

    private String groupId(List<ConnectedClient> members) {
        List<String> ids = new ArrayList<String>();
        for (ConnectedClient member : members) ids.add(member.uid);
        Collections.sort(ids, String.CASE_INSENSITIVE_ORDER);
        return String.join(",", ids);
    }

    private String avatarOf(String user) {
        if (ds == null) return "";
        for (String info : ds.getAllUserInfo(user)) {
            if (info.startsWith("avatar=")) return info.substring("avatar=".length());
        }
        return "";
    }

    private boolean accountExists(String id) {
        for (String user : ds.getUserList()) {
            if (user.equalsIgnoreCase(id)) return true;
        }
        return false;
    }

    private String nextAccountId() {
        int n = 100001;
        while (accountExists("u" + n)) n++;
        return "u" + n;
    }

    private String cleanId(String id) {
        return id == null ? "" : id.trim();
    }

    private String infoOf(String id, String field) {
        for (String info : ds.getAllUserInfo(id)) {
            if (info.startsWith(field + "=")) return info.substring(field.length() + 1);
        }
        return "";
    }

    private String md5(String str) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] bytes = md.digest(str.getBytes("UTF-8"));
            StringBuilder out = new StringBuilder();
            for (byte b : bytes) out.append(b);
            return out.toString();
        } catch (Exception e) {
            return "";
        }
    }
}
