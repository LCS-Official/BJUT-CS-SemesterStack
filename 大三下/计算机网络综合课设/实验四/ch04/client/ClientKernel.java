package com.cncd.ch04.client;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.text.SimpleDateFormat;
import java.util.Base64;
import java.util.Date;
import java.util.LinkedList;
import javax.imageio.ImageIO;
import javax.swing.SwingUtilities;
import java.awt.image.BufferedImage;

public class ClientKernel {
    public static final int CONNECT_TIMEOUT_MS = 8000;
    public static final char MSGENDCHAR = 0xff;
    public static final char EXIT = 0xFE;
    public static final char NICK = 0xFD;
    public static final char COMMAND = 0xFD;

    // 最大文件大小限制：2MB
    public static final int MAX_FILE_SIZE = 2 * 1024 * 1024;
    // 下载目录
    public static String DOWNLOAD_DIR = System.getProperty("user.home")
            + System.getProperty("file.separator") + ".mihalychat"
            + System.getProperty("file.separator") + "downloads";
    public static void setDownloadDir(String dir) {
        DOWNLOAD_DIR = dir;
    }
    public static String getDownloadDir() {
        return DOWNLOAD_DIR;
    }

    private String serverAd;
    private int port;
    private Socket sock;
    private boolean isConnected = false;
    private boolean dropMe = false;
    private LinkedList<ChatClient> clients;
    public String nick;
    public boolean printMsg = true;
    private ClientMsgSender cms;
    private ClientMsgListener cml;

    // 连接状态监听器
    private ConnectionListener connectionListener;

    public interface ConnectionListener {
        void onConnected();
        void onConnectFailed(String reason);
        void onDisconnected(String reason);
        void onError(String error);
    }

    public ClientKernel(String server, int port) {
        this(server, port, null);
    }

    public ClientKernel(String server, int port, ConnectionListener listener) {
        this.port = port;
        nick = "" + port;
        serverAd = server;
        connectionListener = listener;
        clients = new LinkedList<ChatClient>();
        connect();
        if(isConnected) {
            cms = new ClientMsgSender(this, sock);
            cml = new ClientMsgListener(this, sock);
        }
    }

    public void connect() {
        try {
            dropMe = false;
            sock = new Socket();
            sock.connect(new InetSocketAddress(serverAd, port), CONNECT_TIMEOUT_MS);
            sock.setTcpNoDelay(true);
            isConnected = true;
            notifyConnected();
        } catch(IOException ioe ) {
            isConnected = false;
            notifyConnectFailed(ioe.getMessage());
            ioe.printStackTrace();
        }
    }

    public void setConnectionListener(ConnectionListener listener) {
        this.connectionListener = listener;
    }

    private void notifyConnected() {
        if(connectionListener != null) {
            SwingUtilities.invokeLater(() -> connectionListener.onConnected());
        }
    }

    private void notifyConnectFailed(String reason) {
        if(connectionListener != null) {
            SwingUtilities.invokeLater(() -> connectionListener.onConnectFailed(reason));
        }
    }

    private void notifyDisconnected(String reason) {
        if(connectionListener != null) {
            SwingUtilities.invokeLater(() -> connectionListener.onDisconnected(reason));
        }
    }

    private void notifyError(String error) {
        if(connectionListener != null) {
            SwingUtilities.invokeLater(() -> connectionListener.onError(error));
        }
    }

    public int getPort() {
        return port;
    }

    public boolean setNick(String nick) {
        if(nick == null || nick.trim().length() == 0) return false;
        this.nick = nick.trim();
        sendCommand("nick " + this.nick);
        return true;
    }

    public int getLocalPort() {
        return sock != null ? sock.getLocalPort() : -1;
    }

    public void dropMe() {
        System.out.println("Drop ME!!!");
        if (cms != null) cms.drop();
        if (cml != null) cml.drop();
        dropMe = true;
        int waitCount = 0;
        while((cml != null && !cml.hasStoped() || cms != null && !cms.hasStoped()) && waitCount < 50) {
            pause(100);
            waitCount++;
        }
        closeSocketQuietly();
        isConnected = false;
        notifyDisconnected("主动断开连接");
    }

