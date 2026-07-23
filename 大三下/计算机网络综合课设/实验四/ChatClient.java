package com.cncd.ch04.client;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.awt.event.*;
import java.io.File;
import java.nio.file.Files;
import java.util.Base64;

/**
 * 聊天客户端主界面 - 重构版
 * 视觉风格：接近 QQ/微信，清晰区分消息类型
 *
 * @author Client UI Team
 */
public class ChatClient extends JFrame implements KeyListener, ActionListener, FocusListener {
    public static final String appName = "Chat Tool";
    public static final String serverText = "127.0.0.1";
    public static final String portText = "3500";
    public static final String nickText = "YourName";

    // ==================== UI 组件 ====================
    // ---- 顶部状态栏 ----
    private JPanel topStatusPanel;
    private JLabel statusDot;
    private JLabel statusLabel;
    private JLabel serverInfoLabel;
    private JLabel nickInfoLabel;

    // ---- 连接面板 (North) ----
    private JPanel northPanel;
    private JTextField txtHost, txtPort, txtNick;
    private JButton buttonConnect;

    // ---- 主内容区域 (Center) ----
    private JSplitPane mainSplitPane;

    // ---- 左侧联系人面板 ----
    private JPanel leftPanel;
    private JLabel onlineTitleLabel;
    private JList<String> userList;
    private DefaultListModel<String> userModel;
    private JScrollPane userScrollPane;

    // ---- 右侧聊天主面板 ----
    private JPanel chatMainPanel;
    private JPanel chatHeaderPanel;
    private JLabel chatTargetLabel;
    private JLabel chatTargetStatusLabel;
    private JButton buttonFriend;

    // ---- 聊天记录区 ----
    private JScrollPane chatScrollPane;
    private ClientHistory historyWindow;

    // ---- 底部输入区 ----
    private JPanel southPanel;
    private JPanel inputPanel;
    private JTextField msgWindow;
    private JButton buttonSend;
    private JPanel toolPanel;
    private JCheckBox privateChat;
    private JTextField txtProfileField, txtProfileValue;
    private JButton buttonProfileSave, buttonProfileView, buttonFile, buttonImage;
    private JButton buttonAddFriend;

    // ==================== 业务组件 ====================
    private ClientKernel ck;
    private String lastMsg = "";

    // ==================== 颜色常量 ====================
    private static final Color COLOR_ONLINE = new Color(46, 194, 126);
    private static final Color COLOR_OFFLINE = new Color(190, 190, 190);
    private static final Color COLOR_BG_MAIN = new Color(247, 247, 247);
    private static final Color COLOR_BORDER = new Color(220, 220, 220);
    private static final Color COLOR_HEADER_BG = new Color(235, 237, 240);
    private static final Color COLOR_DISCONNECT_BG = new Color(220, 80, 80);
    private static final Color COLOR_DISCONNECT_HOVER = new Color(200, 60, 60);
    private static final Color COLOR_DISCONNECT_PRESSED = new Color(180, 40, 40);
    private static final Font FONT_MAIN = new Font("微软雅黑", Font.PLAIN, 14);
    private static final Font FONT_TITLE = new Font("微软雅黑", Font.BOLD, 14);
    private static final Font FONT_SMALL = new Font("微软雅黑", Font.PLAIN, 12);

    // 绿色按钮颜色
    private static final Color GREEN_BTN_BG = new Color(46, 194, 126);
    private static final Color GREEN_BTN_HOVER = new Color(52, 210, 140);
    private static final Color GREEN_BTN_PRESSED = new Color(40, 175, 110);

    public ChatClient() {
        uiInit();
        txtHost.setText("127.0.0.1");
        txtPort.setText("3500");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
    }

