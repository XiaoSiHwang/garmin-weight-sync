# 小米体重秤自动同步到佳明 (Garmin) 工具

本工具可以将小米运动健康 (Mi Fitness) 中的体重数据，自动生成 Garmin 兼容的 FIT 文件并同步到佳明 Connect 账户。目前支持所有已经导入到小米运动健康中的体重数据。

---

## 📖 目录
1. [新手环境准备](#1-新手环境准备)
2. [下载与安装](#2-下载与安装)
3. [快速配置](#3-快速配置)
4. [核心使用流程](#4-核心使用流程)
5. [进阶功能说明](#5-进阶功能说明)
6. [数据过滤配置](#6-数据过滤配置)
7. [常见问题 (FAQ)](#7-常见问题-faq)

---

## 1. 新手环境准备

### 项目结构说明
```text
garmin-weight-sync/
├── src/                # 源代码文件夹
│   ├── xiaomi/         # 小米登录与数据获取模块
│   ├── garmin/         # 佳明上传与文件生成模块
│   └── main.py         # 一键同步主程序
├── users.json          # 您的核心配置文件 (存账号密码)
├── requirements.txt    # 必须安装的程序组件包
└── README.md           # 您正在看的这份文档
```

在开始使用之前，您需要确保电脑上安装了 Python（这是运行此程序的程序包）。

### 第一步：安装 Python
1. 访问 [Python 官网](https://www.python.org/downloads/)。
2. 下载并安装 **Python 3.12.6** **3.14会导致同步不了**。
3. **特别注意**：安装过程中，一定要勾选 **"Add Python to PATH"**（将 Python 添加到系统变量）。

### 第二步：确认安装成功
打开您的终端（Windows 用户按 `Win+R` 输入 `cmd`；Mac 用户打开 `Terminal`），输入以下命令并按回车：
```bash
python --version
```
如果显示 `Python 3.12.x`，说明安装成功。

---

## 2. 下载与安装

### 第一步：建立虚拟环境（推荐）
虚拟环境可以防止项目依赖与您的系统环境产生冲突。
```bash
# 进入项目目录（请根据您的实际路径操作）
cd garmin-weight-sync

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows 用户:
.venv\Scripts\activate
# Mac/Linux 用户:
source .venv/bin/activate
```

### 第二步：一键安装依赖
```bash
pip install -r requirements.txt
```

---

## 2.5. Docker 部署（推荐）

如果您不想安装 Python 环境，可以使用 Docker 方式部署，更加简单快捷。

### 前置要求

安装 Docker Desktop：
- Windows/Mac: 访问 [Docker Desktop 官网](https://www.docker.com/products/docker-desktop) 下载安装
- Linux: 运行 `curl -fsSL https://get.docker.com | sh`

验证安装：
```bash
docker --version
```

### 快速开始

1. **获取项目代码**
   ```bash
   git clone https://github.com/XiaoSiHwang/garmin-weight-sync.git
   cd garmin-weight-sync
   ```
1.1 **实在不会你就手动下载这个，点击CODE那里可以下载解压**
![alt text](doc/image.png)
1. **创建配置文件**
   ```bash
   # Linux/Mac
   makdir config && makdir data **实在不会你就手动创建个两个文件夹叫config 和 data，记得是在这个路径下**
   cp users.json config/users.json

   # Windows 用户在文件管理器创建 
   ```

   编辑 `config/users.json`，填写您的账户信息（参考下方"快速配置"章节）。

2. **拉取 Docker 镜像**
   ```bash
   docker-compose pull
   ```

3. **首次登录（获取小米授权）**
   ```bash
   docker-compose --profile login run --rm login
   ```

   按照提示完成小米账号的验证码登录流程。

4. **执行同步**
   ```bash
   docker-compose run --rm sync
   ```

### 设置定时任务

**Linux/Mac (crontab)**:
![alt text](doc/image2.png)
```bash
# 先找 docker-compose 的真实路径 这边最重要，要不然corn 是没法执行命令的
which docker-compose 
## 输出的结果替换下面定时任务的路径 以我为例我输出是 /usr/local/bin/docker-compose
## 也有可能是/usr/bin/docker-compose
#输出如上图
# 每天凌晨 2 点自动同步
crontab -e ## 配置定时任务
0 2 * * * cd /您的项目路径 && /usr/local/bin/docker-compose run --rm sync
## 最后保存即可，记得上面的docker-compose别照抄，你们环境不一定和我一样，先获取路径再填写
```

**Windows (任务计划程序)**:
- 创建基本任务
- 程序: `docker-compose`
- 参数: `run --rm sync`
- 起始于: 项目完整路径

### 常用命令

| 操作 | 命令 |
|------|------|
| 拉取镜像 | `docker-compose pull` |
| 首次登录 | `docker-compose --profile login run --rm login` |
| 执行同步 | `docker-compose run --rm sync` |
| 查看日志 | `docker-compose logs sync` |

**详细文档**: 请查看 [DOCKER_SETUP.md](DOCKER_SETUP.md) 了解更多 Docker 部署说明。

---

## 3. 快速配置

在项目文件夹中，找到 `users.json` 文件（如果没有，请手动新建一个）。**这是程序唯一的配置文件。**

### 配置文件模板
请填入您的小米和佳明账户信息：

```json
{
    "users": [
        {
            "username": "您的手机号/邮箱",   
            "password": "小米账号密码",      
            "model": "yunmai.scales.ms103",
            "token": {
                "userId": "",
                "passToken": "",
                "ssecurity": ""
            },
            "garmin": {
                "email": "您的佳明账号",     
                "password": "佳明账号密码",  
                "domain": "CN"              
            }
        }
    ]
}
```

### 关键参数说明：
- **model**: 设备型号。如果您使用的是 **小米体脂秤 S400**，请填 `yunmai.scales.ms103`。如果你不知道设备信号，保持默认即可，目前支持所有已经导入到小米运动健康中的体重数据。所以只要你的体重数据已经同步到小米运动健康，就可以忽略这个参数。
- **domain**: 佳明服务器区域。**中国区**填 `CN`，**国际区**（如台湾、香港、美国）填 `COM`。
- **token**: 初始留空即可。程序运行成功后会自动保存登录凭证，下次无需重复输入。

---

## 4. 核心使用流程

### 第一阶段：获取小米授权 (仅需执行一次)
因为小米账号需要处理图形验证码或短信验证，我们需要手动运行登录工具：

```bash
python src/xiaomi/login.py --config users.json
```

1. **图形验证码**：程序会自动在您的网页浏览器中打开一张图片。看清验证码后，回到终端输入并回车。
2. **2FA 验证**：如果您的账号开启了二次验证，程序会提示已发送验证码到您的手机，输入收到的 6 位数字即可。
3. **成功提示**：看到 `✅ Login SUCCESS!` 后，程序会自动更新 `users.json`。

### 第二阶段：同步数据到佳明
授权成功后，运行主程序开始同步：

```bash
# 获取数据、生成 FIT 文件、并全自动同步到佳明
python src/main.py --config users.json --sync
```

**程序运行时会做什么：**
1. 自动登录您的小米账户（使用之前获取的 Token）。
2. 从小米服务器拉取您的历史体重记录（默认显示最近 10 条）。
3. 自动在本地 `weight_data_{账户}.json` 备份数据。
4. 在 `garmin-fit/` 文件夹下生成佳明专用的数据文件。
5. 自动登录佳明系统并将数据同步上去。

---

## 5. 进阶功能说明

### 常用命令参数
- `--limit N`: 指定显示多少条最近的体重记录（默认 10）。
- `--fit`: 仅生成本地 FIT 文件，不上传。
- `--sync`: 同时执行生成和上传（一键同步模式）。

### 定时自动同步 (长期使用)
您可以设置定时任务（如 Linux 的 `cron` 或 Windows 的任务计划程序），每天自动运行：
```bash
# 示例：每天凌晨 2 点执行同步
0 2 * * * cd /您的项目路径 && .venv/bin/python src/main.py --sync
```

---

## 6. 数据过滤配置 

本工具支持在同步数据前根据健康指标过滤体重数据。详细配置请查看 [FILTER_CONFIG.md](FILTER_CONFIG.md)。

### 快速示例

在 `users.json` 中为每个用户配置独立的过滤规则：

```json
{
    "users": [
        {
            "username": "您的手机号/邮箱",
            "password": "小米账号密码",
            "model": "yunmai.scales.ms103",
            "token": { ... },
            "garmin": {
                "email": "您的佳明账号",
                "password": "佳明账号密码",
                "domain": "CN",
                "filter": {
                    "enabled": true,
                    "conditions": [
                        { "field": "Weight", "operator": "between", "value": [60, 70] }
                    ],
                    "logic": "and"
                }
            }
        }
    ]
}
```

### 功能特性
- 支持按体重、BMI、体脂率等多个指标过滤
- 支持多个条件组合（AND/OR 逻辑）
- 每个用户可独立配置过滤规则
- 向后兼容，不配置则同步所有数据

**完整文档**: [FILTER_CONFIG.md](FILTER_CONFIG.md)

---

## 7. 常见问题 (FAQ)

### Q: 提示 `ModuleNotFoundError: No module named 'requests'` 怎么办？
A: 确保您已激活虚拟环境并运行了 `pip install -r requirements.txt`。

### Q: 佳明上传一直提示 `Duplicate` 怎么办？
A: 说明佳明服务器已经存在这一份记录。佳明会自动识别重复数据并跳过，这不是错误，无需处理。

### Q: 换了新电脑/账号变动怎么办？
A: 删除 `users.json` 中的 `token` 部分，重新运行 `python src/xiaomi/login.py` 即可。

### Q: 支持哪些小米秤？
A: 理论上支持小米运动健康里绑定的所有体脂秤。如果默认 model 无法获取数据，请尝试在 App 内查看设备的插件信息获取对应 ID。

---

## 🛡️ 安全提示
- **users.json** 包含您的明文密码和敏感 Token，**请勿通过任何方式分享该文件**。
- 请勿将 `.venv/`、`.garth/` 和 `users.json` 添加到 `.gitignore` 以防意外提交到公开 GitHub。

---

## ✨ 许可证
MIT License. 开发者：Leslie
参考项目：[XiaomiGateway3](https://github.com/AlexxIT/XiaomiGateway3), [garth](https://github.com/matin/garth)
