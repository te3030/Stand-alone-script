#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 本脚本由 DeepSeek 协助开发

"""
多代理健康监控与统计系统 v5.3
用法:
  python3 proxy_monitor.py <配置文件路径>   # 启动监控
  python3 proxy_monitor.py install [配置文件]  # 安装为系统服务（需要 root）
  python3 proxy_monitor.py --help          # 显示帮助
"""

import os, sys, time, json, socket, threading, logging, shutil, subprocess
from datetime import datetime, timedelta

import requests, yaml, sqlite3

# --------------------- 日志 ---------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("monitor.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --------------------- 常量定义 ---------------------
INSTALL_DIR = "/usr/local/etc/proxy_monitor"
SERVICE_NAME = "proxy_monitor.service"
SERVICE_PATH = f"/etc/systemd/system/{SERVICE_NAME}"

# --------------------- 帮助信息 ---------------------
def print_help():
    print("""
多代理健康监控与统计系统 (由 DeepSeek 协助开发)

用法:
  python3 proxy_monitor.py <配置文件路径>
      使用指定的配置文件启动监控（前台运行）

  python3 proxy_monitor.py install [配置文件]
      将脚本和配置文件安装到 {install_dir}，并注册为 systemd 服务，设置开机自启并立即启动。
      如果未指定配置文件，则尝试复制当前目录下的 config.yaml。

  python3 proxy_monitor.py --help
      显示本帮助信息。

配置文件示例: 见 config.yaml
""".format(install_dir=INSTALL_DIR))