    public void uiInit() {
        // ---------- 窗口基本设置 ----------
        setTitle(appName);
        setSize(900, 680);
        setLocationRelativeTo(null);
        setMinimumSize(new Dimension(800, 500));
        getContentPane().setBackground(COLOR_BG_MAIN);
        setLayout(new BorderLayout(0, 0));

        // ============================================
        // 1. 顶部状态栏 (North 最上方)
        // ============================================
        topStatusPanel = createStatusBar();
        add(topStatusPanel, BorderLayout.NORTH);

        // ============================================
        // 2. 连接设置面板 (位于状态栏下方)
        // ============================================
        northPanel = createConnectionPanel();
        add(northPanel, BorderLayout.BEFORE_FIRST_LINE);

        // ============================================
        // 3. 主内容区域 (Center) - 使用 JSplitPane 分割
        // ============================================
        mainSplitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        mainSplitPane.setDividerLocation(180);
        mainSplitPane.setDividerSize(2);
        mainSplitPane.setBorder(null);

        // ---- 左侧：联系人列表 ----
        leftPanel = createContactPanel();
        mainSplitPane.setLeftComponent(leftPanel);

        // ---- 右侧：聊天主区域 ----
        chatMainPanel = createChatMainPanel();
        mainSplitPane.setRightComponent(chatMainPanel);

        add(mainSplitPane, BorderLayout.CENTER);

        // ============================================
        // 4. 底部输入区域 (South)
        // ============================================
        southPanel = createInputPanel();
        add(southPanel, BorderLayout.SOUTH);

        // 默认状态
        setConnectionStatus(false, "未连接");
    }

