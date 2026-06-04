#!/bin/bash

# curl -o- https://raw.githubusercontent.com/te3030/Stand-alone-script/refs/heads/main/xray/build_xray.sh | bash

cd /etc/xray-node/ && cd - && mv /etc/xray-node/  /etc/xray-node-$(date +%Y%m%d%H%M%S)

mkdir /etc/xray-core
cd /etc/xray-core

wget https://github.com/XTLS/Xray-core/releases/download/v26.2.6/Xray-linux-64.zip

unzip -oq Xray-linux-64.zip 

uid=$(/etc/xray-core/xray uuid)

cat > "/etc/xray-core/config.json" <<EOF_UNIT
{
  "log": {
    "loglevel":"debug"
  },
  "inbounds": [
    {
      "listen": "0.0.0.0",
      "port": 12345,
      "protocol": "vmess",
      "settings": {
        "clients": [
          {
            "id": "${uid}",
            "alterId": 0,
            "email": "t@t.tt",
            "security": "auto",
            "level": 0
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "none"
      }
    }
  ],
  "outbounds": [
    {
      "tag": "direct",
      "protocol": "freedom",
      "settings": {}
    },
    {
      "tag": "blocked",
      "protocol": "blackhole",
      "settings": {}
    }
  ]
}
EOF_UNIT


cat > "/etc/xray-core/xray.service" <<EOF_UNIT
[Unit]
Description=Xray-core
Documentation=https://github.com/XTLS/Xray-core
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/etc/xray-core
ExecStart=/etc/xray-core/xray --config /etc/xray-core/config.json
Restart=always
RestartSec=5
LimitNOFILE=1048576
NoNewPrivileges=true
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF_UNIT

install -m 644 "/etc/xray-core/xray.service" "/etc/systemd/system/xray.service"
systemctl daemon-reload
systemctl enable "xray.service" > /dev/null 2>&1
systemctl restart xray.service

