# VPS 运行说明

> 公开版本使用 RFC 5737 示例地址和端口占位符，不对应真实服务器。

本项目当前目标服务器为 VPS：

```text
VPS Host: 203.0.113.10
SSH Port: <SSH_PORT>
Chat Port: <CHAT_PORT>
Project Dir: /root/ch04
```

SSH 端口 `<SSH_PORT>` 只用于登录服务器；聊天客户端连接端口是 `<CHAT_PORT>`。

## 本地编译

在 Windows PowerShell 中执行：

```powershell
cd D:\ch04
javac -encoding UTF-8 -d out (Get-ChildItem -Recurse -Filter *.java | ForEach-Object { $_.FullName })
```

## 本地启动服务器测试

```powershell
cd D:\ch04
java -cp out com.cncd.ch04.server.MainServer <CHAT_PORT>
```

## 本地启动客户端

```powershell
cd D:\ch04
java -cp out com.cncd.ch04.client.ChatClient
```

客户端默认连接：

```text
Host: 203.0.113.10
Port: <CHAT_PORT>
```

也可以显式指定：

```powershell
java -cp out com.cncd.ch04.client.ChatClient 203.0.113.10 <CHAT_PORT> Alice
```

## 上传到 VPS

把整个项目上传到 VPS：

```powershell
scp -P <SSH_PORT> -r D:\ch04 root@203.0.113.10:/root/ch04
```

如果使用 WinSCP、Xftp、FinalShell，也可以把 `D:\ch04` 上传为 `/root/ch04`。

## VPS 启动服务

登录 VPS 后执行：

```bash
cd /root/ch04
chmod +x deploy/*.sh
./deploy/run-server.sh <CHAT_PORT>
```

## VPS 停止服务

```bash
cd /root/ch04
./deploy/stop-server.sh
```

## 检查服务

```bash
ss -lntp | grep <CHAT_PORT>
tail -f /root/ch04/logs/server.log
```

## 不影响 hysteria2 的注意事项

- 不要执行 `ufw reset`。
- 不要执行 `iptables -F`。
- 不要重启系统网络服务。
- 不要修改 hysteria2 配置文件。
- 本项目脚本只启动或停止 `com.cncd.ch04.server.MainServer` 对应的 Java 进程。

如果客户端无法连接，再单独开放聊天端口：

```bash
ufw allow <CHAT_PORT>/tcp
```

执行前先确认 hysteria2 当前使用的端口和防火墙规则。