    /**
     * 创建自定义绿色按钮 - 确保颜色正确显示
     */
    private JButton createGreenButton(String text) {
        JButton btn = new JButton(text) {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

                if (getModel().isPressed()) {
                    g2.setColor(GREEN_BTN_PRESSED);
                } else if (getModel().isRollover()) {
                    g2.setColor(GREEN_BTN_HOVER);
                } else {
                    g2.setColor(GREEN_BTN_BG);
                }
                g2.fillRoundRect(0, 0, getWidth(), getHeight(), 6, 6);
                g2.dispose();
                super.paintComponent(g);
            }

            @Override
            protected void paintBorder(Graphics g) {
                // 不画边框
            }
        };
        btn.setFont(FONT_MAIN);
        btn.setForeground(Color.WHITE);
        btn.setOpaque(false);
        btn.setContentAreaFilled(false);
        btn.setBorder(BorderFactory.createEmptyBorder(6, 20, 6, 20));
        btn.setFocusPainted(false);
        btn.setCursor(new Cursor(Cursor.HAND_CURSOR));
        return btn;
    }

    /**
     * 创建自定义断开按钮 - 红色
     */
    private JButton createDisconnectButton(String text) {
        JButton btn = new JButton(text) {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

                if (getModel().isPressed()) {
                    g2.setColor(COLOR_DISCONNECT_PRESSED);
                } else if (getModel().isRollover()) {
                    g2.setColor(COLOR_DISCONNECT_HOVER);
                } else {
                    g2.setColor(COLOR_DISCONNECT_BG);
                }
                g2.fillRoundRect(0, 0, getWidth(), getHeight(), 6, 6);
                g2.dispose();
                super.paintComponent(g);
            }

            @Override
            protected void paintBorder(Graphics g) {
                // 不画边框
            }
        };
        btn.setFont(FONT_MAIN);
        btn.setForeground(Color.WHITE);
        btn.setOpaque(false);
        btn.setContentAreaFilled(false);
        btn.setBorder(BorderFactory.createEmptyBorder(6, 20, 6, 20));
        btn.setFocusPainted(false);
        btn.setCursor(new Cursor(Cursor.HAND_CURSOR));
        return btn;
    }

    /**
     * 创建自定义灰色按钮
     */
    private JButton createGrayButton(String text) {
        JButton btn = new JButton(text) {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(new Color(240, 240, 240));
                g2.fillRoundRect(0, 0, getWidth(), getHeight(), 4, 4);
                g2.dispose();
                super.paintComponent(g);
            }
        };
        btn.setFont(FONT_SMALL);
        btn.setForeground(Color.BLACK);
        btn.setOpaque(false);
        btn.setContentAreaFilled(false);
        btn.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(COLOR_BORDER, 1, true),
                BorderFactory.createEmptyBorder(2, 10, 2, 10)
        ));
        btn.setFocusPainted(false);
        btn.setCursor(new Cursor(Cursor.HAND_CURSOR));
        return btn;
    }

    // ================================================
    //  1. 顶部状态栏
    // ================================================
    private JPanel createStatusBar() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT, 15, 6));
        panel.setBackground(new Color(240, 242, 245));
        panel.setBorder(BorderFactory.createMatteBorder(0, 0, 1, 0, COLOR_BORDER));

        statusDot = new JLabel("●");
        statusDot.setFont(new Font("SansSerif", Font.PLAIN, 18));
        statusDot.setForeground(COLOR_OFFLINE);
        panel.add(statusDot);

        statusLabel = new JLabel("未连接");
        statusLabel.setFont(FONT_MAIN);
        statusLabel.setForeground(new Color(80, 80, 80));
        panel.add(statusLabel);

        panel.add(new JSeparator(SwingConstants.VERTICAL) {{
            setPreferredSize(new Dimension(1, 20));
        }});

        serverInfoLabel = new JLabel("服务器: 未连接");
        serverInfoLabel.setFont(FONT_SMALL);
        serverInfoLabel.setForeground(new Color(120, 120, 120));
        panel.add(serverInfoLabel);

        nickInfoLabel = new JLabel("昵称: --");
        nickInfoLabel.setFont(FONT_SMALL);
        nickInfoLabel.setForeground(new Color(120, 120, 120));
        panel.add(nickInfoLabel);

        panel.add(Box.createHorizontalGlue());

        buttonFriend = createGreenButton("＋ 加好友");
        buttonFriend.setFont(FONT_SMALL);
        buttonFriend.setBorder(BorderFactory.createEmptyBorder(4, 12, 4, 12));
        buttonFriend.addActionListener(this);
        panel.add(buttonFriend);

        return panel;
    }

    private void setConnectionStatus(boolean connected, String text) {
        if (connected) {
            statusDot.setForeground(COLOR_ONLINE);
            statusLabel.setText("● " + text);
            statusLabel.setForeground(COLOR_ONLINE);
            buttonConnect.setText("断开");
            buttonConnect.setEnabled(true);
            buttonConnect.setForeground(Color.WHITE);
            buttonConnect = replaceButton(buttonConnect, true);
            txtHost.setEnabled(false);
            txtPort.setEnabled(false);
            txtNick.setEnabled(false);
        } else {
            statusDot.setForeground(COLOR_OFFLINE);
            statusLabel.setText("○ " + text);
            statusLabel.setForeground(new Color(80, 80, 80));
            buttonConnect.setText("连接");
            buttonConnect.setEnabled(true);
            buttonConnect.setForeground(Color.WHITE);
            buttonConnect = replaceButton(buttonConnect, false);
            txtHost.setEnabled(true);
            txtPort.setEnabled(true);
            txtNick.setEnabled(true);
        }
        northPanel.revalidate();
        northPanel.repaint();
    }

    private JButton replaceButton(JButton oldBtn, boolean isDisconnect) {
        JButton newBtn;
        if (isDisconnect) {
            newBtn = createDisconnectButton("断开");
        } else {
            newBtn = createGreenButton("连接");
        }
        newBtn.addActionListener(this);

        Container parent = oldBtn.getParent();
        if (parent != null) {
            GridBagLayout layout = (GridBagLayout) parent.getLayout();
            GridBagConstraints gbc = layout.getConstraints(oldBtn);
            parent.remove(oldBtn);
            parent.add(newBtn, gbc);
        }
        return newBtn;
    }

    private void updateStatusBar(String server, String nick) {
        serverInfoLabel.setText("服务器: " + server + ":" + txtPort.getText());
        nickInfoLabel.setText("昵称: " + (nick != null && !nick.isEmpty() ? nick : "--"));
    }

    // ================================================
    //  2. 连接设置面板
    // ================================================
    private JPanel createConnectionPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(Color.WHITE);
        panel.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createMatteBorder(0, 0, 1, 0, COLOR_BORDER),
                BorderFactory.createEmptyBorder(8, 15, 8, 15)
        ));
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(0, 5, 0, 5);
        gbc.fill = GridBagConstraints.HORIZONTAL;

        gbc.gridx = 0; gbc.gridy = 0;
        panel.add(new JLabel("服务器:"), gbc);
        gbc.gridx = 1;
        txtHost = new JTextField(serverText, 12);
        txtHost.setFont(FONT_MAIN);
        txtHost.setBorder(BorderFactory.createCompoundBorder(
                new LineBorder(COLOR_BORDER, 1, true),
                BorderFactory.createEmptyBorder(4, 8, 4, 8)
        ));
        txtHost.addKeyListener(this);
        txtHost.addFocusListener(this);
        panel.add(txtHost, gbc);

        gbc.gridx = 2;
        panel.add(new JLabel("端口:"), gbc);
        gbc.gridx = 3;
        txtPort = new JTextField(portText, 6);
        txtPort.setFont(FONT_MAIN);
        txtPort.setBorder(BorderFactory.createCompoundBorder(
                new LineBorder(COLOR_BORDER, 1, true),
                BorderFactory.createEmptyBorder(4, 8, 4, 8)
        ));
        txtPort.addKeyListener(this);
        txtPort.addFocusListener(this);
        panel.add(txtPort, gbc);

        gbc.gridx = 4;
        panel.add(new JLabel("昵称:"), gbc);
        gbc.gridx = 5;
        txtNick = new JTextField(nickText, 10);
        txtNick.setFont(FONT_MAIN);
        txtNick.setBorder(BorderFactory.createCompoundBorder(
                new LineBorder(COLOR_BORDER, 1, true),
                BorderFactory.createEmptyBorder(4, 8, 4, 8)
        ));
        txtNick.addKeyListener(this);
        txtNick.addFocusListener(this);
        panel.add(txtNick, gbc);

        gbc.gridx = 6;
        gbc.weightx = 0;
        buttonConnect = createGreenButton("连接");
        buttonConnect.addActionListener(this);
        panel.add(buttonConnect, gbc);

        gbc.gridx = 7;
        gbc.weightx = 1;
        panel.add(new JLabel(), gbc);

        return panel;
    }

    // ================================================
    //  3. 左侧联系人面板
    // ================================================
    private JPanel createContactPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(Color.WHITE);
        panel.setBorder(BorderFactory.createMatteBorder(0, 0, 0, 1, COLOR_BORDER));

        onlineTitleLabel = new JLabel("👥 在线用户 (0)");
        onlineTitleLabel.setFont(FONT_TITLE);
        onlineTitleLabel.setBorder(BorderFactory.createEmptyBorder(12, 15, 10, 10));
        onlineTitleLabel.setBackground(new Color(247, 247, 247));
        onlineTitleLabel.setOpaque(true);
        panel.add(onlineTitleLabel, BorderLayout.NORTH);

        userModel = new DefaultListModel<>();
        userList = new JList<>(userModel);
        userList.setFont(FONT_MAIN);
        userList.setBackground(Color.WHITE);
        userList.setSelectionBackground(new Color(230, 240, 255));
        userList.setBorder(BorderFactory.createEmptyBorder(4, 4, 4, 4));
        userList.setFixedCellHeight(32);
        userList.setCellRenderer(new UserListCellRenderer());

        userScrollPane = new JScrollPane(userList);
        userScrollPane.setBorder(null);
        userScrollPane.getVerticalScrollBar().setUnitIncrement(16);
        panel.add(userScrollPane, BorderLayout.CENTER);

        JLabel hintLabel = new JLabel("单击选中用户后可私聊");
        hintLabel.setFont(FONT_SMALL);
        hintLabel.setForeground(new Color(160, 160, 160));
        hintLabel.setBorder(BorderFactory.createEmptyBorder(6, 15, 10, 10));
        panel.add(hintLabel, BorderLayout.SOUTH);

        return panel;
    }

    private class UserListCellRenderer extends DefaultListCellRenderer {
        @Override
        public Component getListCellRendererComponent(JList<?> list, Object value, int index,
                                                      boolean isSelected, boolean cellHasFocus) {
            JLabel label = (JLabel) super.getListCellRendererComponent(list, value, index, isSelected, cellHasFocus);
            label.setIconTextGap(8);
            label.setFont(FONT_MAIN);
            if (value != null) {
                label.setText("● " + value.toString());
                label.setForeground(new Color(46, 194, 126));
            }
            if (isSelected) {
                label.setBackground(new Color(230, 240, 255));
                label.setOpaque(true);
            } else {
                label.setOpaque(false);
            }
            return label;
        }
    }

    // ================================================
    //  4. 右侧聊天主区域
    // ================================================
    private JPanel createChatMainPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(COLOR_BG_MAIN);

        chatHeaderPanel = new JPanel(new BorderLayout());
        chatHeaderPanel.setBackground(COLOR_HEADER_BG);
        chatHeaderPanel.setBorder(BorderFactory.createMatteBorder(0, 0, 1, 0, COLOR_BORDER));

        JPanel headerLeft = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 8));
        headerLeft.setOpaque(false);

        chatTargetLabel = new JLabel("💬 全部聊天");
        chatTargetLabel.setFont(FONT_TITLE);
        headerLeft.add(chatTargetLabel);

        chatTargetStatusLabel = new JLabel("");
        chatTargetStatusLabel.setFont(FONT_SMALL);
        chatTargetStatusLabel.setForeground(new Color(46, 194, 126));
        headerLeft.add(chatTargetStatusLabel);

        chatHeaderPanel.add(headerLeft, BorderLayout.WEST);

        JPanel headerRight = new JPanel(new FlowLayout(FlowLayout.RIGHT, 5, 4));
        headerRight.setOpaque(false);
        headerRight.add(new JLabel("资料:"));
        txtProfileField = new JTextField("city", 5);
        txtProfileField.setFont(FONT_SMALL);
        txtProfileField.setBorder(BorderFactory.createLineBorder(COLOR_BORDER, 1, true));
        headerRight.add(txtProfileField);
        txtProfileValue = new JTextField("北京", 7);
        txtProfileValue.setFont(FONT_SMALL);
        txtProfileValue.setBorder(BorderFactory.createLineBorder(COLOR_BORDER, 1, true));
        headerRight.add(txtProfileValue);

        buttonProfileSave = createGrayButton("保存");
        buttonProfileSave.addActionListener(this);
        headerRight.add(buttonProfileSave);

        buttonProfileView = createGrayButton("查询");
        buttonProfileView.addActionListener(this);
        headerRight.add(buttonProfileView);

        chatHeaderPanel.add(headerRight, BorderLayout.EAST);
        panel.add(chatHeaderPanel, BorderLayout.NORTH);

        historyWindow = new ClientHistory();
        historyWindow.setBackground(Color.WHITE);
        historyWindow.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        chatScrollPane = new JScrollPane(historyWindow);
        chatScrollPane.setBorder(null);
        chatScrollPane.setBackground(Color.WHITE);
        chatScrollPane.getVerticalScrollBar().setUnitIncrement(16);
        chatScrollPane.setAutoscrolls(true);
        panel.add(chatScrollPane, BorderLayout.CENTER);

        return panel;
    }

    // ================================================
    //  5. 底部输入区域
    // ================================================
    private JPanel createInputPanel() {
        JPanel panel = new JPanel(new BorderLayout(0, 0));
        panel.setBackground(Color.WHITE);
        panel.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createMatteBorder(1, 0, 0, 0, COLOR_BORDER),
                BorderFactory.createEmptyBorder(8, 10, 10, 10)
        ));

        inputPanel = new JPanel(new BorderLayout(8, 0));
        inputPanel.setOpaque(false);

        msgWindow = new JTextField();
        msgWindow.setFont(FONT_MAIN);
        msgWindow.setBorder(BorderFactory.createCompoundBorder(
                new LineBorder(COLOR_BORDER, 1, true),
                BorderFactory.createEmptyBorder(8, 12, 8, 12)
        ));
        msgWindow.addKeyListener(this);
        inputPanel.add(msgWindow, BorderLayout.CENTER);

        buttonSend = createGreenButton("发送 (Enter)");
        buttonSend.addActionListener(this);
        inputPanel.add(buttonSend, BorderLayout.EAST);

        panel.add(inputPanel, BorderLayout.CENTER);

        toolPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 4));
        toolPanel.setOpaque(false);

        privateChat = new JCheckBox("🔒 私聊选中");
        privateChat.setFont(FONT_SMALL);
        privateChat.setBackground(Color.WHITE);
        privateChat.setOpaque(true);
        toolPanel.add(privateChat);

        buttonAddFriend = createGrayButton("＋ 加好友");
        buttonAddFriend.addActionListener(this);
        buttonAddFriend.setActionCommand("addFriend");
        toolPanel.add(buttonAddFriend);

        toolPanel.add(new JSeparator(SwingConstants.VERTICAL) {{
            setPreferredSize(new Dimension(1, 20));
        }});

        buttonFile = createGrayButton("📎 文件");
        buttonFile.addActionListener(this);
        toolPanel.add(buttonFile);

        buttonImage = createGrayButton("🖼️ 图片");
        buttonImage.addActionListener(this);
        toolPanel.add(buttonImage);

        panel.add(toolPanel, BorderLayout.SOUTH);

        return panel;
    }

    // ================================================
    //  6. 核心业务方法
    // ================================================

    public void addMsg(String str) {
        historyWindow.addText(str);
        SwingUtilities.invokeLater(() -> {
            JScrollBar bar = chatScrollPane.getVerticalScrollBar();
            bar.setValue(bar.getMaximum());
        });
    }

    private void disconnect() {
        if (ck != null) {
            try {
                ck.sendCommand("exit");
                ck.dropMe();
                ck = null;
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        setConnectionStatus(false, "已断开");
        userModel.clear();
        onlineTitleLabel.setText("👥 在线用户 (0)");
        addMsg("<div class='system'><span class='sys-icon'>⛔</span> 已断开与服务器的连接</div>");
    }

    private void connect() {
        try {
            if (ck != null) {
                ck.dropMe();
                ck = null;
            }
            setConnectionStatus(false, "连接中...");
            updateStatusBar(txtHost.getText(), txtNick.getText());

            ck = new ClientKernel(txtHost.getText(), Integer.parseInt(txtPort.getText()));
            ck.setNick(txtNick.getText());

            if (ck.isConnected()) {
                ck.addClient(this);
                setConnectionStatus(true, "已连接");
                updateStatusBar(txtHost.getText(), txtNick.getText());
                addMsg("<div class='system'><span class='sys-icon'>✓</span> 已连接到服务器 (端口: " + ck.getLocalPort() + ")</div>");
            } else {
                setConnectionStatus(false, "连接失败");
                addMsg("<div class='system error'><span class='sys-icon'>✗</span> 连接服务器失败，请检查地址和端口</div>");
            }
        } catch (Exception e) {
            e.printStackTrace();
            setConnectionStatus(false, "连接异常");
            addMsg("<div class='system error'><span class='sys-icon'>✗</span> 连接异常: " + e.getMessage() + "</div>");
        }
    }

    private void send() {
        String toSend = msgWindow.getText();
        if (ck == null || !ck.isConnected() || toSend.trim().length() == 0) {
            return;
        }

        String selected = userList.getSelectedValue();
        if (privateChat.isSelected() && selected != null) {
            ck.sendCommand("msg " + selected + " " + toSend);
            addMsg("<div class='self'><div class='msg-info'>我 → " + selected + "</div><div class='msg-bubble'>" + escapeHtml(toSend) + "</div></div>");
        } else {
            ck.sendMessage(toSend);
            addMsg("<div class='self'><div class='msg-info'>我 → 全部</div><div class='msg-bubble'>" + escapeHtml(toSend) + "</div></div>");
        }

        lastMsg = toSend;
        msgWindow.setText("");
    }

    public void updateUsers(String[] users) {
        SwingUtilities.invokeLater(() -> {
            String selected = userList.getSelectedValue();
            userModel.clear();
            for (String user : users) {
                if (user.trim().length() > 0) {
                    userModel.addElement(user.trim());
                }
            }
            onlineTitleLabel.setText("👥 在线用户 (" + userModel.size() + ")");
            if (selected != null && userModel.contains(selected)) {
                userList.setSelectedValue(selected, true);
            }
        });
    }

    private String selectedUser() {
        String selected = userList.getSelectedValue();
        if (selected == null) {
            addMsg("<div class='system warn'><span class='sys-icon'>⚠</span> 请先在右侧选择一个在线用户</div>");
        }
        return selected;
    }

    private void addFriend() {
        String selected = selectedUser();
        if (selected != null && ck != null) {
            ck.sendCommand("friend add " + selected);
            addMsg("<div class='system'><span class='sys-icon'>✓</span> 已发送好友请求给 " + selected + "</div>");
        }
    }

    private void saveProfile() {
        if (ck != null) {
            ck.sendCommand("profile set " + txtProfileField.getText() + "=" + txtProfileValue.getText());
        }
    }

    private void viewProfile() {
        if (ck != null) {
            String selected = userList.getSelectedValue();
            ck.sendCommand("profile view " + (selected == null ? txtNick.getText() : selected));
        }
    }

    private void sendAttachment(boolean image) {
        String selected = selectedUser();
        if (selected == null || ck == null) return;

        JFileChooser chooser = new JFileChooser();
        chooser.setDialogTitle(image ? "选择图片发送" : "选择文件发送");
        if (chooser.showOpenDialog(this) != JFileChooser.APPROVE_OPTION) return;

        try {
            File file = chooser.getSelectedFile();
            if (file.length() > 5 * 1024 * 1024) {
                addMsg("<div class='system error'><span class='sys-icon'>✗</span> 文件超过 5MB 限制</div>");
                return;
            }
            String data = Base64.getEncoder().encodeToString(Files.readAllBytes(file.toPath()));
            ck.sendCommand((image ? "image " : "file ") + selected + " " + file.getName() + "|" + data);
            String type = image ? "图片" : "文件";
            // 图片使用 🖼️ 图标，文件使用 📎 图标
            String icon = image ? "🖼️" : "📎";
            addMsg("<div class='self'><div class='msg-info'>我 → " + selected + " [发送" + type + "]</div><div class='msg-bubble'>" + icon + " " + file.getName() + "</div></div>");
        } catch (Exception ex) {
            addMsg("<div class='system error'><span class='sys-icon'>✗</span> 附件发送失败: " + ex.getMessage() + "</div>");
        }
    }

    // ================================================
    //  7. 工具方法
    // ================================================

    private String escapeHtml(String str) {
        if (str == null) return "";
        return str.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("\n", "<br>");
    }

    // ================================================
    //  8. 事件监听器
    // ================================================

    public void keyPressed(KeyEvent e) {}

    public void keyReleased(KeyEvent e) {
        if (e.getSource() == msgWindow && e.getKeyCode() == KeyEvent.VK_UP) {
            msgWindow.setText(lastMsg);
        }
    }

    public void keyTyped(KeyEvent e) {
        if (e.getKeyChar() == KeyEvent.VK_ENTER) {
            if (e.getSource() == msgWindow) {
                send();
            }
            if (e.getSource() == txtNick) {
                connect();
                msgWindow.requestFocus();
            }
            if (e.getSource() == txtHost) {
                txtPort.requestFocus();
            }
            if (e.getSource() == txtPort) {
                txtNick.requestFocus();
            }
        }
    }

    public void actionPerformed(ActionEvent e) {
        Object src = e.getSource();
        String cmd = e.getActionCommand();

        if (src == buttonConnect) {
            if (buttonConnect.getText().equals("断开")) {
                disconnect();
            } else {
                connect();
            }
        } else if (src == buttonSend) {
            send();
        } else if (src == buttonFriend) {
            addFriend();
        } else if (src == buttonProfileSave) {
            saveProfile();
        } else if (src == buttonProfileView) {
            viewProfile();
        } else if (src == buttonFile) {
            sendAttachment(false);
        } else if (src == buttonImage) {
            sendAttachment(true);
        } else if ("addFriend".equals(cmd)) {
            addFriend();
        }
    }

    public void focusGained(FocusEvent e) {
        if (e.getSource() == txtHost && txtHost.getText().equals(ChatClient.serverText)) {
            txtHost.setText("");
        }
        if (e.getSource() == txtPort && txtPort.getText().equals(ChatClient.portText)) {
            txtPort.setText("");
        }
        if (e.getSource() == txtNick && txtNick.getText().equals(ChatClient.nickText)) {
            txtNick.setText("");
        }
    }

    public void focusLost(FocusEvent e) {
        if (e.getSource() == txtPort && txtPort.getText().equals("")) {
            txtPort.setText(ChatClient.portText);
        }
        if (e.getSource() == txtHost && txtHost.getText().equals("")) {
            txtHost.setText(ChatClient.serverText);
        }
        if (e.getSource() == txtNick && txtNick.getText().equals(ChatClient.nickText)) {
            txtNick.setText(ChatClient.nickText);
        }
    }

    // ================================================
    //  9. 内部类：聊天记录展示组件
    // ================================================

    class ClientHistory extends JEditorPane {
        private static final String CSS_STYLE =
                "<style>"
                        + "body { font-family: '微软雅黑', 'PingFang SC', sans-serif; font-size: 14px; line-height: 1.6; padding: 10px; margin: 0; }"
                        + ".msg-wrapper { display: block; margin-bottom: 12px; }"
                        + ".self { text-align: right; }"
                        + ".other { text-align: left; }"
                        + ".msg-bubble { display: inline-block; padding: 8px 14px; border-radius: 12px; max-width: 70%; word-wrap: break-word; }"
                        + ".self .msg-bubble { background: #9EDD61; color: #1a1a1a; }"
                        + ".other .msg-bubble { background: #ffffff; border: 1px solid #e0e0e0; color: #1a1a1a; }"
                        + ".msg-info { font-size: 11px; color: #999; margin-bottom: 2px; padding: 0 4px; }"
                        + ".system { text-align: center; margin: 8px 0; font-size: 12px; color: #999; }"
                        + ".system .sys-icon { display: inline-block; margin-right: 4px; }"
                        + ".system.error { color: #e74c3c; }"
                        + ".system.warn { color: #f39c12; }"
                        + ".join-msg { text-align: center; margin: 8px 0; font-size: 13px; color: #2ecc71; }"
                        + ".join-msg .join-icon { display: inline-block; margin-right: 6px; font-weight: bold; }"
                        + ".join-msg .user-name { font-weight: bold; color: #1a7a4a; }"
                        + ".leave-msg { text-align: center; margin: 8px 0; font-size: 13px; color: #e67e22; }"
                        + ".leave-msg .leave-icon { display: inline-block; margin-right: 6px; font-weight: bold; }"
                        + ".rename-msg { text-align: center; margin: 8px 0; font-size: 12px; color: #3498db; }"
                        + ".attachment-card { display: inline-block; background: #f5f5f5; border: 1px solid #ddd; border-radius: 8px; padding: 10px 16px; }"
                        + ".attachment-card img { max-width: 180px; max-height: 180px; border-radius: 6px; display: block; margin-top: 6px; }"
                        + "</style>";

        public ClientHistory() {
            super("text/html", "<html><head>" + CSS_STYLE + "</head><body></body></html>");
            setEditable(false);
            setAutoscrolls(true);
            setBackground(Color.WHITE);
        }

        public void addText(String str) {
            String content = str;

            if (str.startsWith("@JOIN ")) {
                String userName = str.substring(6).trim();
                content = "<div class='join-msg'><span class='join-icon'>▶</span> <span class='user-name'>"
                        + escapeHtml(userName) + "</span> 加入聊天室</div>";
            } else if (str.startsWith("@RENAME ")) {
                String[] parts = str.substring(8).split("\\|", 2);
                if (parts.length == 2) {
                    content = "<div class='rename-msg'>✏️ " + escapeHtml(parts[0]) + " 改名为 " + escapeHtml(parts[1]) + "</div>";
                }
            } else if (str.startsWith("@LEAVE ")) {
                String userName = str.substring(7).trim();
                content = "<div class='leave-msg'><span class='leave-icon'>◀</span> " + escapeHtml(userName) + " 离开聊天室</div>";
            } else if (str.startsWith("@SYSTEM ")) {
                String sysMsg = str.substring(8);
                if (sysMsg.contains("connected to chat server") ||
                        sysMsg.contains("changed name to") ||
                        sysMsg.contains("your nickname is now")) {
                    return;
                }
                content = "<div class='system'><span class='sys-icon'>ℹ</span> " + escapeHtml(sysMsg) + "</div>";
            } else if (str.startsWith("@CHAT ")) {
                String chatContent = str.substring(6);
                content = "<div class='msg-wrapper'>" + chatContent + "</div>";
            } else if (str.startsWith("@PROFILE ")) {
                String profileContent = str.substring(9);
                content = "<div class='system' style='color:#3157a5;'>📋 " + profileContent.replace("|", "：") + "</div>";
            } else if (str.startsWith("@IMAGE ")) {
                // 图片消息使用 🖼️ 图标
                String imgContent = str.substring(7);
                content = "<div class='msg-wrapper'><div class='other'><div class='msg-bubble'>🖼️ " + imgContent + "</div></div></div>";
            } else if (str.startsWith("@FILE ")) {
                // 文件消息使用 📎 图标
                String fileContent = str.substring(6);
                content = "<div class='msg-wrapper'><div class='other'><div class='msg-bubble'>📎 " + fileContent + "</div></div></div>";
            } else if (!str.startsWith("<") && !str.startsWith("@")) {
                content = "<div class='msg-wrapper other'><div class='msg-bubble'>" + escapeHtml(str) + "</div></div>";
            } else {
                if (str.contains("msg-wrapper") || str.contains("system") ||
                        str.contains("join-msg") || str.contains("leave-msg") || str.contains("rename-msg")) {
                    content = str;
                } else {
                    content = "<div class='msg-wrapper'>" + str + "</div>";
                }
            }

            String html = getText();
            int end = html.lastIndexOf("</body>");
            if (end == -1) {
                setText("<html><head>" + CSS_STYLE + "</head><body>" + content + "</body></html>");
            } else {
                String newHtml = html.substring(0, end) + content + html.substring(end);
                setText(newHtml);
            }

            setCaretPosition(getDocument().getLength());
        }

        public void clear() {
            setText("<html><head>" + CSS_STYLE + "</head><body></body></html>");
        }
    }

    // ================================================
    //  10. Main 方法
    // ================================================

    public static void main(String args[]) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            e.printStackTrace();
        }

        ChatClient client = new ChatClient();
        client.setVisible(true);
        client.msgWindow.requestFocus();
    }
}