# --------------------- 安装函数 ---------------------
def install_service(config_file=None):
    if os.geteuid() != 0:
        logger.error("安装服务需要 root 权限，请使用 sudo 运行")
        sys.exit(1)

    os.makedirs(INSTALL_DIR, exist_ok=True)

    script_path = os.path.abspath(__file__)
    target_script = os.path.join(INSTALL_DIR, "proxy_monitor.py")
    try:
        shutil.copy2(script_path, target_script)
        os.chmod(target_script, 0o755)
        logger.info(f"已复制脚本到 {target_script}")
    except Exception as e:
        logger.error(f"复制脚本失败: {e}")
        sys.exit(1)

    if config_file:
        if not os.path.exists(config_file):
            logger.error(f"指定的配置文件不存在: {config_file}")
            sys.exit(1)
        source_config = config_file
    else:
        source_config = "config.yaml"
        if not os.path.exists(source_config):
            logger.error("当前目录下没有 config.yaml，且未指定配置文件路径")
            sys.exit(1)
    target_config = os.path.join(INSTALL_DIR, "config.yaml")
    try:
        shutil.copy2(source_config, target_config)
        logger.info(f"已复制配置文件到 {target_config}")
    except Exception as e:
        logger.error(f"复制配置文件失败: {e}")
        sys.exit(1)

    service_content = f"""[Unit]
Description=Proxy Monitor Service (by DeepSeek)
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {target_script} {target_config}
WorkingDirectory={INSTALL_DIR}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    try:
        with open(SERVICE_PATH, 'w') as f:
            f.write(service_content)
        logger.info(f"已写入服务文件 {SERVICE_PATH}")
    except Exception as e:
        logger.error(f"写入服务文件失败: {e}")
        sys.exit(1)

    try:
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", SERVICE_NAME], check=True)
        subprocess.run(["systemctl", "start", SERVICE_NAME], check=True)
        logger.info(f"服务 {SERVICE_NAME} 已安装并启动")
        print(f"安装完成！服务已启动。管理命令：")
        print(f"  sudo systemctl status {SERVICE_NAME}")
        print(f"  sudo systemctl stop {SERVICE_NAME}")
        print(f"  sudo systemctl start {SERVICE_NAME}")
        print(f"  sudo systemctl disable {SERVICE_NAME}")
    except subprocess.CalledProcessError as e:
        logger.error(f"systemd 操作失败: {e}")
        sys.exit(1)

# --------------------- 配置加载 ---------------------
def load_config(path="config.yaml"):
    if not os.path.exists(path):
        sys.exit(f"配置文件不存在: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# --------------------- 依赖检查 ---------------------
def check_socks_support():
    try:
        import socks
        return True
    except ImportError:
        return False

# --------------------- 数据库 ---------------------
class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS download_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    proxy TEXT,
                    url TEXT,
                    success INTEGER,
                    speed REAL,
                    file_size INTEGER,
                    duration REAL,
                    error_message TEXT
                );
                CREATE TABLE IF NOT EXISTS connectivity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    proxy TEXT,
                    host TEXT,
                    port INTEGER,
                    success INTEGER,
                    latency_ms REAL,
                    error_message TEXT
                );
                CREATE TABLE IF NOT EXISTS ip_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    use_proxy INTEGER,
                    proxy TEXT,
                    api_url TEXT,
                    ip_address TEXT,
                    city TEXT,
                    raw_json TEXT,
                    error_message TEXT
                );
            """)

    def save_download(self, proxy, url, success, speed, size, dur, err=""):
        with self._conn() as conn:
            conn.execute("""INSERT INTO download_logs
                (proxy, url, success, speed, file_size, duration, error_message)
                VALUES (?,?,?,?,?,?,?)""",
                (proxy, url, int(success), speed, size, dur, err))

    def save_connectivity(self, proxy, host, port, success, lat, err=""):
        with self._conn() as conn:
            conn.execute("""INSERT INTO connectivity_logs
                (proxy, host, port, success, latency_ms, error_message)
                VALUES (?,?,?,?,?,?)""",
                (proxy, host, port, int(success), lat, err))

    def save_ip(self, use_proxy, proxy, api_url, ip, city, raw, err=""):
        with self._conn() as conn:
            conn.execute("""INSERT INTO ip_logs
                (use_proxy, proxy, api_url, ip_address, city, raw_json, error_message)
                VALUES (?,?,?,?,?,?,?)""",
                (int(use_proxy), proxy, api_url, ip, city, raw, err))

    def clean_old(self, days):
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        with self._conn() as conn:
            for t in ("download_logs", "connectivity_logs", "ip_logs"):
                conn.execute(f"DELETE FROM {t} WHERE timestamp < ?", (cutoff,))

    def stats(self, hours):
        period = f"-{hours} hours"
        with self._conn() as conn:
            cur = conn.execute("SELECT COUNT(*), SUM(success), AVG(speed) FROM download_logs WHERE timestamp > datetime('now',?)", (period,))
            d_total, d_ok, d_avg = cur.fetchone()
            cur = conn.execute("SELECT COUNT(*), SUM(success), AVG(latency_ms) FROM connectivity_logs WHERE timestamp > datetime('now',?)", (period,))
            c_total, c_ok, c_avg = cur.fetchone()
            cur = conn.execute("SELECT proxy, ip_address FROM ip_logs WHERE use_proxy=1 AND timestamp > datetime('now',?) ORDER BY timestamp DESC", (period,))
            proxy_ips = {}
            for row in cur.fetchall():
                if row[0] not in proxy_ips:
                    proxy_ips[row[0]] = row[1]
            cur = conn.execute("SELECT ip_address FROM ip_logs WHERE use_proxy=0 ORDER BY timestamp DESC LIMIT 1")
            direct_ip = cur.fetchone()
        return {
            'download_total': d_total or 0,
            'download_success': d_ok or 0,
            'download_fail': (d_total or 0) - (d_ok or 0),
            'download_avg_speed': d_avg or 0,
            'conn_total': c_total or 0,
            'conn_success': c_ok or 0,
            'conn_fail': (c_total or 0) - (c_ok or 0),
            'conn_avg_latency': c_avg or 0,
            'proxy_ips': proxy_ips,
            'direct_ip': direct_ip[0] if direct_ip else "N/A"
        }

