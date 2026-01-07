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

### 第三步：拉取 Docker 镜像

本项目已将预构建的镜像托管到 Docker Hub，无需本地构建，直接拉取即可：

```bash
docker-compose pull
```

第一次运行需要从 Docker Hub 下载镜像，可能需要几分钟。看到类似以下输出表示成功：

```
Pulling sync ... done
Pulling login ... done
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
| 首次登录 | `docker-compose --profile login run --rm login` |
| 执行同步 | `docker-compose run --rm sync` |
| 查看日志 | `docker-compose logs sync` |
| 停止所有容器 | `docker-compose down` |

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
├── src/                    # 源代码
├── Dockerfile              # Docker 镜像定义
├── docker-compose.yml      # Docker 服务编排
└── DOCKER_SETUP.md         # 本文档
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
