# 聊天软件团队开发 Handoff

本文档用于 5 人团队在当前代码基础上继续并行开发。当前项目是 Java Socket + Swing 架构，已经具备服务器、客户端、在线用户、私聊、好友、资料、中文、文件和图片传输的基础能力。后续目标是把它完善成一个可部署到 AutoDL 公共服务器、客户端界面成熟美观、功能稳定的聊天软件。

## 当前项目结构

```text
D:\ch04
├─ client
│  ├─ ChatClient.java          客户端 Swing 界面
│  └─ ClientKernel.java        客户端网络通信与消息解析
├─ server
│  ├─ MainServer.java          服务器入口，监听端口并接收连接
│  ├─ ConnectedClient.java     单个客户端连接的收发线程
│  ├─ ConnectionKeeper.java    在线连接池、用户列表、消息转发
│  ├─ BroadcastCommandParser.java  服务端命令解析
│  ├─ DataSource.java          数据源接口
│  ├─ FileDataSource.java      文件数据存储
│  └─ CommandParser.java       命令解析接口
├─ chat-data                   运行后生成，保存用户资料等数据
├─ out                         编译输出目录
├─ README_运行说明.md
└─ HANDOFF_团队开发交接.md
```

## 当前运行方式

编译：

```powershell
cd /d D:\ch04
javac -encoding UTF-8 -d out (Get-ChildItem -Recurse -Filter *.java | ForEach-Object { $_.FullName })
```

启动服务器：

```powershell
java -cp out com.cncd.ch04.server.MainServer 3500
```

启动客户端：

```powershell
java -cp out com.cncd.ch04.client.ChatClient
```

如果不在 `D:\ch04` 目录运行，需要使用绝对 classpath：

```powershell
java -cp D:\ch04\out com.cncd.ch04.server.MainServer 3500
java -cp D:\ch04\out com.cncd.ch04.client.ChatClient
```

AutoDL 远程联调使用：

```text
客户端 Host: chat.example.com
客户端 Port: <PUBLIC_CHAT_PORT>
服务器内部监听端口: <INTERNAL_CHAT_PORT>
AutoDL TCP 映射: 公网 <PUBLIC_CHAT_PORT> -> 内部 <INTERNAL_CHAT_PORT>
```

`ssh -p <SSH_PORT> root@ssh.example.com` 只用于登录服务器运维，不是聊天客户端连接地址。

## 当前通信协议

当前客户端和服务器使用 Socket 长连接通信，消息以字节 `0xff` 作为结束符，消息正文使用 UTF-8 编码。

服务器推送消息格式：

```text
@SYSTEM 系统提示文本
@USERS Alice,Bob,Carol
@CHAT 发送者|接收者或全部|聊天内容
@PROFILE 用户名|字段1=值1；字段2=值2
@FILE 发送者|文件名|Base64内容
@IMAGE 发送者|文件名|Base64内容
```

客户端发送命令格式：

```text
/nick Alice
/users
/msg Bob 你好
/friend add Bob
/profile set city=北京
/profile view Alice
/file Bob 文件名|Base64内容
/image Bob 图片名|Base64内容
/stats
/exit
```

普通文本不以 `/` 开头时，按群聊消息发送。

## 当前已实现能力

- 多客户端连接服务器。
- 在线用户列表推送。
- 群聊广播。
- 两个用户之间私聊。
- 添加好友。
- 好友在线提醒。
- 个人资料保存和查询。
- UTF-8 中文通信。
- 文件附件发送和接收。
- 图片附件发送、接收和预览。
- 客户端基础 Swing 界面。

## 当前需要继续完善的问题

这些是后续开发优先级较高的点：

1. 客户端界面还比较基础，需要显著美化。
2. 好友关系目前主要在内存中，建议持久化到 `chat-data`。
3. 文件和图片使用 Base64 放在单条消息里，适合小文件，后续应限制大小或改为分片传输。
4. 没有正式登录系统，当前以昵称为主。
5. 断线重连、连接失败提示还需要增强。
6. AutoDL 公网部署已有基础脚本和说明，后续重点是确认实例重启后服务是否仍在运行。
7. 当前协议简单，字段中如果包含 `|` 可能影响解析，后续应统一转义或改为 JSON。

## 5 人并行分工

### 1 号：AutoDL 公共服务器与部署负责人

适合负责服务器、网络、部署方向的同学。

负责范围：

