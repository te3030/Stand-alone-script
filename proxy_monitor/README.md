# 多代理健康监控与统计系统

由 DeepSeek 协助开发，用于持续监控多个代理服务器的健康状况，并通过钉钉机器人实时推送告警与统计报告。

## 功能特性

- **多代理并行监控**：每个代理独立检测连通性、IP 出口、下载速度
- **灵活开关**：可单独控制代理的“监测”与“下载”任务
- **自适应下载间隔**：下载连续失败时自动缩短重试间隔（最低可配置）
- **失败/恢复告警**：达到连续失败阈值时立即告警，恢复后发送恢复通知
- **定时统计报告**：汇总下载成功率、平均速度、连通率、延迟等，定期推送至钉钉
- **IP 多来源检测**：支持配置多个 IP 查询 API，按顺序尝试，各自定义 JSON 解析路径
- **SQLite 数据持久化**：保留 60 天历史数据，自动清理
- **一键部署**：支持 `install` 命令安装为 systemd 服务，开机自启
- **启动信息可配置**：服务启动时发送自定义内容的钉钉消息

## 系统要求

- Python 3.6+
- 操作系统：Linux（推荐 Debian/Ubuntu）
- 依赖库：`requests`, `pyyaml`, `sqlite3`（内置）
- 若使用 SOCKS5 代理，需额外安装 `PySocks`（Debian/Ubuntu 可使用 `python3-socks` 包）

## 安装

### 1. 克隆项目或直接下载脚本

```bash
git clone https://github.com/te3030/Stand-alone-script.git
cd Stand-alone-script/proxy_monitor
```

或者直接下载 `proxy_monitor.py` 和 `config.yaml` 到同一目录。

### 2. 安装 Python 依赖

```bash
# 系统包管理器（Debian/Ubuntu）
sudo apt update
sudo apt install python3-requests python3-yaml python3-socks

# 使用 pip（推荐使用虚拟环境）
pip install requests pyyaml PySocks
```

### 3. 配置钉钉机器人

在钉钉群中添加一个自定义机器人（安全设置选择“加签”或“关键词”），获取 Webhook 地址，并填入 `config.yaml` 的 `webhook.dingtalk` 字段。

### 4. 修改配置文件

根据实际情况编辑 `config.yaml`，至少需要：
- 填写代理地址（`proxy.url`）
- 填写钉钉 Webhook 地址
- （可选）调整下载链接、告警阈值等

### 5. 运行监控（前台）

```bash
python3 proxy_monitor.py config.yaml
```

### 6. 安装为系统服务（推荐）

```bash
sudo python3 proxy_monitor.py install config.yaml
```

该命令会：
- 将脚本和配置文件复制到 `/usr/local/etc/proxy_monitor/`
- 创建并启用 `proxy_monitor.service`，设置开机自启
- 立即启动服务


## 配置说明

配置文件采用 YAML 格式，所有字段均带有注释。完整注释版 `config.example.yaml`。

## 命令行参考

```bash
# 显示帮助
python3 proxy_monitor.py --help

# 前台运行（调试用）
python3 proxy_monitor.py config.yaml

# 安装服务
sudo python3 proxy_monitor.py install config.yaml
```

## 日志与数据库

- 运行日志：`monitor.log`（与服务脚本同目录）
- 数据库文件：默认 `monitor.db`，可通过配置文件自定义路径
- 数据库包含三张表：`download_logs`、`connectivity_logs`、`ip_logs`，可使用 SQLite 工具直接查询

## 常见问题

### 1. SOCKS 代理报错 “Missing dependencies for SOCKS support”

这是因为缺少 PySocks 库。按前面的安装步骤安装 `python3-socks` 或 `PySocks` 即可。

### 2. 直连 IP 显示 “获取失败” 或 “unknown”

检查 `ip_check.urls` 中的 API 是否可从本机直接访问。若服务器仅通过代理上网，直连 IP 获取失败是正常的，可在启动消息中屏蔽该项。

### 3. 如何只监控不下载？

在代理配置中设置 `download_enabled: false` 即可。

### 4. 如何完全关闭某个代理的监控？

同时设置 `monitor_enabled: false` 和 `download_enabled: false`，该代理将被跳过，不启动任何线程，也不出现在启动消息中。

### 5. 钉钉消息发送失败

- 确认 Webhook 地址正确
- 检查机器人安全设置（关键词或加签），建议使用“关键词”匹配，关键词可填写“监控”
- 服务器需要能访问外网（oapi.dingtalk.com）

### 6. 修改配置后如何生效？

若以前台方式运行，直接 `Ctrl+C` 停止后重新启动即可。若是系统服务，执行：
```bash
sudo systemctl restart proxy_monitor.service
```

### 7. 如何卸载服务？

```bash
sudo systemctl stop proxy_monitor.service
sudo systemctl disable proxy_monitor.service
sudo rm /etc/systemd/system/proxy_monitor.service
sudo rm -r /usr/local/etc/proxy_monitor
sudo systemctl daemon-reload
```

## 项目结构

```
.
├── proxy_monitor.py          # 主程序
├── config.yaml               # 配置文件
├── monitor.log               # 运行日志（自动生成）
├── monitor.db                # 数据库文件（自动生成）
└── README.md                 # 本文件
```
