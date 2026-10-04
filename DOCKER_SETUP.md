# Docker 部署指南

本指南将帮助您使用 Docker 快速部署 Garmin Weight Sync 项目。

---

## 前置要求

您的电脑需要安装 Docker。如果没有安装，请根据您的操作系统选择以下安装方式：

### Windows 用户

1. 访问 [Docker Desktop 官网](https://www.docker.com/products/docker-desktop)
2. 下载 Windows 版本的安装程序
3. 双击运行安装程序，按照提示完成安装
4. 安装完成后，重启电脑
5. 启动 Docker Desktop（第一次启动可能需要几分钟）

### Mac 用户

1. 确保您的 Mac 是 Intel 芯片或 Apple Silicon (M1/M2/M3)
2. 访问 [Docker Desktop 官网](https://www.docker.com/products/docker-desktop)
3. 下载 Mac 版本的安装程序
4. 双击拖拽到 Applications 文件夹完成安装
5. 启动 Docker Desktop（第一次启动可能需要几分钟）

### Linux 用户

```bash
# Ubuntu/Debian 系统
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 将当前用户添加到 docker 组（避免每次都用 sudo）
sudo usermod -aG docker $USER

# 重新登录或运行以下命令使组生效
newgrp docker
```

### 验证安装

打开终端（Terminal 或 CMD），输入以下命令验证 Docker 是否安装成功：

```bash
docker --version
docker-compose --version
```

如果显示版本号，说明安装成功！

---

## 快速开始

### 第一步：获取项目代码

如果您已经有项目代码，请跳过此步骤。

```bash
# 克隆项目（如果您有 GitHub 链接）
git clone <项目地址>
cd garmin-weight-sync

# 或者下载并解压项目压缩包后，进入项目目录
```

### 第二步：创建配置文件

项目目录下已有 `config/` 和 `data/` 文件夹。

1. 复制配置文件模板：

```bash
# Linux/Mac
cp config/users.json.template config/users.json

# Windows（在文件管理器中操作）
# 进入 config 文件夹，复制 users.json.template 并重命名为 users.json
```

2. 使用文本编辑器打开 `config/users.json`，填写您的账户信息：

```json
{
    "users": [
        {
            "username": "您的手机号或邮箱",
            "password": "小米账号密码",
            "model": "yunmai.scales.ms103",
            "token": {
                "userId": "",
                "passToken": "",
                "ssecurity": ""
            },
            "garmin": {
                "email": "您的佳明账号邮箱",
                "password": "佳明账号密码",
                "domain": "CN"
            }
        }
    ]
}
```

**重要参数说明：**

| 参数 | 说明 | 示例值 |
|------|------|--------|
| `username` | 小米账号手机号或邮箱 | `13800138000` 或 `example@qq.com` |
| `password` | 小米账号密码 | `your_password` |
| `model` | 设备型号，小米体脂秤 S400 填此项 | `yunmai.scales.ms103` |
| `garmin.domain` | 佳明服务器区域 | 中国区填 `CN`，国际区填 `COM` |
| `token` | 首次留空，登录后自动填充 | 留空即可 |

### 第三步：拉取 Docker 镜像（或本地构建）

#### 拉取 Docker 镜像

本项目已将预构建的镜像托管到 Docker Hub，无需本地构建，直接拉取即可：

```bash
docker-compose pull
```

第一次运行需要从 Docker Hub 下载镜像，可能需要几分钟。看到类似以下输出表示成功：

```
Pulling sync ... done
Pulling login ... done
```

#### 本地构建（如项目有更新）

如果项目添加了新功能或文件（如 `daily_sync.py`），Docker Hub 的预构建镜像可能不包含这些更新。此时需要本地构建：

```bash
docker-compose build --no-cache
```

这会基于本地的 `Dockerfile` 和源代码重新构建镜像。首次构建可能需要 2-3 分钟。

#### 删除镜像（当需要时）

删除本地构建的镜像：

```bash
# 删除 daily_sync 相关的镜像
docker-compose down daily_sync
docker image rm lesliehwang/garmin-weight-sync:latest

# 或重新构建时覆盖旧镜像
docker-compose build --no-cache
```

### 第四步：首次登录（获取小米授权）

由于小米账号需要验证码登录，第一次需要运行登录服务：

```bash
docker-compose --profile login run --rm login
```

**登录流程：**

1. 程序会提示输入小米账号密码（已在配置文件中）
2. 如果需要图形验证码，程序会自动在浏览器中打开验证码图片
3. 看清验证码后，在终端中输入并回车
4. 如果开启了二次验证（2FA），输入手机收到的 6 位验证码
5. 登录成功后，程序会自动更新 `config/users.json` 中的 token 信息

看到 `Login SUCCESS!` 提示后，表示授权成功，以后不需要再运行此步骤。

### 第五步：执行同步

授权完成后，运行以下命令开始同步数据：

```bash
docker-compose run --rm sync
```

**程序执行流程：**

1. 使用已保存的 token 自动登录小米账号
2. 获取最新的体重数据（默认显示最近 10 条）
3. 在 `data/garmin-fit/` 目录下生成 FIT 文件
4. 自动登录佳明 Connect 并上传数据
5. 备份数据保存到 `data/weight_data_*.json`

**成功输出示例：**

```
Successfully synchronized weight data to Garmin Connect!
```

### 第六步：查看生成的文件

```bash
# 查看生成的 FIT 文件
ls -la data/garmin-fit/

# 查看数据备份
ls -la data/weight_data_*.json
```

---

## 设置定时自动同步（可选）

如果您希望每天自动同步，可以设置定时任务。

### 使用持续运行的容器（推荐）

此方式在 Docker 中持续运行一个容器，自动每日同步数据。容器支持自动重启，无需外部定时任务。

#### 启动持续同步容器

1. 确保已完成首次登录（第四步）。
2. 运行以下命令启动容器：
   ```bash
   docker-compose up -d daily_sync
   ```
   - `-d` 表示后台运行（detached mode）。
   - 容器启动后会**延迟 5 分钟**，然后开始同步。
   - 之后每 **24 小时** 自动同步一次。

#### 管理 daily_sync 容器

| 操作 | 命令 | 说明 |
|------|------|------|
| 启动容器 | `docker-compose up -d daily_sync` | 后台启动，会立即延迟 5 分钟后开始 |
| 查看状态 | `docker-compose ps` | 显示所有容器状态 |
| 查看日志 | `docker-compose logs -f daily_sync` | 实时查看同步日志，按 `Ctrl+C` 退出 |
| 停止容器 | `docker-compose stop daily_sync` | 暂停容器（可稍后重启） |
| 重启容器 | `docker-compose restart daily_sync` | 重启容器 |
| 删除容器 | `docker-compose down daily_sync` | 完全停止并删除容器 |

#### 自定义同步参数（可选）

如需自定义延迟时间或同步间隔，可修改 `docker-compose.yml` 中 `daily_sync` 的 `command` 参数：

```yaml
command: ["python", "src/daily_sync.py", "--config", "config/users.json", "--sync", "--delay", "600", "--interval", "43200"]
```

参数说明：
- `--delay 600`：启动后延迟 600 秒（10 分钟）再进行首次同步。默认 300 秒。
- `--interval 43200`：每次同步间隔 43200 秒（12 小时）。默认 86400 秒（24 小时）。

#### 日志保存

容器的日志可以通过以下方式查看：

```bash
# 实时日志
docker-compose logs -f daily_sync

# 查看最后 100 行
docker-compose logs -n 100 daily_sync

# 保存日志到文件
docker-compose logs daily_sync > sync_logs.txt
```

#### 重启策略

`daily_sync` 容器配置了 `restart: unless-stopped`，表示：
- 容器意外停止时**自动重启**。
- 只有通过 `docker-compose stop` 或 `docker-compose down` 才会停止。
- Docker 守护进程重启后，容器也会自动启动。

#### 容器重启流程

如果容器因任何原因重启：
1. 容器启动
2. 延迟 5 分钟（防止频繁重启时立即运行）
3. 执行同步
4. 等待 24 小时后继续同步

---

### Windows 用户（任务计划程序）

1. 按 `Win + R`，输入 `taskschd.msc` 并回车
2. 点击右侧 "创建基本任务"
3. 填写名称（如 "Garmin 体重同步"），点击下一步
4. 选择触发器（如 "每天"），设置时间，点击下一步
5. 选择 "启动程序"，点击下一步
6. 在 "程序或脚本" 中输入：
   ```
   docker-compose
   ```
7. 在 "添加参数" 中输入：
   ```
   run --rm sync
   ```
8. 在 "起始于" 中输入项目的完整路径（如 `D:\garmin-weight-sync`）
9. 完成创建

### Mac/Linux 用户（crontab）

1. 打开终端，输入：
   ```bash
   crontab -e
   ```

2. 在文件末尾添加以下行（每天凌晨 2 点执行）：
   ```bash
   0 2 * * * cd /您的项目完整路径 && docker-compose run --rm sync >> /您的项目完整路径/data/sync.log 2>&1
   ```

3. 保存并退出（vi 编辑器按 `ESC`，输入 `:wq` 并回车）

**crontab 时间格式说明：**

```
┌───────────── 分钟 (0 - 59)
│ ┌───────────── 小时 (0 - 23)
│ │ ┌───────────── 日 (1 - 31)
│ │ │ ┌───────────── 月 (1 - 12)
│ │ │ │ ┌───────────── 星期 (0 - 7，0和7都代表周日)
│ │ │ │ │
* * * * * 要执行的命令
```

示例：
- `0 2 * * *` - 每天凌晨 2 点
- `0 */6 * * *` - 每 6 小时
- `0 8,20 * * *` - 每天 8 点和 20 点

---

## 常见命令速查

| 操作 | 命令 |
|------|------|
| 拉取镜像 | `docker-compose pull` |
| 本地构建镜像 | `docker-compose build --no-cache` |
| 首次登录 | `docker-compose --profile login run --rm login` |
| 执行同步 | `docker-compose run --rm sync` |
| 查看日志 | `docker-compose logs sync` |
| 停止所有容器 | `docker-compose down` |

### daily_sync 容器命令

| 操作 | 命令 |
|------|------|
| 启动持续同步 | `docker-compose up -d daily_sync` |
| 查看 daily_sync 日志 | `docker-compose logs -f daily_sync` |
| 停止 daily_sync | `docker-compose stop daily_sync` |

---

## 目录结构说明

```
garmin-weight-sync/
├── config/
│   ├── users.json          # 您的配置文件（含密码，不要分享！）
│   └── users.json.template # 配置文件模板
├── data/
│   ├── garmin-fit/         # 生成的 FIT 文件
│   ├── weight_data_*.json  # 数据备份
│   └── sync.log            # 定时任务日志（如设置）
├── src/
│   ├── main.py             # 主同步程序
│   ├── daily_sync.py       # 持续同步程序（新增）
│   └── ...                 # 其他源代码
├── Dockerfile              # Docker 镜像定义
├── docker-compose.yml      # Docker 服务编排
├── DOCKER_SETUP.md         # Docker 部署指南（本文档）
├── DAILY_SYNC.md           # Daily Sync 使用指南（新增）
└── README.md               # 项目说明
```

---

## 常见问题

### Q: 提示 "Cannot connect to the Docker daemon"

**A:** Docker Desktop 没有启动。请启动 Docker Desktop 应用程序，等待其完全启动后再试。

### Q: 提示 "No such file or directory: config/users.json"

**A:** 您需要先创建配置文件。请参考 "第二步：创建配置文件"。

### Q: 首次登录时验证码图片无法打开

**A:** 检查您的浏览器是否正常运行。也可以手动打开终端中显示的图片链接。

### Q: 同步时提示 "Duplicate"

**A:** 这不是错误！表示佳明服务器已经存在这条记录，程序会自动跳过重复数据。

### Q: token 过期怎么办？

**A:** 重新运行登录命令即可：
```bash
docker-compose --profile login run --rm login
```

### Q: 如何查看详细日志？

**A:** 运行时添加日志输出：
```bash
docker-compose run --rm sync
```
或者查看定时任务日志：
```bash
cat data/sync.log
```


### Q: Windows 提示找不到 docker-compose 命令

**A:** 新版本的 Docker Desktop 已将 docker-compose 整合到 docker 命令中。请使用：
```bash
docker compose run --rm sync
```
（注意是 `docker compose` 而不是 `docker-compose`）

### daily_sync 相关问题

#### Q: daily_sync 容器无法启动

**症状**：运行 `docker-compose up -d daily_sync` 后没有响应，或提示 "can't open file '/app/src/daily_sync.py'"

**解决方案**：
1. 查看错误日志：`docker-compose logs daily_sync`
2. 如果提示找不到 `daily_sync.py`，需要本地构建：`docker-compose build --no-cache`
3. 确保配置文件存在：`config/users.json` 是否存在
4. 尝试重建：`docker-compose up -d --build daily_sync`

#### Q: daily_sync 容器启动后没有同步怎么办？

**A:** daily_sync 容器启动后会延迟 5 分钟，然后才进行首次同步。您可以：
1. 使用 `docker-compose logs -f daily_sync` 查看实时日志，等待同步开始。
2. 如果日志显示错误，检查 `config/users.json` 配置是否正确。
3. 确保已完成首次登录（第四步）。

#### Q: daily_sync 容器中的同步失败怎么办？

**A:** 容器会自动在 1 小时后重试。您也可以：
1. 查看日志：`docker-compose logs -f daily_sync`
2. 检查网络连接是否正常
3. 验证 `config/users.json` 中的用户名、密码和 token 是否有效
4. 必要时重新运行登录：`docker-compose --profile login run --rm login`

#### Q: 如何暂停 daily_sync 的自动同步？

**A:** 使用以下命令暂停容器（不会删除容器配置）：
```bash
docker-compose stop daily_sync
```
要重新启动，使用：
```bash
docker-compose restart daily_sync
```

#### Q: daily_sync 容器重启时会丢失数据吗？

**A:** 不会。所有数据都存储在 `config/` 和 `data/` 目录中，这些目录已通过 volumes 映射到容器内，数据不会丢失。

#### Q: 如何修改 daily_sync 的同步间隔？

**A:** 修改 `docker-compose.yml` 中 `daily_sync` 服务的 `command` 参数：
```yaml
command: ["python", "src/daily_sync.py", "--config", "config/users.json", "--sync", "--interval", "43200"]
```
其中 `--interval 43200` 表示 12 小时（单位为秒）。修改后重启容器：
```bash
docker-compose restart daily_sync
```

#### Q: 运行 daily_sync 时提示 "can't open file '/app/src/daily_sync.py': No such file or directory"

**A:** 这是因为 Docker Hub 的预构建镜像是旧版本，不包含 `daily_sync.py` 文件。需要本地构建镜像：
```bash
docker-compose build --no-cache
```
构建完成后重新启动容器：
```bash
docker-compose up -d daily_sync
```

---

## 安全提示

1. **config/users.json 包含您的明文密码和敏感信息，请勿分享给他人或上传到公开网站**
2. 建议定期更换密码
3. 如果不慎泄露了配置文件，请立即修改相关账号密码

---

## 需要帮助？

如果遇到其他问题，可以：

1. 查看项目主 README.md 了解更多使用说明
2. 检查 Docker 容器日志：`docker-compose logs sync`
3. 重新构建镜像：`docker-compose build --no-cache`