- 在 AutoDL 创建实例。
- 安装或确认 JDK。
- 上传项目代码。
- 编译服务器代码。
- 启动聊天服务器。
- 当前 AutoDL 映射为公网 `<PUBLIC_CHAT_PORT>` -> 内部 `<INTERNAL_CHAT_PORT>`，客户端填公网 Host 和公网 Port。
- 确认本地客户端可以连接 AutoDL 公网 Host/Port。
- 编写服务端启动脚本。
- 处理端口占用、防火墙、安全组、服务器断开等问题。

主要关注文件：

```text
server/MainServer.java
server/ConnectionKeeper.java
README_运行说明.md
deploy/autodl部署说明.md
```

建议新增文件：

```text
deploy
├─ run-server.sh
├─ stop-server.sh
└─ autodl部署说明.md
```

交付标准：

- 给出公网服务器 Host 和 Port：`chat.example.com:<PUBLIC_CHAT_PORT>`。
- 其他组员的客户端能远程连接。
- 服务器重启后能重新运行。
- 服务端数据保存在明确目录中。

### 2 号：服务端业务与协议负责人

负责服务端聊天功能和协议稳定性。

负责范围：

- 在线用户列表维护。
- 用户上线、下线通知。
- 群聊广播。
- 私聊转发。
- 好友添加逻辑。
- 好友上线提醒逻辑。
- 昵称重复校验。
- 命令解析健壮性。
- 通信协议扩展和兼容。

主要关注文件：

```text
server/ConnectedClient.java
server/ConnectionKeeper.java
server/BroadcastCommandParser.java
server/CommandParser.java
```

建议优先任务：

- 修正字段分隔符风险，例如禁止昵称包含 `|`、`,`。
- 增加 `/help` 命令。
- 增加用户下线广播。
- 增加私聊失败时的清晰提示。
- 对空消息、超长消息做限制。

交付标准：

- 3 个以上客户端同时在线时，在线列表正确。
- 群聊和私聊不会串消息。
- 用户下线后列表能更新。
- 服务端不会因为非法命令崩溃。

### 3 号：客户端界面与视觉体验负责人

负责把客户端做成更成熟、更美观的聊天软件。

负责范围：

- 优化 `ChatClient.java` 的 Swing 布局。
- 做出接近 QQ/微信的聊天窗口。
- 左侧或右侧联系人列表。
- 中间聊天记录区。
- 底部输入区。
- 区分群聊和私聊。
- 区分自己消息和他人消息。
- 系统消息弱化显示。
- 文件消息用附件卡片显示。
- 图片消息显示缩略图。
- 顶部显示当前连接状态、服务器地址、当前昵称。

主要关注文件：

```text
client/ChatClient.java
```

建议优先任务：

- 把聊天记录从简单 HTML 文本优化为更清晰的消息样式。
- 增加“当前聊天对象”显示。
- 增加连接状态颜色，例如未连接、已连接、连接失败。
- 调整窗口默认大小，例如 `900 x 650`。
- 使用统一字体、间距、颜色。

交付标准：

- 客户端第一眼看起来像完整聊天软件。
- 用户能直观看到在线用户、聊天对象和消息类型。
- 窗口缩放时布局不乱。
- 中文、图片、文件显示不挤压。

### 4 号：客户端通信、多媒体与稳定性负责人

负责客户端网络通信、附件传输和异常处理。

负责范围：

- 维护 `ClientKernel.java`。
- 连接 AutoDL 公网服务器。
- 发送普通消息。
- 发送命令。
- 解析服务器推送。
- 接收在线用户列表。
- 接收聊天消息。
- 接收个人资料。
- 接收文件和图片。
- 保存附件到本地目录。
- 网络断开提示。
- 避免网络线程影响界面卡顿。

主要关注文件：

```text
client/ClientKernel.java
client/ChatClient.java
```

建议优先任务：

- 增加连接失败回调，让界面显示失败原因。
- 限制单个文件大小，例如先限制 2MB。
- 支持中文文件名。
- 附件保存目录可配置。
- 收到附件时提示保存路径。
- 避免服务器断开后无限报错。

交付标准：

- 连接公网服务器稳定。
- 中文消息稳定。
- 图片能预览。
- 文件能保存。
- 网络断开时客户端不崩溃。

### 5 号：数据持久化、好友资料与集成测试负责人

负责数据保存和整体功能验证。报告暂时不用管，但测试记录要保留，后面可以直接转成报告材料。

负责范围：

- 用户资料持久化。
- 好友关系持久化。
- 数据文件格式整理。
- 多人联调测试。
- 功能验收清单。
- 记录 bug 和修复状态。

