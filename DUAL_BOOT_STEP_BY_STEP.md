# 双系统安装 - 完整分步指南

> 这是一份逐步执行的指南。按顺序完成每个步骤，不要跳过！

---

## 📋 整体流程

```
第一阶段（准备）：
  Step 0: 备份数据 ← 你现在的位置
  Step 1: 准备启动 U 盘
  Step 2: 分区调整

第二阶段（安装）：
  Step 3: 重启进入安装
  Step 4: Ubuntu 22.04 安装
  Step 5: 系统配置
  
第三阶段（验证）：
  Step 6: 验证双启动
  Step 7: Isaac Lab 准备
```

---

## 🚀 Step 0：备份数据（现在就做）

### 0.1 运行备份脚本

```bash
# 进入项目目录
cd /home/t/yb/agrimgupta_derl/derl

# 查看备份脚本
cat backup_before_dual_boot.sh

# 给脚本添加执行权限
chmod +x backup_before_dual_boot.sh

# 运行备份（需要输入密码）
./backup_before_dual_boot.sh
```

**预期输出**：
```
================================
  系统备份脚本
================================
备份时间：Mon Feb  2 21:30:45 CST 2026
备份位置：/home/t/backups/system_backup_20260202_213045

[1/4] 备份 DERL 项目...
✓ DERL 备份完成：2.3G
[2/4] 备份 Home 目录配置文件...
✓ 配置文件备份完成：45M
[3/4] 备份 Python 环境信息...
✓ Python 环境信息备份完成
[4/4] 备份系统配置信息...
✓ 系统配置备份完成

[完成] 生成备份清单...
================================
✅ 备份完成！
================================

/home/t/backups/system_backup_20260202_213045_derl.tar.gz (2.3G)
/home/t/backups/system_backup_20260202_213045_home_config.tar.gz (45M)
/home/t/backups/system_backup_20260202_213045_python_env.txt (12K)
/home/t/backups/system_backup_20260202_213045_system_info.txt (5K)
/home/t/backups/system_backup_20260202_213045_MANIFEST.txt (1.5K)

📌 重要：请将这些文件复制到外部存储设备（U盘/移动硬盘）
   以防安装双系统出错无法恢复！
```

### 0.2 验证备份完整性

```bash
# 列出所有备份
ls -lh /home/t/backups/

# 验证备份大小（DERL 备份应该 >= 2GB）
du -sh /home/t/backups/*

# 查看备份清单
cat /home/t/backups/system_backup_*_MANIFEST.txt
```

### 0.3 复制备份到外部存储（推荐）

**如果你有 U 盘或移动硬盘**：

```bash
# 插入 U 盘，等待自动挂载

# 查看 U 盘路径
lsblk
# 输出示例：
# sdb      8:0    1  29.3G  0 disk
# └─sdb1   8:1    1  29.3G  0 part  /media/t/KINGSTON

# 复制备份到 U 盘（假设 U 盘挂载在 /media/t/KINGSTON）
cp -r /home/t/backups/* /media/t/KINGSTON/

# 验证复制完成
ls -lh /media/t/KINGSTON/

# 安全弹出 U 盘
sudo eject /dev/sdb1
```

**如果没有外部存储**：
- 备份已经在 `/home/t/backups/` 目录
- 只要 Ubuntu 20.04 还能启动，就能恢复
- 但为了安全，建议还是用 U 盘备一份

---

## ✅ Step 0 完成检查清单

- [ ] 备份脚本已运行（看到 ✅ 备份完成）
- [ ] `/home/t/backups/` 目录中有 5 个文件
- [ ] 备份总大小 > 2.4GB
- [ ] （推荐）备份已复制到外部存储

---

## 🔧 Step 1：准备启动 U 盘

### 1.1 下载 Ubuntu 22.04 ISO

打开浏览器，访问：
```
https://releases.ubuntu.com/jammy/
```

下载：
```
ubuntu-22.04.3-desktop-amd64.iso (~3.4GB)
```

**下载到**：`/home/t/Downloads/`

**验证下载**：
```bash
# 检查文件大小（应该约 3.4GB）
ls -lh ~/Downloads/ubuntu-22.04.3-desktop-amd64.iso

# 校验 SHA256（可选）
sha256sum ~/Downloads/ubuntu-22.04.3-desktop-amd64.iso
# 对比网站上的 SHA256 值
```

### 1.2 准备 U 盘

```bash
# 插入 U 盘（>= 4GB）
# 等待自动挂载（会弹出文件管理器窗口）

# 查看 U 盘设备名
lsblk
# 输出示例：
# sdb      8:0    1  29.3G  0 disk
# └─sdb1   8:1    1  29.3G  0 part  /media/t/KINGSTON

# U 盘设备名通常是 /dev/sdb（不要用 /dev/sdb1）

# 卸载 U 盘
sudo umount /dev/sdb*

# 确认卸载（应该没有 /media/t/KINGSTON 这一行）
lsblk
```

### 1.3 写入 ISO 到 U 盘

**方法 A：用 dd（命令行，快速）**

