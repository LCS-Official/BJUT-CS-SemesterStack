package com.cncd.ch04.client;

import javax.swing.*;
import javax.swing.border.Border;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import javax.swing.event.HyperlinkEvent;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 聊天客户端主界面 - 重构版
 * 视觉风格：接近 QQ/微信，清晰区分消息类型
 *
 * @author Client UI Team
 */
public class ChatClient extends JFrame implements KeyListener, ActionListener, FocusListener {
    public static final String appName = "Chat Tool";
    public static final String defaultServer = "127.0.0.1";
    public static final String defaultPort = "3500";
    public static final String serverText = ClientConfig.get("server.host", defaultServer);
    public static final String portText = ClientConfig.get("server.port", defaultPort);
    public static final String nickText = ClientConfig.get("nick", "YourName");

    // ==================== UI 组件 ====================
    // ---- 顶部状态栏 ----
    private JPanel topStatusPanel;
    private JLabel statusDot;
    private JLabel statusLabel;
    private JLabel serverInfoLabel;
    private JLabel nickInfoLabel;
    private JButton buttonTopDisconnect;

    // ---- 连接面板 (North) ----
    private JPanel northPanel;
    private JPanel centerPanel, authPanel, loginPanel, registerPanel;
    private CardLayout authCards;
    private CardLayout centerCards;
    private JTextField txtHost, txtPort, txtRegHost, txtRegPort, txtNick, txtUserId, txtSearchId, txtRegNick;
    private JPasswordField txtPassword, txtRegPassword;
    private JLabel loginStatusLabel;
    private JButton buttonConnect, buttonPing, buttonRegPing, buttonRegister, buttonShowRegister, buttonShowLogin, buttonSearchUser;

    // ---- 主内容区域 (Center) ----
    private JSplitPane mainSplitPane;

    // ---- 左侧联系人面板 ----
    private JPanel leftPanel;
    private JLabel onlineTitleLabel;
    private JList<String> userList;
    private DefaultListModel<String> userModel;
    private JScrollPane userScrollPane;
    private JButton buttonCreateGroup;

    // ---- 右侧聊天主面板 ----
    private JPanel chatMainPanel;
    private JPanel chatHeaderPanel;
    private JLabel chatTargetLabel;
    private JLabel chatTargetStatusLabel;
    private JButton buttonFriend;
    private JButton buttonRenameGroup, buttonGroupMembers, buttonDeleteGroup;

    // ---- 聊天记录区 ----
    private JScrollPane chatScrollPane;
    private ClientHistory historyWindow;

    // ---- 底部输入区 ----
    private JPanel southPanel;
    private JPanel inputPanel;
    private JTextField msgWindow;
    private JButton buttonSend;
    private JPanel toolPanel;
    private JButton buttonProfileSave, buttonFile, buttonImage;

    // ==================== 业务组件 ====================
    private ClientKernel ck;
    private String lastMsg = "";
    private String selfUid = "";
    private final Set<String> friends = new HashSet<String>();
    private final Set<String> privateConversations = new LinkedHashSet<String>();
    private final List<String> onlineUsers = new ArrayList<String>();
    private final List<String> groupEntries = new ArrayList<String>();
    private final Map<String, String> groupOwners = new HashMap<String, String>();
    private final Map<String, String> conversationLast = new HashMap<String, String>();
    private final Map<String, String> conversationTime = new HashMap<String, String>();
    private final Map<String, StringBuilder> conversationLogs = new HashMap<String, StringBuilder>();
    private final Map<String, String> userAvatars = new HashMap<String, String>();
    private final Map<String, String> nickByUid = new HashMap<String, String>();
    private final Map<String, String> uidByNick = new HashMap<String, String>();

    private static final String CONV_PUBLIC = "public:公开频道";
    private static final String CONV_USER_PREFIX = "user:";
    private static final String CONV_GROUP_PREFIX = "group:";
    private static final String GROUP_RENAME_PREFIX = "@@GROUP_RENAME:";
    private static final String DEFAULT_AVATAR = "avatar_01_sunrise.png";
    private static final Pattern AVATAR_TOKEN = Pattern.compile("@@AVATAR:([A-Za-z0-9_-]+)@@");

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
        txtHost.setText(serverText);
        txtPort.setText(portText);
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
        JPanel topWrapper = new JPanel(new BorderLayout());
        topStatusPanel = createStatusBar();
        topWrapper.add(topStatusPanel, BorderLayout.NORTH);

        // ============================================
        // 2. 连接设置面板 (位于状态栏下方)
        // ============================================
        add(topWrapper, BorderLayout.NORTH);

        // ============================================
        // 3. 主内容区域 (Center) - 使用 JSplitPane 分割
        // ============================================
        mainSplitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        mainSplitPane.setDividerLocation(230);
        mainSplitPane.setDividerSize(2);
        mainSplitPane.setBorder(null);

        // ---- 左侧：联系人列表 ----
        leftPanel = createContactPanel();
        mainSplitPane.setLeftComponent(leftPanel);

        // ---- 右侧：聊天主区域 ----
        chatMainPanel = createChatMainPanel();
        mainSplitPane.setRightComponent(chatMainPanel);

        loginPanel = createLoginPage();
        centerCards = new CardLayout();
        centerPanel = new JPanel(centerCards);
        centerPanel.add(loginPanel, "login");
        centerPanel.add(mainSplitPane, "chat");
        add(centerPanel, BorderLayout.CENTER);

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