主要关注文件：

```text
server/DataSource.java
server/FileDataSource.java
server/BroadcastCommandParser.java
README_运行说明.md
```

建议优先任务：

- 在 `DataSource` 中增加好友相关接口。
- 在 `FileDataSource` 中保存好友关系。
- 数据目录统一使用项目目录 `chat-data`。
- 支持重启服务器后资料仍可查询。
- 支持重启服务器后好友关系仍存在。

建议新增数据文件：

```text
chat-data
├─ users
├─ info
└─ friends
```

交付标准：

- 资料保存后重启服务器仍能查询。
- 好友添加后重启服务器仍能保留。
- 多人测试流程有记录。
- 每个功能有至少一条测试结果。

## 并行开发建议

为了减少冲突，建议按文件边界并行：

```text
1 号主要改 deploy/、README_运行说明.md、服务器启动相关
2 号主要改 server/ConnectedClient.java、ConnectionKeeper.java、BroadcastCommandParser.java
3 号主要改 client/ChatClient.java
4 号主要改 client/ClientKernel.java，必要时少量配合 ChatClient.java
5 号主要改 server/DataSource.java、FileDataSource.java、数据文件格式
```

容易冲突的文件：

```text
client/ChatClient.java
server/BroadcastCommandParser.java
```

处理方式：

- 3 号主改 `ChatClient.java`，4 号需要 UI 回调时先约定方法名。
- 2 号主改 `BroadcastCommandParser.java`，5 号需要数据接口时先改 `DataSource.java`，再让 2 号接入命令。
- 每次合并前都执行一次完整编译。

## 推荐开发顺序

第一阶段：稳定远程连接

```text
1 号搭 AutoDL
2 号稳定服务器多连接
4 号确认客户端能连公网 IP
```

第二阶段：完善核心聊天

```text
2 号完善群聊、私聊、上下线、好友提醒
3 号优化聊天界面
4 号完善消息解析和异常处理
```

第三阶段：完善资料、好友和附件

```text
5 号做资料和好友持久化
4 号做文件和图片稳定传输
3 号做图片和文件消息展示
```

第四阶段：集成联调

```text
所有人使用 AutoDL 公网服务器同时测试
至少 3 台电脑、3 个账号同时在线
测试群聊、私聊、好友提醒、资料、图片、文件
```

## 每次提交前检查

每个人改完后至少执行：

```powershell
cd /d D:\ch04
javac -encoding UTF-8 -d out (Get-ChildItem -Recurse -Filter *.java | ForEach-Object { $_.FullName })
```

如果负责客户端，还要至少手动启动一次：

```powershell
java -cp out com.cncd.ch04.client.ChatClient
```

如果负责服务端，还要至少手动启动一次：

```powershell
java -cp out com.cncd.ch04.server.MainServer 3500
```

AutoDL 服务端使用内部端口 `<INTERNAL_CHAT_PORT>`：

```bash
cd /root/ch04
./deploy/run-server.sh <INTERNAL_CHAT_PORT>
ss -lntp | grep <INTERNAL_CHAT_PORT>
```

## 集成验收清单

最终软件至少应通过这些检查：

- 服务器能在 AutoDL 上启动。
- 本地客户端能通过公网 Host/Port 连接。
- 两个客户端能看到彼此在线。
- 群聊消息所有在线用户都能收到。
- 选中用户后能私聊。
- 添加好友后有在线提醒。
- 用户资料能保存和查询。
- 中文消息不会乱码。
- 图片能发送并预览。
- 文件能发送并保存。
- 客户端界面清晰美观。
- 异常命令不会导致服务器崩溃。
- 客户端断开后在线列表更新。

## 当前代码继续开发注意事项

- 消息内容使用 UTF-8，不要再改回 `writeBytes` 方式。
- 当前结束符是 `0xff`，发送和接收两端必须保持一致。
- 附件现在使用 Base64，文件过大时会影响性能。
- 昵称、文件名、资料字段中尽量避免 `|` 和 `,`，后续可以做转义或 JSON 化。
- Swing 界面更新应尽量通过 `SwingUtilities.invokeLater`。
- 服务端对共享在线用户列表的操作要注意同步。
- AutoDL 部署时客户端连接的是公网 Host 和公网 Port：`chat.example.com:<PUBLIC_CHAT_PORT>`，不是 `127.0.0.1`，也不是 SSH 端口 `<SSH_PORT>`。
