# AutoDL 部署说明

> 公开版本已将远程主机和端口改为占位符；部署时请按实际环境替换。

已配置的服务器环境：

```text
SSH: ssh -p <SSH_PORT> root@ssh.example.com
Java: OpenJDK 17
项目目录: /root/ch04
数据目录: /root/ch04/chat-data
内部聊天端口: <INTERNAL_CHAT_PORT>
客户端公网地址: chat.example.com:<PUBLIC_CHAT_PORT>
```

不要把 SSH 密码写进仓库、交接文档或实验报告。

## 上传代码

把本目录 `ch04` 上传到服务器 `/root/ch04`。

## 启动服务端

```bash
cd /root/ch04
chmod +x deploy/*.sh
./deploy/run-server.sh <INTERNAL_CHAT_PORT>
```

## 停止服务端

```bash
/root/ch04/deploy/stop-server.sh
```

## 查看日志

```bash
tail -f /root/ch04/logs/server.log
```

## 检查监听

```bash
ss -lntp | grep <INTERNAL_CHAT_PORT>
```

## 给客户端组员的连接信息

客户端填写：

```text
Host: chat.example.com
Port: <PUBLIC_CHAT_PORT>
```

`<SSH_PORT>` 是 SSH 登录端口，不是聊天服务端口。AutoDL/SeetaCloud 控制台里的 TCP 端口映射关系是：公网 `<PUBLIC_CHAT_PORT>` -> 实例内部 `<INTERNAL_CHAT_PORT>`。