        buttonTopDisconnect = createDisconnectButton("断开");
        buttonTopDisconnect.setFont(FONT_SMALL);
        buttonTopDisconnect.setBorder(BorderFactory.createEmptyBorder(4, 12, 4, 12));
        buttonTopDisconnect.addActionListener(this);
        buttonTopDisconnect.setVisible(false);
        panel.add(buttonTopDisconnect);

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
            serverInfoLabel.setText("服务器: 已连接");
            centerCards.show(centerPanel, "chat");
            southPanel.setVisible(true);
            buttonTopDisconnect.setVisible(true);
            setAuthFieldsEnabled(false);
        } else {
            statusDot.setForeground(COLOR_OFFLINE);
            statusLabel.setText("○ " + text);
            statusLabel.setForeground(new Color(80, 80, 80));
            buttonConnect.setText("登录");
            buttonConnect.setEnabled(true);
            buttonConnect.setForeground(Color.WHITE);
            serverInfoLabel.setText("服务器: 未连接");
            nickInfoLabel.setText("昵称: --");
            centerCards.show(centerPanel, "login");
            if (authCards != null && authPanel != null) authCards.show(authPanel, "login");
            southPanel.setVisible(false);
            buttonTopDisconnect.setVisible(false);
            setAuthFieldsEnabled(true);
        }
        centerPanel.revalidate();
        centerPanel.repaint();
    }

    private void setAuthFieldsEnabled(boolean enabled) {
        if (txtHost != null) txtHost.setEnabled(enabled);
        if (txtPort != null) txtPort.setEnabled(enabled);
        if (txtRegHost != null) txtRegHost.setEnabled(enabled);
        if (txtRegPort != null) txtRegPort.setEnabled(enabled);
        if (txtNick != null) txtNick.setEnabled(enabled);
        if (txtUserId != null) txtUserId.setEnabled(enabled);
        if (txtPassword != null) txtPassword.setEnabled(enabled);
        if (txtRegNick != null) txtRegNick.setEnabled(enabled);
        if (txtRegPassword != null) txtRegPassword.setEnabled(enabled);
        if (buttonRegister != null) buttonRegister.setEnabled(enabled);
        if (buttonShowRegister != null) buttonShowRegister.setEnabled(enabled);
        if (buttonShowLogin != null) buttonShowLogin.setEnabled(enabled);
        if (buttonPing != null) buttonPing.setEnabled(enabled);
        if (buttonRegPing != null) buttonRegPing.setEnabled(enabled);
    }

    private void updateStatusBar(String server, String nick) {
        serverInfoLabel.setText("服务器: " + (ck != null && ck.isConnected() ? "已连接" : "连接中"));
        String name = nick != null && !nick.isEmpty() ? nick : "--";
        String id = selfUid != null && selfUid.length() > 0 ? "  ID: " + selfUid : "";
        nickInfoLabel.setText("昵称: " + name + id);
    }

    private String serverHost() {
        String host = txtHost == null ? "" : txtHost.getText().trim();
        return host.length() == 0 ? serverText : host;
    }

    private String serverPortText() {
        String port = txtPort == null ? "" : txtPort.getText().trim();
        return port.length() == 0 ? portText : port;
    }

    // ================================================
    //  2. 连接设置面板
    // ================================================
    private JPanel createLoginPage() {
        JPanel page = new JPanel(new GridBagLayout());
        page.setBackground(new Color(246, 248, 252));
        if (txtHost == null) txtHost = new JTextField(serverText);
        if (txtPort == null) txtPort = new JTextField(portText);
        if (txtNick == null) txtNick = new JTextField(nickText);
        JPanel card = new JPanel(new BorderLayout(0, 14));
        card.setBackground(Color.WHITE);
        card.setBorder(BorderFactory.createCompoundBorder(
                new LineBorder(new Color(222, 226, 232), 1, true),
                BorderFactory.createEmptyBorder(22, 26, 20, 26)
        ));
        authCards = new CardLayout();
        authPanel = new JPanel(authCards);
        authPanel.setBackground(Color.WHITE);
        loginPanel = createLoginForm();
        registerPanel = createRegisterForm();
        authPanel.add(loginPanel, "login");
        authPanel.add(registerPanel, "register");
        card.add(authPanel, BorderLayout.CENTER);
        loginStatusLabel = new JLabel(" ");
        loginStatusLabel.setForeground(new Color(120, 128, 140));
        card.add(loginStatusLabel, BorderLayout.SOUTH);
        page.add(card);
        return page;
    }

    private JLabel authTitle(String text) {
        JLabel title = new JLabel(text);
        title.setFont(new Font("微软雅黑", Font.BOLD, 22));
        return title;
    }

    private JPanel createLoginForm() {
        JPanel wrap = new JPanel(new BorderLayout(0, 14));
        wrap.setBackground(Color.WHITE);
        wrap.add(authTitle("登录聊天服务器"), BorderLayout.NORTH);
        northPanel = createConnectionPanel(false);
        wrap.add(northPanel, BorderLayout.CENTER);
        return wrap;
    }

    private JPanel createRegisterForm() {
        JPanel wrap = new JPanel(new BorderLayout(0, 14));
        wrap.setBackground(Color.WHITE);
        wrap.add(authTitle("新建账户"), BorderLayout.NORTH);
        wrap.add(createConnectionPanel(true), BorderLayout.CENTER);
        return wrap;
    }

    private JPanel createConnectionPanel(boolean registerPage) {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(Color.WHITE);
        panel.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createMatteBorder(0, 0, 1, 0, COLOR_BORDER),
                BorderFactory.createEmptyBorder(8, 15, 8, 15)
        ));
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(0, 5, 0, 5);
        gbc.fill = GridBagConstraints.HORIZONTAL;

        int row = 0;
        gbc.gridx = 1; gbc.gridy = row;
        gbc.anchor = GridBagConstraints.EAST;
        JButton pingButton;
        if (registerPage) {
            if (buttonRegPing == null) {
                buttonRegPing = createGrayButton("Ping");
                buttonRegPing.addActionListener(this);
            }
            pingButton = buttonRegPing;
        } else {
            if (buttonPing == null) {
                buttonPing = createGrayButton("Ping");
                buttonPing.addActionListener(this);
            }
            pingButton = buttonPing;
        }
        panel.add(pingButton, gbc);

        gbc.anchor = GridBagConstraints.CENTER;

        if (!registerPage) {
            gbc.gridx = 0; gbc.gridy = ++row;
            panel.add(new JLabel("ID:"), gbc);
            gbc.gridx = 1;
            txtUserId = new JTextField(ClientConfig.get("user.id", ""), 12);
            txtUserId.setFont(FONT_MAIN);
            txtUserId.setBorder(inputBorder());
            txtUserId.addKeyListener(this);
            panel.add(txtUserId, gbc);

            gbc.gridx = 0; gbc.gridy = ++row;
            panel.add(new JLabel("密码:"), gbc);
            gbc.gridx = 1;
            txtPassword = new JPasswordField(12);
            txtPassword.setFont(FONT_MAIN);
            txtPassword.setBorder(inputBorder());
            txtPassword.addKeyListener(this);
            panel.add(txtPassword, gbc);

            gbc.gridx = 0; gbc.gridy = ++row;
            gbc.weightx = 0;
            buttonConnect = createGreenButton("登录");
            buttonConnect.addActionListener(this);
            panel.add(buttonConnect, gbc);

            gbc.gridx = 1;
            buttonShowRegister = createGrayButton("新建账户");
            buttonShowRegister.addActionListener(this);
            panel.add(buttonShowRegister, gbc);
        } else {
            gbc.gridx = 0; gbc.gridy = ++row;
            panel.add(new JLabel("昵称:"), gbc);
            gbc.gridx = 1;
            txtRegNick = new JTextField(nickText, 10);
            txtRegNick.setFont(FONT_MAIN);
            txtRegNick.setBorder(inputBorder());
            txtRegNick.addKeyListener(this);
            panel.add(txtRegNick, gbc);

            gbc.gridx = 0; gbc.gridy = ++row;
            panel.add(new JLabel("密码:"), gbc);
            gbc.gridx = 1;
            txtRegPassword = new JPasswordField(12);
            txtRegPassword.setFont(FONT_MAIN);
            txtRegPassword.setBorder(inputBorder());
            txtRegPassword.addKeyListener(this);
            panel.add(txtRegPassword, gbc);

            gbc.gridx = 0; gbc.gridy = ++row;
            gbc.weightx = 0;
            buttonRegister = createGreenButton("注册");
            buttonRegister.addActionListener(this);
            panel.add(buttonRegister, gbc);

            gbc.gridx = 1;
            buttonShowLogin = createGrayButton("已有账户");
            buttonShowLogin.addActionListener(this);
            panel.add(buttonShowLogin, gbc);
        }

        gbc.gridx = 2;
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

        JPanel header = new JPanel(new BorderLayout(8, 0));
        header.setBackground(new Color(247, 247, 247));
        header.setBorder(BorderFactory.createEmptyBorder(10, 12, 8, 10));

        onlineTitleLabel = new JLabel("会话 (1)");
        onlineTitleLabel.setFont(FONT_TITLE);
        header.add(onlineTitleLabel, BorderLayout.WEST);

        buttonCreateGroup = createGrayButton("建群");
        buttonCreateGroup.addActionListener(this);
        header.add(buttonCreateGroup, BorderLayout.EAST);

        JPanel searchPanel = new JPanel(new BorderLayout(6, 0));
        searchPanel.setOpaque(false);
        txtSearchId = new JTextField();
        txtSearchId.setFont(FONT_SMALL);
        txtSearchId.setBorder(BorderFactory.createCompoundBorder(
                new LineBorder(COLOR_BORDER, 1, true),
                BorderFactory.createEmptyBorder(3, 6, 3, 6)
        ));
        buttonSearchUser = createGrayButton("搜ID");
        buttonSearchUser.addActionListener(this);
        searchPanel.add(txtSearchId, BorderLayout.CENTER);
        searchPanel.add(buttonSearchUser, BorderLayout.EAST);
        header.add(searchPanel, BorderLayout.SOUTH);
        panel.add(header, BorderLayout.NORTH);

        userModel = new DefaultListModel<>();
        userModel.addElement(CONV_PUBLIC);
        userList = new JList<>(userModel);
        userList.setFont(FONT_MAIN);
        userList.setBackground(Color.WHITE);
        userList.setSelectionBackground(new Color(230, 240, 255));
        userList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        userList.setBorder(BorderFactory.createEmptyBorder(4, 4, 4, 4));
        userList.setFixedCellHeight(66);
        userList.setCellRenderer(new UserListCellRenderer());
        userList.addListSelectionListener(e -> updateChatTarget());
        userList.addMouseListener(new MouseAdapter() {
            public void mouseClicked(MouseEvent e) {
                if (e.getClickCount() != 2) return;
                String conversation = selectedConversation();
                if (isPublicConversation(conversation)) showPublicMembers();
                else if (isUserConversation(conversation)) viewProfile();
                else if (isGroupConversation(conversation)) showGroupMembers();
            }
        });
        userList.setSelectedIndex(0);

        userScrollPane = new JScrollPane(userList);
        userScrollPane.setBorder(null);
        userScrollPane.getVerticalScrollBar().setUnitIncrement(16);
        panel.add(userScrollPane, BorderLayout.CENTER);

        JLabel hintLabel = new JLabel("选中会话后发送；建群后可群聊");
        hintLabel.setFont(FONT_SMALL);
        hintLabel.setForeground(new Color(160, 160, 160));
        hintLabel.setBorder(BorderFactory.createEmptyBorder(6, 15, 10, 10));
        panel.add(hintLabel, BorderLayout.SOUTH);

        return panel;
    }

    private Border inputBorder() {
        return BorderFactory.createCompoundBorder(
                new LineBorder(COLOR_BORDER, 1, true),
                BorderFactory.createEmptyBorder(4, 8, 4, 8)
        );
    }

    private class UserListCellRenderer extends JPanel implements ListCellRenderer<String> {
        private final JLabel avatar = new JLabel("", SwingConstants.CENTER);
        private final JLabel title = new JLabel();
        private final JLabel subtitle = new JLabel();
        private final JLabel time = new JLabel();
        private final JPanel textPanel = new JPanel(new GridLayout(2, 1, 0, 2));

        UserListCellRenderer() {
            setLayout(new BorderLayout(8, 0));
            setBorder(BorderFactory.createEmptyBorder(7, 8, 7, 8));
            avatar.setPreferredSize(new Dimension(42, 42));
            avatar.setOpaque(true);
            avatar.setBackground(new Color(232, 236, 244));
            avatar.setBorder(new LineBorder(new Color(215, 221, 232), 1, true));
            avatar.setFont(new Font("微软雅黑", Font.BOLD, 18));

            title.setFont(new Font("微软雅黑", Font.PLAIN, 15));
            subtitle.setFont(FONT_SMALL);
            subtitle.setForeground(new Color(145, 151, 160));
            textPanel.setOpaque(false);
            textPanel.add(title);
            textPanel.add(subtitle);

            time.setFont(FONT_SMALL);
            time.setForeground(new Color(165, 169, 176));

            add(avatar, BorderLayout.WEST);
            add(textPanel, BorderLayout.CENTER);
            add(time, BorderLayout.EAST);
        }

        @Override
        public Component getListCellRendererComponent(JList<? extends String> list, String value, int index,
                                                      boolean isSelected, boolean cellHasFocus) {
            String entry = value == null ? CONV_PUBLIC : value;
            String name = conversationTitle(entry);
            boolean user = isUserConversation(entry);

            avatar.setText("");
            avatar.setIcon(conversationAvatarIcon(entry));
            String uid = user ? entry.substring(CONV_USER_PREFIX.length()) : "";
            title.setText((user && friends.contains(uid.toLowerCase()) ? "★ " : "") + name);
            subtitle.setText(conversationLast.containsKey(entry)
                    ? conversationLast.get(entry)
                    : defaultConversationSubtitle(entry));
            time.setText(conversationTime.getOrDefault(entry, ""));

            Color bg = isSelected ? new Color(229, 232, 236) : Color.WHITE;
            setBackground(bg);
            setOpaque(true);
            title.setForeground(new Color(28, 32, 36));
            return this;
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

        JPanel headerRight = new JPanel(new FlowLayout(FlowLayout.RIGHT, 8, 5));
        headerRight.setOpaque(false);

        buttonProfileSave = createGrayButton("编辑资料");
        buttonProfileSave.addActionListener(this);
        headerRight.add(buttonProfileSave);
        buttonGroupMembers = createGrayButton("群成员");
        buttonGroupMembers.addActionListener(this);
        buttonGroupMembers.setVisible(false);
        headerRight.add(buttonGroupMembers);
        buttonRenameGroup = createGrayButton("改群名");
        buttonRenameGroup.addActionListener(this);
        buttonRenameGroup.setVisible(false);
        headerRight.add(buttonRenameGroup);
        buttonDeleteGroup = createGrayButton("删除群聊");
        buttonDeleteGroup.addActionListener(this);
        buttonDeleteGroup.setVisible(false);
        headerRight.add(buttonDeleteGroup);

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

        buttonFile = createGrayButton("📎 文件");
        buttonFile.addActionListener(this);
        toolPanel.add(buttonFile);

        buttonImage = createGrayButton("🖼️ 图片");
        buttonImage.addActionListener(this);
        toolPanel.add(buttonImage);

        panel.add(toolPanel, BorderLayout.SOUTH);

        updateChatTarget();
        return panel;
    }

    // ================================================
    //  6. 核心业务方法
    // ================================================

    public void addMsg(String str) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> addMsg(str));
            return;
        }
        addMsgToConversation(selectedConversation(), str);
    }

    public void addChatMsg(String sender, String target, String message, String html) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> addChatMsg(sender, target, message, html));
            return;
        }
        addChatMsg(uidFor(sender), sender, uidFor(target), target, message);
    }

    public void addChatMsg(String senderUid, String senderNick, String targetId, String targetTitle, String message) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> addChatMsg(senderUid, senderNick, targetId, targetTitle, message));
            return;
        }
        rememberUser(senderUid, senderNick);
        if (!isPublicConversationId(targetId) && !isGroupConversationId(targetId)) {
            rememberUser(targetId, targetTitle);
        }
        String conversation = conversationForChat(senderUid, senderNick, targetId, targetTitle);
        if (message != null && message.startsWith(GROUP_RENAME_PREFIX)) {
            String name = decodeGroupName(message.substring(GROUP_RENAME_PREFIX.length()));
            String renamed = renameGroupConversation(conversation, name);
            addMsgToConversation(renamed, "<div class='system'>群名已改为 " + escapeHtml(name) + "</div>");
            noteConversation(renamed, "群名已改为 " + name);
            return;
        }
        noteConversation(conversation, (sameUser(senderUid, currentUid()) ? "我" : displayName(senderUid)) + "：" + message);
        addMsgToConversation(conversation, chatHtml(senderUid, targetTitle, message));
    }

    public void addAttachmentMsg(String sender, String fileName, boolean image, String html) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> addAttachmentMsg(sender, fileName, image, html));
            return;
        }
        String conversation = conversationForAttachment(sender);
        noteConversation(conversation, (sameUser(sender, currentUid()) ? "我" : displayName(sender))
                + "：" + (image ? "[图片] " : "[文件] ") + fileName);
        addMsgToConversation(conversation, decorateAvatar(html, sender));
    }

    public void setUserAvatar(String user, String avatar) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> setUserAvatar(user, avatar));
            return;
        }
        if (user == null || user.trim().length() == 0) return;
        String uid = uidFor(user);
        String cleanAvatar = avatar == null ? "" : avatar.trim();
        if (cleanAvatar.length() == 0 && uid.length() > 0
                && userAvatars.containsKey(uid.toLowerCase())) {
            return;
        }
        userAvatars.put(uid.toLowerCase(), validAvatar(cleanAvatar));
        userAvatars.put(user.trim().toLowerCase(), validAvatar(cleanAvatar));
        if (sameUser(uid, currentUid()) || user.trim().equalsIgnoreCase(currentNick())) {
            ClientConfig.set("avatar", validAvatar(cleanAvatar));
        }
        showConversation(selectedConversation());
        userList.repaint();
    }

    public void setUserAvatar(String uid, String nick, String avatar) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> setUserAvatar(uid, nick, avatar));
            return;
        }
        rememberUser(uid, nick);
        setUserAvatar(uid, avatar);
    }

    public void setSelf(String uid, String nick) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> setSelf(uid, nick));
            return;
        }
        rememberUser(uid, nick);
        selfUid = uid == null ? "" : uid.trim();
        userList.repaint();
    }

    public void showProfile(String user, String rawProfile) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> showProfile(user, rawProfile));
            return;
        }
        Map<String, String> fields = profileFields(rawProfile);
        if (fields.containsKey("avatar")) setUserAvatar(user, fields.get("avatar"));
        addMsg(profileHtml(user, displayName(user), fields));
    }

    public void showProfile(String visibleUid, String nick, String rawProfile) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> showProfile(visibleUid, nick, rawProfile));
            return;
        }
        String uid = visibleUid == null || visibleUid.length() == 0 ? uidFor(nick) : visibleUid;
        rememberUser(uid, nick);
        Map<String, String> fields = profileFields(rawProfile);
        if (fields.containsKey("avatar")) setUserAvatar(uid, nick, fields.get("avatar"));
        addMsg(profileHtml(visibleUid, nick, fields));
    }

    private void addMsgToConversation(String conversation, String str) {
        String content = historyWindow.renderText(str);
        if (content == null) return;
        String key = conversation == null ? CONV_PUBLIC : conversation;
        conversationLogs.computeIfAbsent(key, k -> new StringBuilder()).append(content);
        if (key.equals(selectedConversation())) {
            historyWindow.setBody(conversationLogs.get(key).toString());
        }
        SwingUtilities.invokeLater(() -> {
            JScrollBar bar = chatScrollPane.getVerticalScrollBar();
            bar.setValue(bar.getMaximum());
        });
    }

    private void disconnect() {
        if (ck != null) {
            try {
                ck.dropMe();
                ck = null;
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        setConnectionStatus(false, "已断开");
        onlineUsers.clear();
        rebuildConversationModel(CONV_PUBLIC);
        addMsg("<div class='system'><span class='sys-icon'>⛔</span> 已断开与服务器的连接</div>");
    }

    private void connect() {
        connect(false);
    }

    private void connect(boolean register) {
        try {
            final String host = serverHost();
            final String port = serverPortText();
            final String userId = register ? "" : txtUserId.getText().trim();
            final String password = new String((register ? txtRegPassword : txtPassword).getPassword());
            String nickInput = register ? txtRegNick.getText().trim() : currentNick();
            final String nick = nickInput;
            if ((!register && (userId.length() == 0 || password.length() == 0))
                    || (register && (nick.length() == 0 || password.length() == 0))) {
                setLoginStatus(register ? "请输入昵称和密码，ID 将由系统自动分配。" : "请输入ID和密码。");
                return;
            }

            if (ck != null) {
                ck.dropMe();
                ck = null;
            }
            setConnectionStatus(false, "连接中...");
            setLoginStatus("正在连接服务器...");
            JButton authButton = register ? buttonRegister : buttonConnect;
            authButton.setEnabled(false);
            updateStatusBar(host, register ? nick : userId);

            ClientKernel.ConnectionListener listener = new ClientKernel.ConnectionListener() {
                public void onConnected() {
                    SwingUtilities.invokeLater(() -> {
                        setLoginStatus("已连接，正在认证...");
                    });
                }

                public void onConnectFailed(String reason) {
                    SwingUtilities.invokeLater(() -> {
                        setConnectionStatus(false, "连接失败");
                        setLoginStatus("连接失败: " + reason);
                    });
                }

                public void onDisconnected(String reason) {
                    SwingUtilities.invokeLater(() -> {
                        setConnectionStatus(false, "已断开");
                        onlineUsers.clear();
                        rebuildConversationModel(CONV_PUBLIC);
                        if (reason != null && reason.length() > 0) {
                            setLoginStatus("连接断开: " + reason);
                        }
                    });
                }

                public void onError(String error) {
                    SwingUtilities.invokeLater(() -> setLoginStatus(error));
                }
            };

            ck = new ClientKernel(host, Integer.parseInt(port), listener);

            if (ck.isConnected()) {
                ck.addClient(this);
                ClientConfig.set("server.host", host);
                ClientConfig.set("server.port", port);
                if (register) {
                    ClientConfig.set("nick", nick);
                    ck.sendCommand("register " + nick + " " + password);
                } else {
                    ck.sendCommand("login " + userId + " " + password);
                }
            } else {
                setConnectionStatus(false, "连接失败");
                setLoginStatus("连接服务器失败，请稍后重试或联系维护者。");
            }
        } catch (Exception e) {
            e.printStackTrace();
            setConnectionStatus(false, "连接异常");
            setLoginStatus("连接异常: " + e.getMessage());
        } finally {
            if (buttonConnect != null) buttonConnect.setEnabled(true);
            if (buttonRegister != null) buttonRegister.setEnabled(true);
        }
    }

    private void syncAuthConnectionFields(boolean fromRegisterPage) {
        if (fromRegisterPage) {
            if (txtHost != null && txtRegHost != null) txtHost.setText(txtRegHost.getText().trim());
            if (txtPort != null && txtRegPort != null) txtPort.setText(txtRegPort.getText().trim());
        } else {
            if (txtRegHost != null && txtHost != null) txtRegHost.setText(txtHost.getText().trim());
            if (txtRegPort != null && txtPort != null) txtRegPort.setText(txtPort.getText().trim());
        }
    }

    private void showRegisterPage() {
        syncAuthConnectionFields(false);
        authCards.show(authPanel, "register");
        setLoginStatus("注册时系统会自动分配ID。");
        if (txtRegNick != null) txtRegNick.requestFocusInWindow();
    }

    private void showLoginPage() {
        syncAuthConnectionFields(true);
        authCards.show(authPanel, "login");
        setLoginStatus(" ");
        if (txtUserId != null) txtUserId.requestFocusInWindow();
    }

    private void pingServer() {
        pingServer(false);
    }

    private void pingServer(boolean registerPage) {
        JButton pingButton = registerPage ? buttonRegPing : buttonPing;
        final String host = serverHost();
        final int port;
        try {
            port = Integer.parseInt(serverPortText());
        } catch (NumberFormatException ex) {
            setLoginStatus("Ping失败：服务器配置异常");
            return;
        }

        pingButton.setEnabled(false);
        pingButton.setText("Ping...");
        new Thread(() -> {
            long start = System.nanoTime();
            String result;
            try (Socket socket = new Socket()) {
                socket.connect(new InetSocketAddress(host, port), ClientKernel.CONNECT_TIMEOUT_MS);
                long ms = (System.nanoTime() - start) / 1_000_000L;
                result = "服务器延迟 = " + ms + " ms";
            } catch (Exception ex) {
                result = "服务器 Ping 失败：" + ex.getMessage();
            }
            final String text = result;
            SwingUtilities.invokeLater(() -> {
                pingButton.setEnabled(true);
                pingButton.setText("Ping");
                if (ck == null || !ck.isConnected()) setLoginStatus(text);
                else addMsg("<div class='system'>" + escapeHtml(text) + "</div>");
            });
        }, "chat-ping").start();
    }

    private void send() {
        String toSend = msgWindow.getText();
        if (ck == null || !ck.isConnected() || toSend.trim().length() == 0) {
            return;
        }

        String conversation = selectedConversation();
        List<String> recipients = conversationRecipients(conversation);
        if (isPublicConversation(conversation)) {
            ck.sendMessage(toSend);
        } else if (isUserConversation(conversation)) {
            if (recipients.isEmpty()) {
                addMsg("<div class='system warn'>请选择一个私聊会话</div>");
                return;
            }
            ck.sendCommand("msg " + recipients.get(0) + " " + toSend);
        } else {
            if (recipients.isEmpty()) {
                addMsg("<div class='system warn'>请先组建一个群聊</div>");
                return;
            }
            ck.sendCommand("gmsg " + String.join(",", withoutSelf(recipients)) + " " + toSend);
        }

        noteConversation(conversation, "我：" + toSend);
        lastMsg = toSend;
        msgWindow.setText("");
    }

    private void updateChatTarget() {
        if (chatTargetLabel == null || chatTargetStatusLabel == null || userList == null) return;
        String conversation = selectedConversation();
        boolean group = isGroupConversation(conversation);
        boolean owner = isGroupOwner(conversation);
        if (buttonGroupMembers != null) buttonGroupMembers.setVisible(group);
        if (buttonRenameGroup != null) buttonRenameGroup.setVisible(owner);
        if (buttonDeleteGroup != null) buttonDeleteGroup.setVisible(owner);
        if (isPublicConversation(conversation)) {
            chatTargetLabel.setText("💬 公开频道");
            chatTargetStatusLabel.setText("所有在线用户可见");
        } else if (isUserConversation(conversation)) {
            chatTargetLabel.setText("🔒 " + conversationTitle(conversation));
            String uid = conversation.substring(CONV_USER_PREFIX.length());
            chatTargetStatusLabel.setText(friends.contains(uid.toLowerCase()) ? "★ 好友" : "私聊");
        } else {
            chatTargetLabel.setText("👥 " + conversationTitle(conversation));
            chatTargetStatusLabel.setText(String.join("、", displayNames(groupMemberIds(conversation))));
        }
        showConversation(conversation);
    }

    public void updateUsers(String[] users) {
        SwingUtilities.invokeLater(() -> {
            String selected = selectedConversation();
            onlineUsers.clear();
            for (String user : users) {
                String[] parts = user.trim().split("\\|", 2);
                String uid = parts.length == 2 ? parts[0].trim() : user.trim();
                String name = parts.length == 2 ? parts[1].trim() : user.trim();
                if (uid.length() == 0 || name.length() == 0) continue;
                rememberUser(uid, name);
                onlineUsers.add(uid);
                if (name.equalsIgnoreCase(currentNick())) selfUid = uid;
            }
            rebuildConversationModel(selected);
        });
    }

    public void loginOk(String uid, String nick) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> loginOk(uid, nick));
            return;
        }
        rememberUser(uid, nick);
        selfUid = uid;
        txtUserId.setText(uid);
        txtNick.setText(nick);
        ClientConfig.set("user.id", uid);
        ClientConfig.set("nick", nick);
        setLoginStatus("登录成功");
        setConnectionStatus(true, "已连接");
        updateStatusBar(txtHost.getText().trim(), nick);
        addMsg("<div class='system'><span class='sys-icon'>✓</span> 已登录服务器，ID: "
                + escapeHtml(uid) + "</div>");
    }

    public void registered(String uid, String nick) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> registered(uid, nick));
            return;
        }
        txtUserId.setText(uid);
        setLoginStatus("注册成功，系统分配ID: " + uid);
    }

    public void authFailed(String reason) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> authFailed(reason));
            return;
        }
        setConnectionStatus(false, "认证失败");
        String text = reason != null && reason.toLowerCase().contains("id or password")
                ? "该ID或密码输入错误，请重新输入。"
                : "认证失败: " + reason;
        setLoginStatus(text, new Color(210, 65, 65));
        if (txtPassword != null) {
            txtPassword.setText("");
            txtPassword.requestFocusInWindow();
        }
        if (ck != null) {
            ck.dropMe();
            ck = null;
        }
    }

    public void searchResult(String uid, String nick, boolean friend) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> searchResult(uid, nick, friend));
            return;
        }
        rememberUser(uid, nick);
        if (friend) friends.add(uid.toLowerCase());
        privateConversations.add(uidFor(uid).toLowerCase());
        String entry = userEntry(uid);
        if (!userModel.contains(entry)) userModel.addElement(entry);
        userList.setSelectedValue(entry, true);
        onlineTitleLabel.setText("会话 (" + userModel.size() + ")");
        noteConversation(entry, friend ? "好友" : "非好友，可私聊");
    }

    public void searchFailed(String id) {
        if (!SwingUtilities.isEventDispatchThread()) {
            SwingUtilities.invokeLater(() -> searchFailed(id));
            return;
        }
        addMsg("<div class='system warn'>未找到用户ID: " + escapeHtml(id) + "</div>");
    }

    private void setLoginStatus(String text) {
        setLoginStatus(text, new Color(120, 128, 140));
    }

    private void setLoginStatus(String text, Color color) {
        if (loginStatusLabel == null) return;
        loginStatusLabel.setForeground(color == null ? new Color(120, 128, 140) : color);
        loginStatusLabel.setText(text == null ? " " : text);
    }

    private void addFriendMark(String user) {
        if (user == null || user.trim().length() == 0) return;
        friends.add(uidFor(user).toLowerCase());
        userList.repaint();
    }

    private String selectedUser() {
        String selected = selectedConversation();
        if (!isUserConversation(selected)) {
            addMsg("<div class='system warn'><span class='sys-icon'>⚠</span> 请先选择一个私聊用户</div>");
            return null;
        }
        return selected.substring(CONV_USER_PREFIX.length());
    }

    private boolean ensureConnected() {
        if (ck != null && ck.isConnected()) return true;
        addMsg("<div class='system error'><span class='sys-icon'>✗</span> 当前未连接服务器</div>");
        return false;
    }

    private void addFriend() {
        if (!ensureConnected()) return;
        String selected = selectedUser();
        if (selected != null && ck != null) {
            addFriend(selected);
        }
    }

    private void addFriend(String uid) {
        if (!ensureConnected() || uid == null || uid.trim().length() == 0) return;
        ck.sendCommand("friend add " + uid);
        addMsg("<div class='system'><span class='sys-icon'>✓</span> 已发送好友请求给 "
                + escapeHtml(displayName(uid)) + "</div>");
    }

    private void acceptFriend(String user) {
        if (!ensureConnected()) return;
        ck.sendCommand("friend accept " + user);
    }

    private void saveProfile() {
        if (!ensureConnected()) return;
        JPanel form = new JPanel(new GridLayout(0, 2, 8, 8));
        JTextField nickInput = new JTextField(txtNick.getText().trim());
        JComboBox<String> avatarInput = avatarCombo(avatarFor(currentNick()));
        JTextField introInput = new JTextField("");
        form.add(new JLabel("昵称"));
        form.add(nickInput);
        form.add(new JLabel("头像"));
        form.add(avatarInput);
        form.add(new JLabel("个人签名"));
        form.add(introInput);
        int ok = JOptionPane.showConfirmDialog(this, form, "编辑我的资料",
                JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE);
        if (ok != JOptionPane.OK_OPTION) return;

        String newNick = nickInput.getText().trim();
        String avatar = validAvatar((String) avatarInput.getSelectedItem());
        String intro = introInput.getText().trim();
        if (newNick.length() == 0) {
            addMsg("<div class='system error'><span class='sys-icon'>✗</span> 昵称不能为空</div>");
            return;
        }
        if (hasBadProfileChars(newNick) || hasBadProfileChars(avatar) || hasBadProfileChars(intro)) {
            addMsg("<div class='system error'><span class='sys-icon'>✗</span> 资料中不能包含 | , ;，字段名不能有空格</div>");
            return;
        }
        if (!newNick.equals(txtNick.getText().trim())) {
            txtNick.setText(newNick);
            ck.setNick(newNick);
            ClientConfig.set("nick", newNick);
        }
        rememberUser(currentUid(), newNick);
        updateStatusBar("", newNick);
        userAvatars.put(currentUid().toLowerCase(), avatar);
        userAvatars.put(newNick.toLowerCase(), avatar);
        ClientConfig.set("avatar", avatar);
        ck.sendCommand("profile set avatar=" + avatar);
        if (intro.length() > 0) ck.sendCommand("profile set intro=" + intro);
        addMsg("<div class='system'>资料已提交保存</div>");
    }

    private boolean hasBadProfileChars(String value) {
        return value.indexOf('|') >= 0 || value.indexOf(',') >= 0 || value.indexOf(';') >= 0;
    }

    private void viewProfile() {
        if (!ensureConnected()) return;
        String selected = selectedUser();
        if (selected == null) return;
        addMsg("<div class='system profile-tip'>正在查看 "
                + escapeHtml(displayName(selected) + " 的") + "资料...</div>");
        ck.sendCommand("profile view " + selected);
    }

    private void searchUser() {
        if (!ensureConnected()) return;
        String id = txtSearchId.getText().trim();
        if (id.length() == 0) {
            addMsg("<div class='system warn'>请输入用户ID</div>");
            return;
        }
        ck.sendCommand("search " + id);
    }

    private void openPrivateConversation(String user) {
        String uid = uidFor(user);
        if (uid.length() == 0 || sameUser(uid, currentUid())) return;
        String entry = userEntry(uid);
        privateConversations.add(uid.toLowerCase());
        if (!userModel.contains(entry)) {
            userModel.addElement(entry);
            onlineTitleLabel.setText("会话 (" + userModel.size() + ")");
        }
        userList.setSelectedValue(entry, true);
        showConversation(entry);
    }

    private void showPublicMembers() {
        if (!ensureConnected()) return;
        List<String> members = withoutSelf(onlineUsers);
        JDialog dialog = new JDialog(this, "公开频道成员", true);
        JPanel list = new JPanel();
        list.setLayout(new BoxLayout(list, BoxLayout.Y_AXIS));
        list.setBackground(Color.WHITE);
        if (members.isEmpty()) {
            JLabel empty = new JLabel("当前没有其他在线成员");
            empty.setBorder(BorderFactory.createEmptyBorder(18, 22, 18, 22));
            list.add(empty);
        } else {
            for (String uid : members) list.add(publicMemberRow(uid, dialog));
        }
        JScrollPane scroll = new JScrollPane(list);
        scroll.setBorder(null);
        scroll.getVerticalScrollBar().setUnitIncrement(16);
        dialog.add(scroll, BorderLayout.CENTER);
        JButton close = createGrayButton("关闭");
        close.addActionListener(e -> dialog.dispose());
        JPanel footer = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        footer.add(close);
        dialog.add(footer, BorderLayout.SOUTH);
        dialog.setSize(420, Math.min(420, Math.max(180, 86 * Math.max(1, members.size()) + 70)));
        dialog.setLocationRelativeTo(this);
        dialog.setVisible(true);
    }

    private JPanel publicMemberRow(String uid, JDialog dialog) {
        JPanel row = new JPanel(new BorderLayout(10, 0));
        row.setBackground(Color.WHITE);
        row.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createMatteBorder(0, 0, 1, 0, COLOR_BORDER),
                BorderFactory.createEmptyBorder(8, 10, 8, 10)
        ));
        JLabel avatar = new JLabel(scaledAvatarIcon(avatarFor(uid), 42));
        avatar.setPreferredSize(new Dimension(46, 46));
        row.add(avatar, BorderLayout.WEST);

        JPanel info = new JPanel(new GridLayout(2, 1, 0, 2));
        info.setOpaque(false);
        JLabel name = new JLabel(displayName(uid));
        name.setFont(FONT_MAIN);
        JLabel id = new JLabel("ID: " + uid);
        id.setFont(FONT_SMALL);
        id.setForeground(new Color(135, 145, 158));
        info.add(name);
        info.add(id);
        row.add(info, BorderLayout.CENTER);

        JPanel actions = new JPanel(new FlowLayout(FlowLayout.RIGHT, 6, 4));
        actions.setOpaque(false);
        JButton chat = createGreenButton("私聊");
        chat.setFont(FONT_SMALL);
        chat.addActionListener(e -> {
            openPrivateConversation(uid);
            dialog.dispose();
        });
        JButton friend = createGrayButton("加好友");
        friend.addActionListener(e -> addFriend(uid));
        actions.add(chat);
        actions.add(friend);
        row.add(actions, BorderLayout.EAST);
        return row;
    }

    private void sendAttachment(boolean image) {
        if (!ensureConnected()) return;
        String conversation = selectedConversation();
        List<String> recipients = conversationRecipients(conversation);
        if (recipients.isEmpty() || ck == null) {
            addMsg("<div class='system warn'>请选择私聊或群聊会话；附件不发送到公开频道</div>");
            return;
        }

        JFileChooser chooser = new JFileChooser();
        chooser.setDialogTitle(image ? "选择图片发送" : "选择文件发送");
        if (chooser.showOpenDialog(this) != JFileChooser.APPROVE_OPTION) return;

        try {
            File file = chooser.getSelectedFile();
            if (file.length() > ClientKernel.MAX_FILE_SIZE) {
                addMsg("<div class='system error'><span class='sys-icon'>✗</span> 文件超过 "
                        + (ClientKernel.MAX_FILE_SIZE / 1024 / 1024) + "MB 限制</div>");
                return;
            }
            String data = Base64.getEncoder().encodeToString(Files.readAllBytes(file.toPath()));
            List<String> targets = isGroupConversation(conversation) ? withoutSelf(recipients) : recipients;
            for (String user : targets) {
                ck.sendCommand((image ? "image " : "file ") + user + " " + file.getName() + "|" + data);
            }
            noteConversation(conversation, "我：" + (image ? "[图片] " : "[文件] ") + file.getName());
        } catch (Exception ex) {
            addMsg("<div class='system error'><span class='sys-icon'>✗</span> 附件发送失败: " + escapeHtml(ex.getMessage()) + "</div>");
        }
    }

    private void createGroup() {
        if (!ensureConnected()) return;

        DefaultListModel<String> availableModel = new DefaultListModel<String>();
        DefaultListModel<String> selectedModel = new DefaultListModel<String>();
        String self = currentUid();
        for (String uid : onlineUsers) {
            if (uid.length() > 0 && !sameUser(uid, self) && friends.contains(uid.toLowerCase())) {
                availableModel.addElement(displayName(uid));
            }
        }
        if (availableModel.isEmpty()) {
            addMsg("<div class='system warn'>当前没有可加入群聊的好友</div>");
            return;
        }

        JList<String> availableList = new JList<String>(availableModel);
        JList<String> selectedList = new JList<String>(selectedModel);
        availableList.setSelectionMode(ListSelectionModel.MULTIPLE_INTERVAL_SELECTION);
        selectedList.setSelectionMode(ListSelectionModel.MULTIPLE_INTERVAL_SELECTION);
        availableList.setVisibleRowCount(Math.min(8, availableModel.size()));
        selectedList.setVisibleRowCount(Math.min(8, availableModel.size()));
        JButton addMember = createGrayButton("添加 >");
        JButton removeMember = createGrayButton("< 移除");
        addMember.addActionListener(ev -> {
            for (String user : availableList.getSelectedValuesList()) {
                if (!selectedModel.contains(user)) selectedModel.addElement(user);
            }
        });
        removeMember.addActionListener(ev -> {
            List<String> selectedUsers = selectedList.getSelectedValuesList();
            for (String user : selectedUsers) selectedModel.removeElement(user);
        });
        JTextField groupName = new JTextField();

        JPanel form = new JPanel(new BorderLayout(0, 8));
        form.add(new JLabel("选择群成员"), BorderLayout.NORTH);
        JPanel buttons = new JPanel(new GridLayout(0, 1, 0, 8));
        buttons.add(addMember);
        buttons.add(removeMember);
        JPanel lists = new JPanel(new GridLayout(1, 3, 10, 0));
        lists.add(wrapList("好友/在线用户", availableList));
        lists.add(buttons);
        lists.add(wrapList("群成员", selectedList));
        JPanel namePanel = new JPanel(new BorderLayout(8, 0));
        namePanel.add(new JLabel("群聊名称"), BorderLayout.WEST);
        namePanel.add(groupName, BorderLayout.CENTER);
        form.setPreferredSize(new Dimension(520, 330));
        form.add(namePanel, BorderLayout.NORTH);
        form.add(lists, BorderLayout.CENTER);

        int ok = JOptionPane.showConfirmDialog(this, form, "组建群聊",
                JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE);
        if (ok != JOptionPane.OK_OPTION) return;

        List<String> members = new ArrayList<String>();
        for (int i = 0; i < selectedModel.size(); i++) members.add(uidFor(selectedModel.get(i)));
        if (!members.contains(currentUid())) members.add(currentUid());
        members = canonicalIds(members);
        if (members.isEmpty()) {
            addMsg("<div class='system warn'>至少选择一个群成员</div>");
            return;
        }
        String title = groupName.getText().trim();
        if (title.length() == 0) title = "群聊 " + String.join("、", displayNames(members));

        String entry = groupEntry(title, members);
        if (!groupEntries.contains(entry)) groupEntries.add(entry);
        groupOwners.put(entry, currentUid().toLowerCase());
        noteConversation(entry, "群聊已创建");
        rebuildConversationModel(entry);
    }

    private JPanel wrapList(String title, JList<String> list) {
        JPanel panel = new JPanel(new BorderLayout(0, 6));
        JLabel label = new JLabel(title);
        label.setFont(FONT_SMALL);
        panel.add(label, BorderLayout.NORTH);
        panel.add(new JScrollPane(list), BorderLayout.CENTER);
        return panel;
    }

    private boolean isGroupOwner(String conversation) {
        if (!isGroupConversation(conversation)) return false;
        String owner = groupOwners.get(conversation);
        return owner != null && owner.equalsIgnoreCase(currentUid());
    }

    private void deleteSelectedGroup() {
        String conversation = selectedConversation();
        if (!isGroupConversation(conversation)) return;
        if (!isGroupOwner(conversation)) {
            addMsg("<div class='system warn'>只有群主可以删除群聊</div>");
            return;
        }
        int ok = JOptionPane.showConfirmDialog(this,
                "确定删除群聊 \"" + conversationTitle(conversation) + "\" 吗？",
                "删除群聊",
                JOptionPane.OK_CANCEL_OPTION,
                JOptionPane.WARNING_MESSAGE);
        if (ok != JOptionPane.OK_OPTION) return;
        groupEntries.remove(conversation);
        groupOwners.remove(conversation);
        conversationLast.remove(conversation);
        conversationTime.remove(conversation);
        conversationLogs.remove(conversation);
        rebuildConversationModel(CONV_PUBLIC);
        addMsg("<div class='system'>群聊已删除</div>");
    }

    private void renameSelectedGroup() {
        String conversation = selectedConversation();
        if (!isGroupConversation(conversation)) return;
        if (!isGroupOwner(conversation)) {
            addMsg("<div class='system warn'>只有群主可以修改群名</div>");
            return;
        }
        String name = JOptionPane.showInputDialog(this, "输入新的群聊名称", conversationTitle(conversation));
        if (name == null) return;
        name = name.replace('|', ' ').trim();
        if (name.length() == 0) {
            addMsg("<div class='system warn'>群名不能为空</div>");
            return;
        }
        String renamed = renameGroupConversation(conversation, name);
        List<String> targets = withoutSelf(conversationRecipients(renamed));
        if (ck != null && ck.isConnected() && !targets.isEmpty()) {
            String encoded = Base64.getUrlEncoder().withoutPadding()
                    .encodeToString(name.getBytes(StandardCharsets.UTF_8));
            ck.sendCommand("gmsg " + String.join(",", targets) + " " + GROUP_RENAME_PREFIX + encoded);
        }
    }

    private void showGroupMembers() {
        String conversation = selectedConversation();
        if (!isGroupConversation(conversation)) return;
        StringBuilder text = new StringBuilder();
        for (String uid : groupMemberIds(conversation)) {
            text.append(displayName(uid)).append("  (").append(uid).append(")");
            if (uid.equalsIgnoreCase(groupOwners.get(conversation))) text.append("  群主");
            text.append('\n');
        }
        JOptionPane.showMessageDialog(this, text.length() == 0 ? "暂无成员" : text.toString(),
                "群成员 - " + conversationTitle(conversation), JOptionPane.INFORMATION_MESSAGE);
    }

    private String renameGroupConversation(String conversation, String newTitle) {
        if (!isGroupConversation(conversation)) return conversation;
        String cleanTitle = newTitle == null ? "" : newTitle.replace('|', ' ').trim();
        if (cleanTitle.length() == 0) return conversation;
        String renamed = groupEntry(cleanTitle, conversationRecipients(conversation));
        if (renamed.equals(conversation)) return conversation;

        int index = groupEntries.indexOf(conversation);
        if (index >= 0) groupEntries.set(index, renamed);
        else if (!groupEntries.contains(renamed)) groupEntries.add(renamed);
        String owner = groupOwners.remove(conversation);
        if (owner != null) groupOwners.put(renamed, owner);
        moveMapKey(conversationLast, conversation, renamed);
        moveMapKey(conversationTime, conversation, renamed);
        moveMapKey(conversationLogs, conversation, renamed);
        rebuildConversationModel(renamed);
        return renamed;
    }

    private <T> void moveMapKey(Map<String, T> map, String oldKey, String newKey) {
        if (!map.containsKey(oldKey)) return;
        T value = map.remove(oldKey);
        map.put(newKey, value);
    }

    private String decodeGroupName(String encoded) {
        try {
            return new String(Base64.getUrlDecoder().decode(encoded), StandardCharsets.UTF_8).trim();
        } catch (Exception ex) {
            return encoded == null ? "" : encoded.trim();
        }
    }

    public void noteChat(String sender, String target, String message) {
        String conversation = conversationForChat(sender, target);
        noteConversation(conversation, (sameUser(sender, currentUid()) ? "我" : displayName(sender)) + "：" + message);
    }

    private String conversationForChat(String sender, String target) {
        return conversationForChat(uidFor(sender), sender, uidFor(target), target);
    }

    private String conversationForChat(String senderUid, String senderNick, String targetId, String targetTitle) {
        if (isPublicConversationId(targetId) || "全部".equals(targetTitle)) {
            return CONV_PUBLIC;
        } else if (isGroupConversationId(targetId) || (targetTitle != null && targetTitle.startsWith("群聊("))) {
            return groupConversationFor(senderUid, targetId, targetTitle);
        } else {
            String other = sameUser(targetId, currentUid()) ? senderUid : targetId;
            return userEntry(uidFor(other));
        }
    }

    public void noteAttachment(String sender, String fileName, boolean image) {
        String conversation = conversationForAttachment(sender);
        noteConversation(conversation, (sameUser(sender, currentUid()) ? "我" : displayName(sender))
                + "：" + (image ? "[图片] " : "[文件] ") + fileName);
    }

    private String conversationForAttachment(String sender) {
        String self = currentUid();
        if (sameUser(sender, self) && isGroupConversation(selectedConversation())) {
            return selectedConversation();
        }
        return userEntry(sameUser(sender, self) ? selectedUserForFallback() : uidFor(sender));
    }

    private String selectedUserForFallback() {
        String selected = selectedConversation();
        List<String> recipients = conversationRecipients(selected);
        return recipients.isEmpty() ? currentUid() : recipients.get(0);
    }

    private void noteConversation(String conversation, String preview) {
        SwingUtilities.invokeLater(() -> {
            String text = preview == null ? "" : preview.replace('\n', ' ');
            if (text.length() > 26) text = text.substring(0, 26) + "...";
            conversationLast.put(conversation, text);
            conversationTime.put(conversation, new SimpleDateFormat("HH:mm").format(new Date()));
            if (isUserConversation(conversation)) {
                privateConversations.add(conversation.substring(CONV_USER_PREFIX.length()).toLowerCase());
            }
            if (!userModel.contains(conversation)) {
                if (isGroupConversation(conversation) && !groupEntries.contains(conversation)) {
                    groupEntries.add(conversation);
                }
                userModel.addElement(conversation);
                onlineTitleLabel.setText("会话 (" + userModel.size() + ")");
            }
            userList.repaint();
        });
    }

    private void showConversation(String conversation) {
        if (historyWindow == null) return;
        StringBuilder html = conversationLogs.get(conversation == null ? CONV_PUBLIC : conversation);
        historyWindow.setBody(html == null ? "" : html.toString());
    }

    private void rebuildConversationModel(String selected) {
        if (userModel == null) return;
        userModel.clear();
        userModel.addElement(CONV_PUBLIC);

        String self = currentUid();
        for (String uid : privateConversations) {
            if (uid.length() > 0 && !sameUser(uid, self)) {
                userModel.addElement(userEntry(uid));
            }
        }
        for (String group : groupEntries) {
            if (!userModel.contains(group)) userModel.addElement(group);
        }

        onlineTitleLabel.setText("会话 (" + userModel.size() + ")");
        int index = userModel.indexOf(selected);
        userList.setSelectedIndex(index >= 0 ? index : 0);
        userList.repaint();
        updateChatTarget();
    }

    private String selectedConversation() {
        if (userList == null) return CONV_PUBLIC;
        String selected = userList.getSelectedValue();
        return selected == null ? CONV_PUBLIC : selected;
    }

    private boolean isPublicConversation(String entry) {
        return entry == null || entry.startsWith("public:");
    }

    private boolean isUserConversation(String entry) {
        return entry != null && entry.startsWith(CONV_USER_PREFIX);
    }

    private boolean isGroupConversation(String entry) {
        return entry != null && entry.startsWith(CONV_GROUP_PREFIX);
    }

    private String userEntry(String user) {
        return CONV_USER_PREFIX + uidFor(user);
    }

    private String groupEntry(String title, List<String> members) {
        String safeTitle = title.replace('|', ' ').trim();
        return CONV_GROUP_PREFIX + safeTitle + "|" + String.join(",", canonicalIds(members));
    }

    private String conversationTitle(String entry) {
        if (isPublicConversation(entry)) return "公开频道";
        if (isUserConversation(entry)) return displayName(entry.substring(CONV_USER_PREFIX.length()));
        if (isGroupConversation(entry)) {
            String body = entry.substring(CONV_GROUP_PREFIX.length());
            int sep = body.indexOf('|');
            return sep >= 0 ? body.substring(0, sep) : body;
        }
        return entry == null ? "" : entry;
    }

    private List<String> conversationRecipients(String entry) {
        List<String> recipients = new ArrayList<String>();
        if (isUserConversation(entry)) {
            recipients.add(entry.substring(CONV_USER_PREFIX.length()));
        } else if (isGroupConversation(entry)) {
            String body = entry.substring(CONV_GROUP_PREFIX.length());
            int sep = body.indexOf('|');
            if (sep >= 0) {
                for (String user : body.substring(sep + 1).split(",")) {
                    if (user.trim().length() > 0) recipients.add(user.trim());
                }
            }
        }
        return recipients;
    }

    private String conversationAvatar(String entry) {
        if (isPublicConversation(entry)) return "公";
        if (isGroupConversation(entry)) return "群";
        String title = conversationTitle(entry);
        return title.length() == 0 ? "人" : title.substring(0, 1).toUpperCase();
    }

    private ImageIcon conversationAvatarIcon(String entry) {
        return compositeAvatarIcon(conversationAvatarUsers(entry), 42);
    }

    private List<String> conversationAvatarUsers(String entry) {
        List<String> users = new ArrayList<String>();
        if (isPublicConversation(entry)) {
            users.addAll(canonicalIds(onlineUsers));
        } else if (isGroupConversation(entry)) {
            users.addAll(groupMemberIds(entry));
        } else if (isUserConversation(entry)) {
            users.add(entry.substring(CONV_USER_PREFIX.length()));
        } else {
            users.add(currentUid());
        }
        return users;
    }

    private String defaultConversationSubtitle(String entry) {
        if (isPublicConversation(entry)) return "全部在线成员";
        if (isGroupConversation(entry)) return String.join("、", displayNames(groupMemberIds(entry)));
        return "在线";
    }

    private List<String> groupMemberIds(String entry) {
        List<String> members = canonicalIds(conversationRecipients(entry));
        String self = currentUid();
        if (self.length() > 0 && !containsUser(members, self)) members.add(self);
        return canonicalIds(members);
    }

    private List<String> withoutSelf(List<String> users) {
        List<String> result = new ArrayList<String>();
        String self = currentUid();
        for (String user : canonicalIds(users)) {
            if (!sameUser(user, self)) result.add(user);
        }
        return result;
    }

    private boolean containsUser(List<String> users, String user) {
        for (String item : users) {
            if (sameUser(item, user)) return true;
        }
        return false;
    }

    private String groupConversationFor(String sender, String targetId, String targetTitle) {
        LinkedHashSet<String> replyMembers = new LinkedHashSet<String>();
        if (isGroupConversationId(targetId)) {
            for (String id : targetId.substring("group:".length()).split(",")) {
                String uid = uidFor(id.trim());
                if (uid.length() > 0) replyMembers.add(uid);
            }
        } else {
            String self = currentUid();
            if (sender != null && !sameUser(sender, self)) replyMembers.add(uidFor(sender));
            int left = targetTitle == null ? -1 : targetTitle.indexOf('(');
            int right = targetTitle == null ? -1 : targetTitle.lastIndexOf(')');
            if (left >= 0 && right > left) {
                for (String member : targetTitle.substring(left + 1, right).split(",")) {
                    String uid = uidFor(member.trim());
                    if (uid.length() > 0) replyMembers.add(uid);
                }
            }
        }

        List<String> members = new ArrayList<String>(replyMembers);
        for (String entry : groupEntries) {
            if (sameRecipients(conversationRecipients(entry), members)) return entry;
        }

        String entry = groupEntry(targetTitle != null && targetTitle.length() > 0
                ? targetTitle : "群聊 " + String.join("、", displayNames(members)), members);
        if (!groupEntries.contains(entry)) groupEntries.add(entry);
        if (sender != null && sender.length() > 0) {
            groupOwners.putIfAbsent(entry, uidFor(sender).toLowerCase());
        }
        return entry;
    }

    private boolean sameRecipients(List<String> a, List<String> b) {
        if (a.size() != b.size()) return false;
        Set<String> aa = new HashSet<String>();
        Set<String> bb = new HashSet<String>();
        for (String item : a) aa.add(uidFor(item).toLowerCase());
        for (String item : b) bb.add(uidFor(item).toLowerCase());
        aa.add(currentUid().toLowerCase());
        bb.add(currentUid().toLowerCase());
        return aa.equals(bb);
    }

    private String currentNick() {
        String nick = txtNick == null ? "" : txtNick.getText().trim();
        return nick.length() == 0 ? nickText : nick;
    }

    private String currentUid() {
        return selfUid == null || selfUid.length() == 0 ? currentNick() : selfUid;
    }

    private void rememberUser(String uid, String nick) {
        if (uid == null || uid.trim().length() == 0 || nick == null || nick.trim().length() == 0) return;
        String cleanUid = uid.trim();
        String cleanNick = nick.trim();
        nickByUid.put(cleanUid, cleanNick);
        uidByNick.put(cleanNick.toLowerCase(), cleanUid);
    }

    private String uidFor(String uidOrNick) {
        if (uidOrNick == null) return "";
        String value = uidOrNick.trim();
        if (value.length() == 0) return "";
        if (nickByUid.containsKey(value)) return value;
        String uid = uidByNick.get(value.toLowerCase());
        return uid == null ? value : uid;
    }

    private String displayName(String uidOrNick) {
        if (uidOrNick == null) return "";
        String value = uidOrNick.trim();
        String nick = nickByUid.get(value);
        return nick == null ? value : nick;
    }

    private List<String> displayNames(List<String> users) {
        List<String> names = new ArrayList<String>();
        for (String user : users) names.add(displayName(user));
        return names;
    }

    private List<String> canonicalIds(List<String> users) {
        List<String> ids = new ArrayList<String>();
        for (String user : users) {
            String uid = uidFor(user);
            if (uid.length() > 0 && !ids.contains(uid)) ids.add(uid);
        }
        java.util.Collections.sort(ids, String.CASE_INSENSITIVE_ORDER);
        return ids;
    }

    private boolean sameUser(String a, String b) {
        String aa = uidFor(a);
        String bb = uidFor(b);
        return aa.length() > 0 && aa.equalsIgnoreCase(bb);
    }

    private boolean isPublicConversationId(String id) {
        return id == null || "public".equalsIgnoreCase(id) || "全部".equals(id);
    }

    private boolean isGroupConversationId(String id) {
        return id != null && id.startsWith("group:");
    }

    private String chatHtml(String sender, String target, String message) {
        boolean mine = sameUser(sender, currentUid());
        return "<div class='msg-wrapper " + (mine ? "self" : "other") + "'>"
                + "<div class='msg-info'>" + avatarToken(sender) + " "
                + senderNameHtml(sender, mine) + " · " + escapeHtml(target) + "</div>"
                + "<div class='msg-bubble'>" + escapeHtml(message) + "</div></div>";
    }

    private String decorateAvatar(String html, String sender) {
        if (html == null) return "";
        return html.replace("<div class='msg-info'>", "<div class='msg-info'>" + avatarToken(sender) + " ");
    }

    private String senderNameHtml(String sender, boolean mine) {
        if (mine) return "我";
        String name = displayName(sender);
        return "<a href=\"chat:" + escapeHtml(uidFor(sender)) + "\">" + escapeHtml(name) + "</a>";
    }

    private String avatarImg(String user) {
        return "<img src=\"" + avatarFile(avatarFor(user)).toURI().toString()
                + "\" width=\"28\" height=\"28\" align=\"middle\">";
    }

    private String avatarToken(String user) {
        String name = user == null ? "" : user;
        return "@@AVATAR:" + Base64.getUrlEncoder().withoutPadding()
                .encodeToString(name.getBytes(StandardCharsets.UTF_8)) + "@@";
    }

    private String resolveAvatarTokens(String html) {
        if (html == null || html.indexOf("@@AVATAR:") < 0) return html == null ? "" : html;
        Matcher matcher = AVATAR_TOKEN.matcher(html);
        StringBuffer out = new StringBuffer();
        while (matcher.find()) {
            String user = new String(Base64.getUrlDecoder().decode(matcher.group(1)), StandardCharsets.UTF_8);
            matcher.appendReplacement(out, Matcher.quoteReplacement(avatarImg(user)));
        }
        matcher.appendTail(out);
        return out.toString();
    }

    private String avatarFor(String user) {
        String uid = uidFor(user);
        String saved = uid.length() == 0 ? null : userAvatars.get(uid.toLowerCase());
        if (saved == null && user != null) saved = userAvatars.get(user.trim().toLowerCase());
        if (saved == null && sameUser(uid, currentUid())) {
            saved = ClientConfig.get("avatar", DEFAULT_AVATAR);
        }
        return validAvatar(saved);
    }

    private String validAvatar(String avatar) {
        if (avatar == null || avatar.trim().length() == 0) return DEFAULT_AVATAR;
        String name = new File(avatar.trim()).getName();
        File file = avatarFile(name);
        return file.exists() && isSquarePng(file) ? name : DEFAULT_AVATAR;
    }

    private File avatarFile(String avatar) {
        return new File("avatar", avatar == null ? DEFAULT_AVATAR : avatar);
    }

    private List<String> avatarChoices() {
        List<String> names = new ArrayList<String>();
        File[] files = new File("avatar").listFiles((dir, name) ->
                name.toLowerCase().endsWith(".png") && !name.startsWith("_"));
        if (files != null) {
            java.util.Arrays.sort(files, (a, b) -> a.getName().compareToIgnoreCase(b.getName()));
            for (File file : files) {
                if (isSquarePng(file)) names.add(file.getName());
            }
        }
        if (names.isEmpty()) names.add(DEFAULT_AVATAR);
        return names;
    }

    private boolean isSquarePng(File file) {
        ImageIcon icon = new ImageIcon(file.getAbsolutePath());
        return icon.getIconWidth() > 0 && icon.getIconWidth() == icon.getIconHeight();
    }

    private ImageIcon scaledAvatarIcon(String avatar, int size) {
        ImageIcon icon = new ImageIcon(avatarFile(avatar).getAbsolutePath());
        Image image = icon.getImage().getScaledInstance(size, size, Image.SCALE_SMOOTH);
        return new ImageIcon(image);
    }

    private ImageIcon compositeAvatarIcon(List<String> users, int size) {
        if (users == null || users.isEmpty()) users = java.util.Collections.singletonList(currentUid());
        BufferedImage image = new BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = image.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(new Color(232, 236, 244));
        g.fillRoundRect(0, 0, size, size, 4, 4);

        int count = Math.max(1, Math.min(9, users.size()));
        if (count == 1) {
            drawAvatarCell(g, users.get(0), 0, 0, size);
            g.dispose();
            return new ImageIcon(image);
        }

        int cols = count <= 4 ? 2 : 3;
        int rows = count == 2 ? 1 : (int) Math.ceil(count / (double) cols);
        int gap = 2;
        int cell = Math.min((size - (cols - 1) * gap) / cols, (size - (rows - 1) * gap) / rows);
        int startX = (size - (cols * cell + (cols - 1) * gap)) / 2;
        int startY = (size - (rows * cell + (rows - 1) * gap)) / 2;
        for (int i = 0; i < count; i++) {
            int row = i / cols;
            int col = i % cols;
            drawAvatarCell(g, users.get(i), startX + col * (cell + gap), startY + row * (cell + gap), cell);
        }
        g.dispose();
        return new ImageIcon(image);
    }

    private void drawAvatarCell(Graphics2D g, String user, int x, int y, int size) {
        ImageIcon icon = new ImageIcon(avatarFile(avatarFor(user)).getAbsolutePath());
        g.drawImage(icon.getImage(), x, y, size, size, null);
    }

    private JComboBox<String> avatarCombo(String selected) {
        JComboBox<String> combo = new JComboBox<String>(avatarChoices().toArray(new String[0]));
        combo.setSelectedItem(validAvatar(selected));
        combo.setRenderer(new DefaultListCellRenderer() {
            public Component getListCellRendererComponent(JList<?> list, Object value, int index,
                                                          boolean isSelected, boolean cellHasFocus) {
                JLabel label = (JLabel) super.getListCellRendererComponent(list, value, index, isSelected, cellHasFocus);
                String name = value == null ? DEFAULT_AVATAR : value.toString();
                label.setIcon(scaledAvatarIcon(name, 32));
                label.setText(name);
                label.setBorder(BorderFactory.createEmptyBorder(3, 6, 3, 6));
                return label;
            }
        });
        combo.setMaximumRowCount(10);
        return combo;
    }

    private Map<String, String> profileFields(String rawProfile) {
        Map<String, String> fields = new HashMap<String, String>();
        if (rawProfile == null || rawProfile.trim().length() == 0 || "暂无资料".equals(rawProfile)) return fields;
        for (String item : rawProfile.split(";")) {
            int eq = item.indexOf('=');
            if (eq > 0) fields.put(item.substring(0, eq), item.substring(eq + 1));
        }
        return fields;
    }

    private String profileHtml(String visibleUid, String nick, Map<String, String> fields) {
        String name = nick == null ? "" : nick;
        StringBuilder html = new StringBuilder();
        html.append("<div class='profile-card'>")
                .append(avatarToken(name)).append(" <span class='profile-title'>个人资料 - ")
                .append(escapeHtml(name)).append("</span>");
        if (visibleUid != null && visibleUid.length() > 0) {
            html.append("<br><font color=\"#666666\">UID：</font>").append(escapeHtml(visibleUid));
        }
        if (fields.isEmpty()) {
            html.append("<br><font color=\"#888888\">暂无资料</font>");
        } else {
            for (Map.Entry<String, String> entry : fields.entrySet()) {
                html.append("<br><font color=\"#666666\">")
                        .append(escapeHtml(profileFieldLabel(entry.getKey()))).append("：</font>")
                        .append(escapeHtml(entry.getValue()));
            }
        }
        html.append("</div>");
        return html.toString();
    }

    private String profileFieldLabel(String field) {
        if ("avatar".equals(field)) return "头像";
        if ("intro".equals(field)) return "个人签名";
        if ("city".equals(field)) return "城市";
        if ("phone".equals(field)) return "电话";
        if ("email".equals(field)) return "邮箱";
        return field == null ? "" : field;
    }

    private void showUserCard(String user) {
        if (user == null || user.trim().length() == 0) return;
        String name = user.trim();
        JPanel card = new JPanel(new BorderLayout(12, 0));
        JLabel avatar = new JLabel(scaledAvatarIcon(avatarFor(name), 96));
        avatar.setPreferredSize(new Dimension(104, 104));
        avatar.setOpaque(true);
        avatar.setBackground(new Color(232, 236, 244));
        avatar.setBorder(new LineBorder(new Color(210, 216, 228), 1, true));
        avatar.setFont(new Font("微软雅黑", Font.BOLD, 22));

        JLabel info = new JLabel("<html><div style='font-size:15px;font-weight:bold;'>"
                + escapeHtml(name)
                + "</div><br><font color='#888888'>昵称：</font>"
                + escapeHtml(name)
                + (friends.contains(uidFor(name).toLowerCase())
                ? "<br><font color='#888888'>UID：</font>" + escapeHtml(uidFor(name)) : "")
                + "</html>");
        card.add(avatar, BorderLayout.WEST);
        card.add(info, BorderLayout.CENTER);
        JOptionPane.showMessageDialog(this, card, "个人资料", JOptionPane.PLAIN_MESSAGE);
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

    private String currentTimeText() {
        return new SimpleDateFormat("HH:mm:ss").format(new Date());
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
            if (e.getSource() == txtHost) {
                txtPort.requestFocus();
            }
            if (e.getSource() == txtPort) {
                txtUserId.requestFocus();
            }
            if (e.getSource() == txtUserId) {
                txtPassword.requestFocus();
            }
            if (e.getSource() == txtPassword) {
                connect(false);
            }
            if (e.getSource() == txtRegHost) {
                txtRegPort.requestFocus();
            }
            if (e.getSource() == txtRegPort) {
                txtRegNick.requestFocus();
            }
            if (e.getSource() == txtRegNick) {
                txtRegPassword.requestFocus();
            }
            if (e.getSource() == txtRegPassword) {
                connect(true);
            }
        }
    }

    public void actionPerformed(ActionEvent e) {
        Object src = e.getSource();
        String cmd = e.getActionCommand();

        if (src == buttonConnect || src == buttonTopDisconnect) {
            if (buttonConnect.getText().equals("断开")) {
                disconnect();
            } else {
                connect(false);
            }
        } else if (src == buttonRegister) {
            connect(true);
        } else if (src == buttonShowRegister) {
            showRegisterPage();
        } else if (src == buttonShowLogin) {
            showLoginPage();
        } else if (src == buttonPing) {
            pingServer();
        } else if (src == buttonRegPing) {
            pingServer(true);
        } else if (src == buttonSearchUser) {
            searchUser();
        } else if (src == buttonSend) {
            send();
        } else if (src == buttonFriend) {
            addFriend();
        } else if (src == buttonCreateGroup) {
            createGroup();
        } else if (src == buttonRenameGroup) {
            renameSelectedGroup();
        } else if (src == buttonGroupMembers) {
            showGroupMembers();
        } else if (src == buttonDeleteGroup) {
            deleteSelectedGroup();
        } else if (src == buttonProfileSave) {
            saveProfile();
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
        if (e.getSource() == txtNick && txtNick.getText().equals("")) {
            txtNick.setText(ChatClient.nickText);
        }
    }

    // ================================================
    //  9. 内部类：聊天记录展示组件
    // ================================================

    class ClientHistory extends JEditorPane {
        private static final String CSS_STYLE =
                "<style>"
                        + "body { font-family: '微软雅黑', 'PingFang SC', sans-serif; font-size: 14px; line-height: 1.6; padding: 12px; margin: 0; background: #f6f8fb; }"
                        + ".msg-wrapper { display: block; margin-bottom: 12px; }"
                        + ".self { text-align: right; }"
                        + ".other { text-align: left; }"
                        + ".msg-bubble { display: inline-block; padding: 10px 14px; border-radius: 12px; max-width: 70%; word-wrap: break-word; }"
                        + ".self .msg-bubble { background: #d8f8c6; color: #17320f; border: 1px solid #b7e8a2; }"
                        + ".other .msg-bubble { background: #ffffff; border: 1px solid #dfe7f2; color: #1f2a36; }"
                        + ".msg-info { font-size: 11px; color: #7f8b99; margin-bottom: 3px; padding: 0 4px; }"
                        + ".msg-time { color: #9aa6b2; margin-left: 4px; }"
                        + ".system { text-align: center; margin: 9px 0; font-size: 12px; color: #8994a3; }"
                        + ".system .sys-icon { display: inline-block; margin-right: 4px; }"
                        + ".system.error { color: #e74c3c; }"
                        + ".system.warn { color: #f39c12; }"
                        + ".profile-card { text-align: left; margin: 10px auto; width: 360px; background: #fff7df; border: 1px solid #f0dca8; padding: 10px 12px; color: #3d3320; }"
                        + ".profile-title { font-weight: bold; color: #6b4f15; margin-bottom: 6px; }"
                        + ".profile-tip { color: #6d7f96; }"
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
            addHyperlinkListener(e -> {
                if (e.getEventType() != HyperlinkEvent.EventType.ACTIVATED) return;
                openLink(e);
            });
        }

        public void addText(String str) {
            String content = renderText(str);
            if (content != null) appendContent(content);
        }

        public String renderText(String str) {
            String content = str;
            if (content.contains("msg-info") && !content.contains("msg-time")) {
                content = content.replaceFirst("</div>\\s*<div class='msg-bubble'>",
                        " <span class='msg-time'>· " + currentTimeText()
                                + "</span></div><div class='msg-bubble'>");
            }

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
                    return null;
                }
                content = "<div class='system'><span class='sys-icon'>ℹ</span> " + escapeHtml(sysMsg) + "</div>";
            } else if (str.startsWith("@CHAT ")) {
                String chatContent = str.substring(6);
                content = "<div class='msg-wrapper'>" + chatContent + "</div>";
            } else if (str.startsWith("@PROFILE ")) {
                String profileContent = str.substring(9);
                content = "<div class='system' style='color:#3157a5;'>📋 " + profileContent.replace("|", "：") + "</div>";
            } else if (str.startsWith("@FRIEND_REQUEST ")) {
                String[] parts = str.substring(16).trim().split("\\|", 2);
                String uid = parts[0];
                String nick = parts.length == 2 ? parts[1] : parts[0];
                rememberUser(uid, nick);
                content = "<div class='system'>好友申请：" + escapeHtml(nick)
                        + " 请求添加你为好友。<a href='cmd:friend accept " + escapeHtml(uid) + "'>接受</a></div>";
            } else if (str.startsWith("@FRIEND_ACCEPTED ")) {
                String[] parts = str.substring(17).trim().split("\\|", 2);
                String uid = parts[0];
                String nick = parts.length == 2 ? parts[1] : parts[0];
                rememberUser(uid, nick);
                addFriendMark(uid);
                content = "<div class='system'>★ 你和 " + escapeHtml(nick) + " 已成为好友</div>";
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

            return content;
        }

        private void appendContent(String content) {
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

        public void setBody(String body) {
            setText("<html><head>" + CSS_STYLE + "</head><body>" + resolveAvatarTokens(body) + "</body></html>");
            setCaretPosition(getDocument().getLength());
        }

        public void clear() {
            setBody("");
        }

        private void openLink(HyperlinkEvent e) {
            try {
                String href = e.getDescription();
                if (href != null && href.startsWith("cmd:")) {
                    String command = href.substring(4);
                    if (command.startsWith("friend accept ")) {
                        acceptFriend(command.substring("friend accept ".length()));
                    } else if (ck != null) {
                        ck.sendCommand(command);
                    }
                    return;
                }
                if (href != null && href.startsWith("user:")) {
                    showUserCard(href.substring(5));
                    return;
                }
                if (href != null && href.startsWith("chat:")) {
                    openPrivateConversation(href.substring(5));
                    return;
                }
                URI uri = e.getURL() != null ? e.getURL().toURI() : new URI(href);
                if ("file".equalsIgnoreCase(uri.getScheme())) {
                    Desktop.getDesktop().open(new File(uri));
                } else {
                    Desktop.getDesktop().browse(uri);
                }
            } catch (Exception ex) {
                addMsg("<div class='system error'>无法打开链接: " + escapeHtml(ex.getMessage()) + "</div>");
            }
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
        boolean autoConnect = args.length >= 4;
        if (args.length >= 1) client.txtHost.setText(args[0]);
        if (args.length >= 2) client.txtPort.setText(args[1]);
        if (args.length >= 3) client.txtUserId.setText(args[2]);
        if (args.length >= 4) client.txtPassword.setText(args[3]);
        if (args.length >= 5) client.txtNick.setText(args[4]);
        client.setVisible(true);
        client.msgWindow.requestFocus();
        if (autoConnect) {
            SwingUtilities.invokeLater(client::connect);
        }
    }
}
