#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# DERL 机器人MuJoCo可视化脚本
# ═══════════════════════════════════════════════════════════════
# 用法: ./show_robot.sh <索引1> [索引2] [索引3] ...
# 示例:
#   ./show_robot.sh 0          # 显示第0个机器人
#   ./show_robot.sh 0 10 100   # 连续显示第0、10、100个机器人
#   ./show_robot.sh 0 100 200  # 连续显示第0、100、200个机器人
# ═══════════════════════════════════════════════════════════════

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 激活conda环境
source activate derl_lunar_jump 2>/dev/null

# 进入项目父目录（tools脚本位置）
cd "$SCRIPT_DIR/.."

# 如果没有提供参数，显示帮助信息
if [ -z "$1" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "🤖 DERL 机器人可视化工具"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "📍 已发现 $(ls output/lunar_jump/xml/*.xml 2>/dev/null | wc -l) 个机器人"
    echo ""
    echo "💡 使用方式:"
    echo "   ./show_robot.sh 0              # 显示第一个机器人"
    echo "   ./show_robot.sh 500            # 显示第500个机器人"
    echo "   ./show_robot.sh 0 100 200      # 连续显示第0、100、200个机器人"
    echo "   ./show_robot.sh 0 10 20 30 40  # 连续显示多个机器人"
    echo ""
    echo "🎮 MuJoCo窗口操作:"
    echo "   右键拖动  - 旋转视角"
    echo "   滚轮/中键 - 缩放"
    echo "   ESC键     - 退出（继续显示下一个机器人）"
    echo ""
    echo "📋 查看机器人统计信息:"
    echo "   python tools/inspect_robots.py              # 检查所有机器人"
    echo "   python tools/inspect_robots.py --sample 50  # 随机抽样检查"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    exit 0
fi

# 遍历所有提供的索引参数
for index in "$@"; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📍 显示机器人 #$index"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 运行可视化脚本
    python tools/show_robot.py "$index"
    
    # 检查返回值
    if [ $? -ne 0 ]; then
        echo "❌ 显示机器人 #$index 失败，跳过"
    fi
done

echo ""
echo "✅ 批量可视化完成！"
echo ""