    void connectionLost(String reason) {
        if(dropMe || !isConnected) return;
        dropMe = true;
        if (cms != null) cms.drop();
        if (cml != null) cml.drop();
        closeSocketQuietly();
        isConnected = false;
        notifyDisconnected(reason == null || reason.length() == 0 ? "连接已断开" : reason);
    }

    private void closeSocketQuietly() {
        try {
            if (sock != null && !sock.isClosed()) {
                sock.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void sendMessage(String str) {
        if(!dropMe && isConnected && cms != null) {
            if(str.length() == 0) return;
            if(str.charAt(0) == '/')
                cms.addMessage(str.substring(1));
            else cms.addMessage(str);
        } else if(!isConnected) {
            notifyError("未连接到服务器，消息未发送");
        }
    }

    public void sendCommand(String command) {
        if(!dropMe && isConnected && cms != null) {
            cms.addMessage(command.startsWith("/") ? command.substring(1) : command);
        } else if(!isConnected) {
            notifyError("未连接到服务器，命令未发送");
        }
    }

    public void addClient(ChatClient c) {
        clients.add(c);
    }

    public void removeClient(ChatClient c) {
        clients.remove(c);
    }

    public void pause(int time) {
        try {
            Thread.sleep(time);
        } catch(Exception e) {}
    }

    public synchronized void storeMsg(String str) {
        if(str.startsWith("@USERS ")) {
            updateUsers(str.substring(7));
        } else if(str.startsWith("@LOGIN_OK ")) {
            String[] parts = str.substring(10).split("\\|", 2);
            if(parts.length == 2) loginOk(parts[0], parts[1]);
        } else if(str.startsWith("@REGISTERED ")) {
            String[] parts = str.substring(12).split("\\|", 2);
            if(parts.length == 2) registered(parts[0], parts[1]);
        } else if(str.startsWith("@AUTH_FAIL ")) {
            authFailed(str.substring(11));
        } else if(str.startsWith("@SEARCH ")) {
            String[] parts = str.substring(8).split("\\|", 3);
            if(parts.length == 3) searchResult(parts[0], parts[1], Boolean.parseBoolean(parts[2]));
        } else if(str.startsWith("@SEARCH_FAIL ")) {
            searchFailed(str.substring(13));
        } else if(str.startsWith("@ME ")) {
            String[] parts = str.substring(4).split("\\|", 2);
            if(parts.length == 2) setSelf(parts[0], parts[1]);
        } else if(str.startsWith("@SYSTEM ")) {
            addMsg("<div class='system'>系统：" + escape(str.substring(8)) + "</div>");
        } else if(str.startsWith("@AVATAR2 ")) {
            String[] parts = str.substring(9).split("\\|", 3);
            if(parts.length == 3) {
                setUserAvatar(parts[0], parts[1], parts[2]);
            }
        } else if(str.startsWith("@AVATAR ")) {
            String[] parts = str.substring(8).split("\\|", 2);
            if(parts.length == 2) {
                setUserAvatar(parts[0], parts[1]);
            }
        } else if(str.startsWith("@CHAT2 ")) {
            String[] parts = str.substring(7).split("\\|", 5);
            if(parts.length == 5) {
                addChatMsg(parts[0], parts[1], parts[2], parts[3], parts[4]);
            }
        } else if(str.startsWith("@CHAT ")) {
            String[] parts = str.substring(6).split("\\|", 3);
            if(parts.length == 3) {
                addChatMsg(parts[0], parts[1], parts[2], null);
            }
        } else if(str.startsWith("@PROFILE ")) {
            String[] parts = str.substring(9).split("\\|", 2);
            if(parts.length == 2) {
                showProfile(parts[0], parts[1]);
            }
        } else if(str.startsWith("@PROFILE2 ")) {
            String[] parts = str.substring(10).split("\\|", 3);
            if(parts.length == 3) {
                showProfile(parts[0], parts[1], parts[2]);
            }
        } else if(str.startsWith("@FRIEND_REQUEST ") || str.startsWith("@FRIEND_ACCEPTED ")) {
            addMsg(str);
        } else if(str.startsWith("@FILE ") || str.startsWith("@IMAGE ")) {
            handleAttachment(str.startsWith("@IMAGE "), str.substring(str.indexOf(' ') + 1));
        } else {
            addMsg(escape(str));
        }
    }

    private void addMsg(String html) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.addMsg(html);
            }
        }
    }

