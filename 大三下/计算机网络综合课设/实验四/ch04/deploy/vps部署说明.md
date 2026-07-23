# VPS 部署说明

> 公开版本使用 RFC 5737 示例地址和端口占位符，不对应真实服务器。

本文档用于把聊天服务器部署到 VPS `203.0.113.10`。当前 VPS 的 SSH 端口是 `<SSH_PORT>`。聊天服务建议使用 `<CHAT_PORT>` 端口。

注意：VPS 上已有 hysteria2 服务。部署聊天服务器时不要重启系统网络服务，不要修改 hysteria2 配置，不要执行会清空防火墙规则的命令。

## 连接信息

```text
SSH Host: 203.0.113.10
SSH Port: <SSH_PORT>
Project Dir: /root/ch04
Chat Port: <CHAT_PORT>
Client Host: 203.0.113.10
Client Port: <CHAT_PORT>
```

不要把 SSH 密码提交到仓库、交接文档或报告中。

## 上传代码

在本地 PowerShell 中进入项目目录：

```powershell
cd D:\ch04
```

如果使用 scp：

```powershell
scp -P <SSH_PORT> -r . root@203.0.113.10:/root/ch04
```

也可以用 Xftp、WinSCP、FinalShell 等工具把整个 `D:\ch04` 上传到 `/root/ch04`。

## 启动服务

登录 VPS 后执行：

```bash
cd /root/ch04
chmod +x deploy/*.sh
./deploy/run-server.sh <CHAT_PORT>
```

脚本会自动：

- 编译 Java 源码到 `out`
- 创建 `logs` 和 `chat-data`
- 使用 `nohup` 后台启动服务
- 写入 PID 到 `logs/chat-server.pid`
- 写入日志到 `logs/server.log`

## 停止服务

```bash
cd /root/ch04
./deploy/stop-server.sh
```

停止脚本只会停止 `logs/chat-server.pid` 指向的聊天服务器进程，并会检查该进程命令行中是否包含 `com.cncd.ch04.server.MainServer`。

## 检查服务

查看监听端口：

```bash
ss -lntp | grep <CHAT_PORT>
```

查看日志：

```bash
tail -f /root/ch04/logs/server.log
```

检查 hysteria2 是否仍在运行：

```bash
systemctl status hysteria-server 2>/dev/null || systemctl status hysteria2 2>/dev/null || true
```

## 防火墙提示

如果客户端连不上 `203.0.113.10:<CHAT_PORT>`，先检查 VPS 是否有防火墙。

仅在确认不会影响 hysteria2 的情况下，允许 `<CHAT_PORT>/tcp`：

```bash
ufw allow <CHAT_PORT>/tcp
```

不要执行 `ufw reset`、`iptables -F`、重启网络等命令。

## 客户端连接

客户端填写：

```text
Host: 203.0.113.10
Port: <CHAT_PORT>
```

或者直接用命令行启动：

```powershell
java -cp out com.cncd.ch04.client.ChatClient 203.0.113.10 <CHAT_PORT> Alice
```

## 验收标准

- `ssh root@203.0.113.10 -p <SSH_PORT>` 可以登录。
- `ss -lntp | grep <CHAT_PORT>` 能看到 Java 进程监听。
- 本地客户端能连接 `203.0.113.10:<CHAT_PORT>`。
- 两个客户端能互相看到在线用户。
- 群聊、私聊、中文消息能正常收发。
- hysteria2 服务不被停止、不被改配置。
