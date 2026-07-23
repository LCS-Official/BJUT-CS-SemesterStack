# 实验四 简单聊天程序运行说明

> 公开版本已将远程主机和端口改为占位符；部署时请按实际环境替换。

## 已扩充功能

- 客户端右侧显示当前所有在线用户。
- 支持群聊和两个用户之间的私聊。
- 支持添加好友，好友在线时给出提醒。
- 支持个人资料保存和查询，数据保存在项目目录 `chat-data` 下。
- 通信内容使用 UTF-8，支持中文聊天。
- 支持发送图片，接收后在聊天窗口中预览。
- 支持发送普通文件附件，接收后保存到用户目录 `.mihalychat/downloads`。

## 编译

先进入项目目录：

```powershell
cd /d D:\ch04
```

然后执行编译：

```powershell
javac -encoding UTF-8 -d out (Get-ChildItem -Recurse -Filter *.java | ForEach-Object { $_.FullName })
```

## 启动服务器

```powershell
cd D:\ch04
java -cp out com.cncd.ch04.server.MainServer 3500
```

## 启动客户端

另开一个 PowerShell 窗口执行：

```powershell
cd /d D:\ch04
java -cp out com.cncd.ch04.client.ChatClient
```

要测试两人聊天，再开第三个 PowerShell 窗口重复启动一次客户端。

如果不想切换目录，也可以使用绝对路径：

```powershell
java -cp D:\ch04\out com.cncd.ch04.server.MainServer 3500
java -cp D:\ch04\out com.cncd.ch04.client.ChatClient
```

客户端默认连接 AutoDL 公网聊天服务：

```text
Host: chat.example.com
Port: <PUBLIC_CHAT_PORT>
```

如果是本机测试，请手动把客户端里的 Host 改成 `127.0.0.1`，Port 改成你本机服务器启动时使用的端口，例如 `3500`。

## 客户端使用

1. 填写服务器地址、端口、昵称，点击 `Connect`。远程联调用默认的 AutoDL 地址，本机测试用 `127.0.0.1:3500`。
2. 右侧会显示在线用户列表。
3. 不勾选 `私聊选中用户` 时，消息发送给所有在线用户。
4. 选中右侧用户并勾选 `私聊选中用户` 后，消息只发送给该用户。
5. 选中用户后点击 `加好友`，好友在线时会收到系统提醒。
6. 在个人资料栏输入字段和值，例如 `city` 和 `北京`，点击 `保存资料`。
7. 点击 `查看资料` 可查看自己或选中用户的资料。
8. 选中用户后点击 `文件` 或 `图片` 可发送附件。

## 常用命令

聊天输入框也支持命令：

```text
/nick Alice
/users
/msg Bob 你好
/friend add Bob
/profile set city=北京
/profile view Alice
/stats
/exit
```