    private void addChatMsg(String sender, String target, String message, String html) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.addChatMsg(sender, target, message, html);
            }
        }
    }

    private void addAttachmentMsg(String sender, String fileName, boolean image, String html) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.addAttachmentMsg(sender, fileName, image, html);
            }
        }
    }

    private void setUserAvatar(String user, String avatar) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.setUserAvatar(user, avatar);
            }
        }
    }

    private void setUserAvatar(String uid, String nick, String avatar) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.setUserAvatar(uid, nick, avatar);
            }
        }
    }

    private void setSelf(String uid, String nick) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.setSelf(uid, nick);
            }
        }
    }

    private void addChatMsg(String senderUid, String senderNick, String targetId, String targetTitle, String message) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.addChatMsg(senderUid, senderNick, targetId, targetTitle, message);
            }
        }
    }

    private void showProfile(String user, String rawProfile) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.showProfile(user, rawProfile);
            }
        }
    }

    private void showProfile(String visibleUid, String nick, String rawProfile) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.showProfile(visibleUid, nick, rawProfile);
            }
        }
    }

    private void loginOk(String uid, String nick) {
        for(ChatClient client : clients) if(client != null) client.loginOk(uid, nick);
    }

    private void registered(String uid, String nick) {
        for(ChatClient client : clients) if(client != null) client.registered(uid, nick);
    }

    private void authFailed(String reason) {
        for(ChatClient client : clients) if(client != null) client.authFailed(reason);
    }

    private void searchResult(String uid, String nick, boolean friend) {
        for(ChatClient client : clients) if(client != null) client.searchResult(uid, nick, friend);
    }

    private void searchFailed(String id) {
        for(ChatClient client : clients) if(client != null) client.searchFailed(id);
    }

    private void updateUsers(String csv) {
        String[] users = csv.length() == 0 ? new String[0] : csv.split(",");
        for(ChatClient client : clients) {
            if(client != null) {
                client.updateUsers(users);
            }
        }
    }

    private void notifyChat(String sender, String target, String message) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.noteChat(sender, target, message);
            }
        }
    }

    private void notifyAttachment(String sender, String fileName, boolean image) {
        for(ChatClient client : clients) {
            if(client != null) {
                client.noteAttachment(sender, fileName, image);
            }
        }
    }

    private String escape(String str) {
        if(str == null) return "";
        return str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }

    private String senderHtml(String sender, boolean mine) {
        if(mine) return "我";
        return "<a href=\"user:" + escape(sender) + "\">" + avatarText(sender) + "</a> " + escape(sender);
    }

    private String avatarText(String sender) {
        if(sender == null || sender.length() == 0) return "人";
        return escape(sender.substring(0, 1).toUpperCase());
    }

    private String profileHtml(String user, String rawProfile) {
        StringBuilder html = new StringBuilder();
        html.append("<div class='profile-card'><div class='profile-title'>个人资料 - ")
                .append(escape(user)).append("</div>");
        if(rawProfile == null || rawProfile.trim().length() == 0 || rawProfile.equals("暂无资料")) {
            html.append("<font color=\"#888888\">暂无资料</font>");
        } else {
            String[] items = rawProfile.split(";");
            for(String item : items) {
                if(item.trim().length() == 0) continue;
                String[] kv = item.split("=", 2);
                html.append("<br><font color=\"#666666\">")
                        .append(escape(profileFieldLabel(kv[0]))).append("：</font>");
                html.append(escape(kv.length == 2 ? kv[1] : ""));
            }
        }
        html.append("</div>");
        return html.toString();
    }

    private String profileFieldLabel(String field) {
        if(field == null) return "";
        if(field.equals("avatar")) return "头像";
        if(field.equals("city")) return "城市";
        if(field.equals("phone")) return "电话";
        if(field.equals("email")) return "邮箱";
        if(field.equals("intro")) return "个人签名";
        return field;
    }

    private void handleAttachment(boolean image, String payload) {
        try {
            String[] parts = payload.split("\\|", 3);
            if(parts.length != 3) {
                addMsg("<font color=\"#cc0000\">附件格式错误</font>");
                return;
            }

            String sender = parts[0];
            String fileName = new File(parts[1]).getName();
            if(fileName.trim().length() == 0) fileName = image ? "image" : "file";
            String base64Data = parts[2];

            byte[] fileData = Base64.getMimeDecoder().decode(base64Data.trim());
            if(fileData.length > MAX_FILE_SIZE) {
                addMsg("<font color=\"#cc0000\">文件过大（" + (fileData.length / 1024)
                        + "KB），最大支持 " + (MAX_FILE_SIZE / 1024 / 1024) + "MB</font>");
                return;
            }

            File dir = new File(DOWNLOAD_DIR);
            if(!dir.exists()) {
                dir.mkdirs();
            }

            // 处理文件名冲突
            File file = new File(dir, fileName);
            int counter = 1;
            String nameWithoutExt = fileName;
            String ext = "";
            int dotIndex = fileName.lastIndexOf('.');
            if(dotIndex > 0) {
                nameWithoutExt = fileName.substring(0, dotIndex);
                ext = fileName.substring(dotIndex);
            }
            while(file.exists()) {
                file = new File(dir, nameWithoutExt + "_" + counter + ext);
                counter++;
            }

            try(FileOutputStream out = new FileOutputStream(file)) {
                out.write(fileData);
            }

            String text = attachmentHtml(sender, file, fileData.length, image);
            addAttachmentMsg(sender, file.getName(), image, text);

        } catch(IllegalArgumentException e) {
            addMsg("<font color=\"#cc0000\">附件接收失败：Base64解码错误</font>");
        } catch(Exception e) {
            addMsg("<font color=\"#cc0000\">附件接收失败：" + escape(e.getMessage()) + "</font>");
            e.printStackTrace();
        }
    }

    private String attachmentHtml(String sender, File file, int size, boolean image) {
        StringBuilder html = new StringBuilder();
        boolean mine = nick != null && sender.equalsIgnoreCase(nick);
        String uri = file.toURI().toString();
        html.append("<div class='msg-wrapper ").append(mine ? "self" : "other").append("'>")
                .append("<div class='msg-info'>").append(senderHtml(sender, mine))
                .append(image ? " 发送图片" : " 发送文件").append("</div>")
                .append("<div class='msg-bubble'>");
        if(image) {
            html.append(imagePreviewTag(file))
                    .append("<br><b>").append(escape(file.getName())).append("</b>")
                    .append(" <font color=\"#777777\">").append(formatSize(size)).append("</font>")
                    .append("<br><a href=\"").append(uri).append("\">打开图片</a>");
        } else {
            html.append("📎 <b>").append(escape(file.getName())).append("</b>")
                    .append("<br><font color=\"#777777\">").append(formatSize(size)).append("</font>")
                    .append(" &nbsp; <a href=\"").append(uri).append("\">打开文件</a>")
                    .append(filePreview(file));
        }
        html.append("</div></div>");
        return html.toString();
    }

    private String imagePreviewTag(File file) {
        String uri = file.toURI().toString();
        int width = 220;
        int height = -1;
        try {
            BufferedImage img = ImageIO.read(file);
            if(img != null && img.getWidth() > 0 && img.getHeight() > 0) {
                width = img.getWidth();
                height = img.getHeight();
                if(width > 240) {
                    height = Math.max(1, height * 240 / width);
                    width = 240;
                }
                if(height > 180) {
                    width = Math.max(1, width * 180 / height);
                    height = 180;
                }
            }
        } catch(IOException ignored) {}
        String size = height > 0
                ? " width=\"" + width + "\" height=\"" + height + "\""
                : " width=\"" + width + "\"";
        return "<a href=\"" + uri + "\"><img src=\"" + uri + "\"" + size + "></a>";
    }

    private String filePreview(File file) {
        if(!isPreviewableText(file) || file.length() > 64 * 1024) return "";
        try {
            StringBuilder preview = new StringBuilder("<br><font color=\"#3157a5\">文本预览</font><br><font face=\"monospaced\" color=\"#333333\">");
            int count = 0;
            for(String line : Files.readAllLines(file.toPath(), StandardCharsets.UTF_8)) {
                if(count++ >= 6) break;
                preview.append(escape(line)).append("<br>");
            }
            if(count >= 6) preview.append("...");
            preview.append("</font>");
            return preview.toString();
        } catch(IOException ignored) {
            return "";
        }
    }

    private boolean isPreviewableText(File file) {
        String name = file.getName().toLowerCase();
        return name.endsWith(".txt") || name.endsWith(".md") || name.endsWith(".csv")
                || name.endsWith(".json") || name.endsWith(".xml") || name.endsWith(".html")
                || name.endsWith(".css") || name.endsWith(".js") || name.endsWith(".java")
                || name.endsWith(".log");
    }

    private String formatSize(int bytes) {
        long kb = Math.max(1, (bytes + 1023L) / 1024L);
        if(kb < 1024) return kb + "KB";
        return String.format("%.1fMB", bytes / 1024.0 / 1024.0);
    }

    public boolean isConnected() {
        return isConnected && sock != null && !sock.isClosed();
    }

    public String getServerAddress() {
        return serverAd;
    }

    public int getServerPort() {
        return port;
    }

    public static void main(String args[]) {
        new ClientKernel("localhost", 1984);
    }
}