# --------------------- 工具函数 ---------------------
def parse_proxy(proxy_url):
    info = {"url": proxy_url, "host": None, "port": None}
    if "://" in proxy_url:
        scheme, rest = proxy_url.split("://", 1)
        info["scheme"] = scheme
    else:
        rest = proxy_url
    if "@" in rest:
        auth, host_port = rest.rsplit("@", 1)
        info["auth"] = auth
    else:
        host_port = rest
    if ":" in host_port:
        host, port = host_port.rsplit(":", 1)
        info["host"] = host
        info["port"] = int(port)
    else:
        info["host"] = host_port
    return info

def json_value(data, path):
    if not path:
        return None
    try:
        for key in path.split('.'):
            data = data[key]
        return str(data) if data is not None else None
    except (KeyError, TypeError):
        return None

def is_proxy_error(ex):
    return isinstance(ex, requests.exceptions.ProxyError)

def check_tcp(host, port, timeout):
    start = time.time()
    sock = None
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        lat = (time.time() - start) * 1000
        return True, lat, None
    except Exception as e:
        lat = (time.time() - start) * 1000
        return False, lat, str(e)
    finally:
        if sock:
            sock.close()

def send_dingtalk(webhook, title, text):
    if not webhook:
        return
    try:
        resp = requests.post(webhook, json={
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text}
        }, timeout=10)
        if resp.status_code == 200:
            logger.info(f"钉钉消息发送成功: {title}")
        else:
            logger.error(f"钉钉发送失败 {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"钉钉请求异常: {e}")

def download_with_proxy(url, proxy_url, timeout):
    proxies = {"http": proxy_url, "https": proxy_url}
    start = time.time()
    try:
        resp = requests.get(url, proxies=proxies, stream=True, timeout=timeout)
        resp.raise_for_status()
        size = 0
        for chunk in resp.iter_content(8192):
            if chunk:
                size += len(chunk)
        dur = time.time() - start
        return {"success": True, "speed": size/dur if dur>0 else 0, "file_size": size, "duration": dur, "error": None}
    except Exception as e:
        dur = time.time() - start
        return {"success": False, "speed": 0, "file_size": 0, "duration": dur, "error": str(e), "exception": e}

def get_proxy_outbound_ip(proxy_url, ip_urls, timeout):
    for item in ip_urls:
        url = item.get("url")
        ip_path = item.get("ip_json_path", "ip")
        city_path = item.get("city_json_path", "")
        try:
            proxies = {"http": proxy_url, "https": proxy_url}
            resp = requests.get(url, proxies=proxies, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            ip = json_value(data, ip_path)
            city = json_value(data, city_path) if city_path else ""
            if ip:
                return ip, city
        except:
            continue
    return "获取失败", ""

# --------------------- 单代理监控器 ---------------------
class ProxyWatcher:
    def __init__(self, proxy_cfg, global_config, db, socks_available, webhook, title_prefix):
        self.proxy_url = proxy_cfg["url"]
        self.proxy_label = proxy_cfg.get("label", self.proxy_url)
        self.db = db
        self.socks_available = socks_available
        self.webhook = webhook
        self.title_prefix = title_prefix
        self.stop_event = threading.Event()

        self.monitor_enabled = proxy_cfg.get("monitor_enabled", True)
        self.download_enabled = proxy_cfg.get("download_enabled", True)

        conn_cfg = proxy_cfg.get("connectivity", global_config.get("connectivity_check", {}))
        p_info = parse_proxy(self.proxy_url)
        self.conn_host = conn_cfg.get("host") or p_info.get("host")
        self.conn_port = conn_cfg.get("port") or p_info.get("port")
        self.conn_timeout = conn_cfg.get("timeout", 5)
        self.conn_interval = conn_cfg.get("interval", 60)

        dl_cfg = global_config.get("download", {})
        self.download_urls = dl_cfg.get("urls", [])
        self.download_timeout = dl_cfg.get("timeout", 600)
        self.base_interval = dl_cfg.get("interval", 300)
        self.min_interval = dl_cfg.get("fail_interval_min", 10)
        self.current_interval = self.base_interval

        ip_cfg = global_config.get("ip_check", {})
        self.ip_urls = ip_cfg.get("urls", [])
        self.ip_timeout = ip_cfg.get("timeout", 10)
        self.ip_interval = ip_cfg.get("interval", 600)

        alerts_cfg = global_config.get("alerts", {})
        self.down_fail_threshold = alerts_cfg.get("download_fail_threshold", 3)
        self.down_success_threshold = alerts_cfg.get("download_success_threshold", 2)
        self.conn_fail_threshold = alerts_cfg.get("connectivity_fail_threshold", 5)
        self.conn_success_threshold = alerts_cfg.get("connectivity_success_threshold", 2)

        self._lock = threading.Lock()
        self._down_anomaly = False
        self._down_fail_count = 0
        self._down_success_count = 0
        self._conn_anomaly = False
        self._conn_fail_count = 0
        self._conn_success_count = 0

    def _alert(self, title, message):
        full_title = f"[{self.title_prefix}][{self.proxy_label}] {title}"
        send_dingtalk(self.webhook, full_title,
                      f"**{full_title}**\n\n{message}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def _report_download_success(self):
        with self._lock:
            if self._down_anomaly:
                self._down_success_count += 1
                if self._down_success_count >= self._down_success_threshold:
                    self._alert("✅ 下载已恢复", f"连续成功 {self._down_success_count} 次")
                    self._down_anomaly = False
                    self._down_success_count = 0
            else:
                self._down_fail_count = 0

    def _report_download_fail(self):
        with self._lock:
            if self._down_anomaly:
                self._down_success_count = 0
            else:
                self._down_fail_count += 1
                if self._down_fail_count >= self._down_fail_threshold:
                    self._alert("⚠️ 下载连续失败告警", f"连续失败 {self._down_fail_count} 次")
                    self._down_anomaly = True
                    self._down_success_count = 0

    def _report_conn_success(self):
        with self._lock:
            if self._conn_anomaly:
                self._conn_success_count += 1
                if self._conn_success_count >= self._conn_success_threshold:
                    self._alert("✅ 连通性已恢复", f"连续成功 {self._conn_success_count} 次")
                    self._conn_anomaly = False
                    self._conn_success_count = 0
            else:
                self._conn_fail_count = 0

    def _report_conn_fail(self):
        with self._lock:
            if self._conn_anomaly:
                self._conn_success_count = 0
            else:
                self._conn_fail_count += 1
                if self._conn_fail_count >= self._conn_fail_threshold:
                    self._alert("❌ 连通性告警", f"连续失败 {self._conn_fail_count} 次")
                    self._conn_anomaly = True
                    self._conn_success_count = 0

    def _download_loop(self):
        if not self.download_urls or not self.download_enabled:
            return
        while not self.stop_event.is_set():
            success = False
            for idx, url in enumerate(self.download_urls):
                if self.stop_event.is_set():
                    break
                logger.info(f"[{self.proxy_label}] 下载 [{idx+1}/{len(self.download_urls)}] {url}")
                if not self.socks_available:
                    res = {"success": False, "speed": 0, "file_size": 0, "duration": 0, "error": "PySocks未安装", "exception": None}
                else:
                    res = download_with_proxy(url, self.proxy_url, self.download_timeout)
                self.db.save_download(self.proxy_url, url, res["success"], res["speed"], res["file_size"], res["duration"], res.get("error", ""))
                if res["success"]:
                    logger.info(f"[{self.proxy_label}] 下载成功 {res['speed']/1024:.1f} KB/s")
                    self._report_download_success()
                    success = True
                    break
                else:
                    logger.warning(f"[{self.proxy_label}] 下载失败: {res.get('error')}")
                    self._report_download_fail()
                    if "exception" in res and is_proxy_error(res["exception"]):
                        break
            if success:
                self.current_interval = self.base_interval
            else:
                self.current_interval = max(self.current_interval / 2, self.min_interval)
                logger.info(f"[{self.proxy_label}] 下载全失败，下次间隔 {self.current_interval:.0f}s")
            self._sleep(self.current_interval)

    def _ip_loop(self):
        if not self.ip_urls or not self.monitor_enabled:
            return
        while not self.stop_event.is_set():
            if self.socks_available:
                for idx, item in enumerate(self.ip_urls):
                    if self.stop_event.is_set():
                        break
                    url = item.get("url")
                    ip_path = item.get("ip_json_path", "ip")
                    city_path = item.get("city_json_path", "")
                    try:
                        proxies = {"http": self.proxy_url, "https": self.proxy_url}
                        resp = requests.get(url, proxies=proxies, timeout=self.ip_timeout)
                        resp.raise_for_status()
                        data = resp.json()
                        ip = json_value(data, ip_path)
                        city = json_value(data, city_path) if city_path else ""
                        self.db.save_ip(True, self.proxy_url, url, ip or "unknown", city, json.dumps(data, ensure_ascii=False))
                        logger.info(f"[{self.proxy_label}] 代理IP: {ip}")
                        break
                    except Exception as e:
                        logger.warning(f"[{self.proxy_label}] 代理IP检测失败 {url}: {e}")
                else:
                    self.db.save_ip(True, self.proxy_url, "", "error", "", "", "全部API失败")
            else:
                self.db.save_ip(True, self.proxy_url, "", "error", "", "", "PySocks未安装")
            self._sleep(self.ip_interval)

    def _conn_loop(self):
        if not self.conn_host or not self.conn_port or not self.monitor_enabled:
            return
        while not self.stop_event.is_set():
            ok, lat, err = check_tcp(self.conn_host, self.conn_port, self.conn_timeout)
            self.db.save_connectivity(self.proxy_url, self.conn_host, self.conn_port, ok, lat, err or "")
            status = "OK" if ok else "FAIL"
            logger.info(f"[{self.proxy_label}] 连通性 {status} {self.conn_host}:{self.conn_port} {lat:.1f}ms")
            if ok:
                self._report_conn_success()
            else:
                self._report_conn_fail()
            self._sleep(self.conn_interval)

    def _sleep(self, secs):
        for _ in range(int(secs)):
            if self.stop_event.is_set():
                break
            time.sleep(1)

    def start(self):
        threads = []
        if self.download_enabled:
            threads.append(threading.Thread(target=self._download_loop, daemon=True, name=f"DL-{self.proxy_label}"))
        if self.monitor_enabled:
            threads.append(threading.Thread(target=self._ip_loop, daemon=True, name=f"IP-{self.proxy_label}"))
            threads.append(threading.Thread(target=self._conn_loop, daemon=True, name=f"Conn-{self.proxy_label}"))
        for t in threads:
            t.start()
        if not threads:
            logger.info(f"[{self.proxy_label}] 所有功能已禁用，不启动线程")

    def shutdown(self):
        self.stop_event.set()

# --------------------- 主监控器 ---------------------
class Monitor:
    def __init__(self, config, db, socks_available):
        self.config = config
        self.db = db
        self.socks_available = socks_available
        self.stop_event = threading.Event()

        self.webhook = config.get("webhook", {}).get("dingtalk", "")
        self.title_prefix = config.get("startup_message", {}).get("title", "监控服务")

        proxy_list = config.get("proxy", [])
        if isinstance(proxy_list, dict):
            proxy_list = [proxy_list]

        active_proxies = []
        for p_cfg in proxy_list:
            dl = p_cfg.get("download_enabled", True)
            mon = p_cfg.get("monitor_enabled", True)
            if dl or mon:
                active_proxies.append(p_cfg)
            else:
                logger.info(f"跳过代理 {p_cfg.get('label', p_cfg.get('url', ''))}：两项均已禁用")

        self.watchers = [ProxyWatcher(p_cfg, config, db, socks_available, self.webhook, self.title_prefix)
                         for p_cfg in active_proxies]

        ip_cfg = config.get("ip_check", {})
        self.ip_urls = ip_cfg.get("urls", [])
        self.ip_timeout = ip_cfg.get("timeout", 10)
        self.ip_interval = ip_cfg.get("interval", 600)

        stats_cfg = config.get("statistics", {})
        self.stats_period = stats_cfg.get("period_hours", 24)
        self.stats_interval = stats_cfg.get("send_interval", 3600)
        self.retention_days = config.get("database", {}).get("retention_days", 60)

    def _direct_ip_loop(self):
        if not self.ip_urls:
            return
        while not self.stop_event.is_set():
            for item in self.ip_urls:
                if self.stop_event.is_set():
                    break
                url = item.get("url")
                ip_path = item.get("ip_json_path", "ip")
                city_path = item.get("city_json_path", "")
                try:
                    resp = requests.get(url, timeout=self.ip_timeout)
                    resp.raise_for_status()
                    data = resp.json()
                    ip = json_value(data, ip_path)
                    city = json_value(data, city_path) if city_path else ""
                    self.db.save_ip(False, "direct", url, ip or "unknown", city, json.dumps(data, ensure_ascii=False))
                    logger.info(f"直连IP: {ip}")
                    break
                except Exception as e:
                    logger.warning(f"直连IP检测失败 {url}: {e}")
            else:
                self.db.save_ip(False, "direct", "", "error", "", "", "全部API失败")
            self._sleep(self.ip_interval)

    def _stats_loop(self):
        self._sleep(self.stats_interval)
        while not self.stop_event.is_set():
            self.db.clean_old(self.retention_days)
            s = self.db.stats(self.stats_period)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            proxy_ips_str = "\n".join([f"  - {k}: {v}" for k, v in s['proxy_ips'].items()]) if s['proxy_ips'] else "  - 无数据"
            text = f"""## 📊 {self.title_prefix}统计报告 ({now})
---
**统计周期**: 最近 {self.stats_period} 小时

**下载任务 (汇总)**:
- 总次数: {s['download_total']}  成功: {s['download_success']}  失败: {s['download_fail']}
- 平均速度: {s['download_avg_speed']/1024:.1f} KB/s

**代理连通性 (汇总)**:
- 检测次数: {s['conn_total']}  成功: {s['conn_success']}  失败: {s['conn_fail']}
- 平均延迟: {s['conn_avg_latency']:.1f} ms

**当前公网IP**:
- 直连: {s['direct_ip']}
- 代理IP:
{proxy_ips_str}
"""
            send_dingtalk(self.webhook, f"{self.title_prefix}统计报告", text)
            self._sleep(self.stats_interval)

    def _sleep(self, secs):
        for _ in range(int(secs)):
            if self.stop_event.is_set():
                break
            time.sleep(1)

    def start(self):
        for w in self.watchers:
            w.start()
        threading.Thread(target=self._direct_ip_loop, daemon=True, name="DirectIP").start()
        threading.Thread(target=self._stats_loop, daemon=True, name="Stats").start()
        logger.info("所有监控线程已启动")

    def shutdown(self):
        self.stop_event.set()
        for w in self.watchers:
            w.shutdown()
        logger.info("监控停止信号已发送")

# --------------------- 启动消息构建 ---------------------
def build_startup_message(config, title_prefix):
    startup_cfg = config.get("startup_message", {})
    if not startup_cfg.get("enabled", True):
        return ""
    items = startup_cfg.get("items")
    if not items:
        items = ["proxy_list", "download_urls", "download_interval", "direct_ip", "proxy_outbound_ip", "proxy_connectivity"]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"## 🚀 {title_prefix}已启动 ({now})", "---"]

    proxy_list = config.get("proxy", [])
    if isinstance(proxy_list, dict):
        proxy_list = [proxy_list]

    active_proxies = []
    for p in proxy_list:
        dl = p.get("download_enabled", True)
        mon = p.get("monitor_enabled", True)
        if dl or mon:
            active_proxies.append(p)

    dl_cfg = config.get("download", {})
    dl_urls = dl_cfg.get("urls", [])
    dl_interval = dl_cfg.get("interval", 300)

    ip_cfg = config.get("ip_check", {})
    ip_urls = ip_cfg.get("urls", [])
    ip_timeout = ip_cfg.get("timeout", 10)

    socks_ok = check_socks_support()

    for item in items:
        if item == "proxy_list":
            lines.append("**代理列表**")
            for p in active_proxies:
                p_url = p.get("url", "")
                p_label = p.get("label", p_url)
                p_info = parse_proxy(p_url)
                host = p_info.get('host', '?')
                port = p_info.get('port', '?')
                auth = p_info.get('auth', '')
                user = auth.split(':')[0] if auth else ''
                user_str = f" (用户: {user})" if user else ""
                lines.append(f"  - {p_label}: {host}:{port}{user_str}")
            lines.append("")

        elif item == "download_urls":
            lines.append("**下载文件**")
            for u in dl_urls:
                lines.append(f"  - {u}")
            lines.append("")

        elif item == "download_interval":
            lines.append(f"**下载监测频率**: 每 {dl_interval} 秒")
            lines.append("")

        elif item == "direct_ip":
            direct_ip = "获取中..."
            direct_city = ""
            if ip_urls:
                for api in ip_urls:
                    url = api.get("url")
                    ip_path = api.get("ip_json_path", "ip")
                    city_path = api.get("city_json_path", "")
                    try:
                        resp = requests.get(url, timeout=ip_timeout)
                        data = resp.json()
                        direct_ip = json_value(data, ip_path) or "unknown"
                        if city_path:
                            direct_city = json_value(data, city_path) or ""
                        break
                    except:
                        pass
            ip_str = direct_ip
            if direct_city:
                ip_str += f" ({direct_city})"
            lines.append(f"**直连IP**: {ip_str}")
            lines.append("")

        elif item == "proxy_outbound_ip":
            lines.append("**代理出口IP**")
            for p in active_proxies:
                p_label = p.get("label", p.get("url", ""))
                if socks_ok or not p.get("url", "").lower().startswith("socks"):
                    out_ip, out_city = get_proxy_outbound_ip(p["url"], ip_urls, ip_timeout)
                else:
                    out_ip, out_city = "PySocks未安装", ""
                ip_str = out_ip
                if out_city:
                    ip_str += f" ({out_city})"
                lines.append(f"  - {p_label}: {ip_str}")
            lines.append("")

        elif item == "proxy_connectivity":
            lines.append("**代理连通性**")
            for p in active_proxies:
                p_label = p.get("label", p.get("url", ""))
                p_url = p.get("url", "")
                conn_cfg = p.get("connectivity", config.get("connectivity_check", {}))
                p_info = parse_proxy(p_url)
                host = conn_cfg.get("host") or p_info.get("host")
                port = conn_cfg.get("port") or p_info.get("port")
                if host and port:
                    ok, lat, _ = check_tcp(host, port, conn_cfg.get("timeout", 5))
                    status = f"✅ 正常 ({lat:.0f}ms)" if ok else "❌ 失败"
                else:
                    status = "⚠️ 配置缺失"
                lines.append(f"  - {p_label}: {status}")
            lines.append("")

    return "\n".join(lines)

# --------------------- 主程序 ---------------------
def main():
    args = sys.argv[1:]

    if not args:
        print_help()
        sys.exit(0)

    if args[0] in ("--help", "-h"):
        print_help()
        sys.exit(0)

    if args[0] == "install":
        config_file = args[1] if len(args) > 1 else None
        install_service(config_file)
        sys.exit(0)

    config_path = args[0]
    config = load_config(config_path)
    db = Database(config.get("database", {}).get("path", "monitor.db"))

    webhook = config.get("webhook", {}).get("dingtalk", "")
    title_prefix = config.get("startup_message", {}).get("title", "监控服务")

    startup_msg = build_startup_message(config, title_prefix)
    if startup_msg and webhook:
        send_dingtalk(webhook, f"{title_prefix}启动", startup_msg)

    socks_ok = check_socks_support()
    monitor = Monitor(config, db, socks_ok)
    monitor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("手动停止...")
        monitor.shutdown()
        logger.info("程序已退出")

if __name__ == "__main__":
    main()