```bash
# 写入 ISO（这个命令会持续 5-10 分钟）
# ⚠️ 确保 of=/dev/sdb 是正确的设备（不是 sdb1）！
sudo dd if=/home/t/Downloads/ubuntu-22.04.3-desktop-amd64.iso of=/dev/sdb bs=4M status=progress

# 完成后
sudo sync

# 卸载 U 盘
sudo umount /dev/sdb*

# 成功标志：命令返回到提示符，没有错误
```

**方法 B：用 GNOME Disks（图形界面，更安全）**

```bash
# 打开 GNOME Disks
gnome-disks

# 或在应用菜单中搜索 "Disks"

# 步骤：
# 1. 左边点击 U 盘（sdb）
# 2. 右上角三点菜单 → "Restore Disk Image"
# 3. 选择 ~/Downloads/ubuntu-22.04.3-desktop-amd64.iso
# 4. 点击 "Start Restoring"
# 5. 输入密码，等待完成（5-10 分钟）
```

### 1.4 验证启动 U 盘

```bash
# 重新插入 U 盘（如果拔出了）

# 查看 U 盘内容（应该能看到 boot 文件）
sudo file -s /dev/sdb1
# 输出应该包含：Linux 或 FAT

# 启动到 U 盘测试（可选，可以跳过）
# 只需重启，按 F12/F2 选择 U 盘启动
```

---

## ✅ Step 1 完成检查清单

- [ ] ISO 文件已下载（3.4GB，在 ~/Downloads/）
- [ ] U 盘已插入
- [ ] 已卸载 U 盘
- [ ] ISO 已写入 U 盘（用 dd 或 GNOME Disks）
- [ ] U 盘已弹出（可选再插入验证）

---

## 🔨 Step 2：分区调整（关键步骤）

**⚠️ 警告**：这是最危险的步骤。缩小分区可能导致数据丢失。  
**建议**：先完成备份，再操作。

### 2.1 安装 GParted

```bash
# 安装 GParted（图形化分区工具）
sudo apt install gparted -y

# 验证安装
which gparted
```

### 2.2 启动 GParted

```bash
# 启动 GParted
sudo gparted

# 或在应用菜单中搜索 "GParted"
```

### 2.3 缩小 /dev/sda5 分区

**在 GParted 窗口中**：

```
1. 确认选择了 /dev/sda 磁盘（左上角下拉菜单）

2. 找到 /dev/sda5 分区（应该显示 468 GB）

3. 右键点击 /dev/sda5 → "Resize/Move"

4. 在弹出窗口中：
   ┌─────────────────────────────┐
   │ Resize /dev/sda5            │
   ├─────────────────────────────┤
   │ New Size (MiB): 358400      │  ← 缩小到 350GB
   │ Free Space After: 150000    │  ← 留 150GB 给新系统
   │ Free Space Before: 0        │
   └─────────────────────────────┘
   
   修改 "New Size" 为：358400 MiB（= 350 GB）

5. 点击 "Resize" 按钮

6. 回到主窗口，看到操作列表：
   ├─ Resize /dev/sda5 [Pending]
   └─ (等待应用)

7. 点击 ✓ "Apply" 按钮（绿色勾号）

8. 确认操作（会显示警告）→ 点击 "Apply"
```

### 2.4 等待完成

```
进度条会显示缩小进度：

Progress:                 [████████░░░░░░░░░░] 45%

这可能需要 30-60 分钟，取决于磁盘速度和分区大小
```

**期间注意**：
- ⚠️ **不要关闭 GParted**
- ⚠️ **不要强制关机**
- ⚠️ **不要拔掉电源**
- ✅ 可以看书、喝咖啡等待

### 2.5 验证分区调整成功

```bash
# 关闭 GParted

# 在终端中验证
sudo parted -l

# 应该看到：
# Number  Start   End    Size   Type      File system
# 1       1049kB  538MB  537MB  primary   fat32
# 2       539MB   512GB  512GB  extended
# 5       539MB   376GB  350GB  logical   ext4    ← 缩小后
#         (未分配空间：376GB-512GB = 136GB)
```

---

## ✅ Step 2 完成检查清单

- [ ] GParted 已安装
- [ ] /dev/sda5 已缩小到 350GB（原来 468GB）
- [ ] 有 ~150GB 未分配空间
- [ ] 系统仍然能正常启动

---

## 🎯 目前为止的进度

```
✅ Step 0：备份完成
✅ Step 1：启动 U 盘准备完成
✅ Step 2：分区调整完成

🟡 Step 3-7：等待下一阶段指导
```

---

## 📞 接下来

完成 Step 0-2 后，**告诉我**：

1. 备份是否成功（看到 ✅ 标志）
2. Step 2 是否完成（分区调整）
3. 有没有任何错误信息

然后我会给你 **Step 3：重启安装** 的详细指导！

---

## 🆘 遇到问题？

### GParted 中看不到 /dev/sda5？
```bash
# 可能需要刷新
# 在 GParted 中：View → Refresh Devices（或按 F5）
```

### GParted 进度条卡住了？
- 等待至少 1 小时后再考虑中止
- 如果确实卡住，可以按 Ctrl+C（但会中止操作）

### 分区缩小失败？
```bash
# 可能是磁盘有坏块，尝试修复
sudo fsck -f /dev/sda5
# 然后重新缩小
```

**有问题随时问我！**