class ClientMsgSender extends Thread {
    private Socket s;
    private ClientKernel ck;
    private LinkedList<String> msgList;
    private boolean running = true;
    private boolean hasStoped = false;

    public ClientMsgSender(ClientKernel ck, Socket s) {
        this.ck = ck;
        this.s  = s;
        msgList = new LinkedList<String>();
        start();
    }

    public synchronized void addMessage(String msg) {
        msgList.addLast(msg);
    }

    public void drop() {
        running = false;
    }

    public boolean hasStoped() {
        return hasStoped;
    }

    public void run() {
        try {
            DataOutputStream dataOut = new DataOutputStream(s.getOutputStream());
            while(running) {
                while(msgList.size()>0) {
                    String msg = msgList.removeFirst();
                    if (ck.printMsg) {
                        System.out.println("ClientMsgSender.send: " + msg);
                    }
                    dataOut.write(msg.getBytes(StandardCharsets.UTF_8));
                    dataOut.write(ClientKernel.MSGENDCHAR);
                    dataOut.flush();
                }
                sleep(10);
            }
            dataOut.write(ClientKernel.EXIT);
            dataOut.close();
        } catch(SocketException se) {
            if (ck.printMsg) {
                System.out.println("ClientMsgSender: Socket closed");
            }
        } catch(Exception ioe) {
            ioe.printStackTrace();
        } finally {
            hasStoped = true;
        }
    }
}

class ClientMsgListener extends Thread {
    private ClientKernel ck;
    private Socket s;
    private boolean running = true;
    private boolean hasStoped = false;

    public ClientMsgListener(ClientKernel ck, Socket s) {
        this.ck = ck;
        this.s  = s;
        start();
    }

    public void drop() {
        running = false;
    }

    public boolean hasStoped() {
        return hasStoped;
    }

    public void run() {
        try {
            BufferedInputStream buffIn = new BufferedInputStream(s.getInputStream());
            DataInputStream dataIn = new DataInputStream(buffIn);
            while(running) {
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                int c;
                while( (c=dataIn.read()) != ClientKernel.MSGENDCHAR) {
                    if(c == -1) {
                        throw new IOException("连接已断开");
                    }
                    bytes.write(c);
                }
                String msg = new String(bytes.toByteArray(), StandardCharsets.UTF_8);
                if (ck.printMsg) {
                    System.out.println("ClientMsgListener.recv: " + msg);
                }
                ck.storeMsg(msg);
            }
            dataIn.close();
            buffIn.close();
        } catch(SocketException se) {
            if (ck.printMsg) {
                System.out.println("ClientMsgListener: Socket closed");
            }
            if(running) ck.connectionLost("连接已断开");
        } catch(IOException ioe) {
            if (ck.printMsg) {
                System.out.println("ClientMsgListener: " + ioe.getMessage());
            }
            if(running) ck.connectionLost(ioe.getMessage());
        } finally {
            hasStoped = true;
        }
    }
}
