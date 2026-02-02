#!/bin/bash

# DERL Lunar Jump - Ubuntu 20.04 Conda 完整安装脚本
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DERL Lunar Jump - Ubuntu 20.04 安装脚本${NC}"
echo -e "${BLUE}========================================${NC}\n"

# ============= 步骤1: 系统依赖安装 =============
echo -e "${YELLOW}[1/5] 安装Ubuntu系统依赖...${NC}"

sudo apt-get update -q 2>/dev/null || true

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    git \
    cmake \
    unzip \
    bzip2 \
    wget \
    libgl1-mesa-dev \
    libgl1-mesa-glx \
    libglew-dev \
    libosmesa6-dev \
    libopenmpi-dev \
    software-properties-common \
    net-tools \
    vim \
    ffmpeg \
    xpra \
    libglfw3-dev \
    xserver-xorg-dev \
    build-essential \
    python3-dev \
    > /dev/null 2>&1

echo -e "${GREEN}✓ 系统依赖安装完成${NC}"

# ============= 步骤2: 检测/安装MuJoCo 2.0 =============
echo -e "${YELLOW}[2/5] 检测/安装MuJoCo 2.0...${NC}"

MUJOCO_FOUND=0
MUJOCO_PATH=""

# 优先检测mujoco200 (兼容mujoco_py 2.x)
if [ -d "$HOME/.mujoco/mujoco200" ]; then
    MUJOCO_PATH="$HOME/.mujoco/mujoco200"
    MUJOCO_FOUND=1
    echo -e "${GREEN}✓ 检测到MuJoCo 2.0${NC}"
fi

# 检查unitree-rl中的mujoco
if [ "$MUJOCO_FOUND" -eq 0 ] && [ -d "$HOME/anaconda3/envs/unitree-rl/lib/python3.8/site-packages/mujoco" ]; then
    MUJOCO_PATH="$HOME/anaconda3/envs/unitree-rl/lib/python3.8/site-packages/mujoco"
    MUJOCO_FOUND=1
    echo -e "${GREEN}✓ 检测到MuJoCo (unitree-rl)${NC}"
fi

# 如果没找到mujoco200，则下载安装
if [ "$MUJOCO_FOUND" -eq 0 ]; then
    echo -e "${YELLOW}未找到MuJoCo 2.0，正在下载...${NC}"
    mkdir -p "$HOME/.mujoco"
    cd "$HOME/.mujoco"
    
    # 下载mujoco200
    if [ ! -d mujoco200 ]; then
        wget -q https://www.roboti.us/download/mujoco200_linux.zip 2>/dev/null || (echo -e "${RED}✗ 下载MuJoCo失败${NC}" && exit 1)
        unzip -q mujoco200_linux.zip
        mv mujoco200_linux mujoco200
        rm -f mujoco200_linux.zip
    fi
    
    MUJOCO_PATH="$HOME/.mujoco/mujoco200"
    MUJOCO_FOUND=1
    echo -e "${GREEN}✓ MuJoCo 2.0已安装${NC}"
fi

# 复制或链接mjkey.txt
mkdir -p "$HOME/.mujoco"
if [ -f "$HOME/yb/mujoco/mjkey.txt" ]; then
    cp "$HOME/yb/mujoco/mjkey.txt" "$HOME/.mujoco/mjkey.txt"
    echo -e "${GREEN}✓ mjkey.txt已配置${NC}"
elif [ -f "$HOME/Downloads/mjkey.txt" ]; then
    cp "$HOME/Downloads/mjkey.txt" "$HOME/.mujoco/mjkey.txt"
    echo -e "${GREEN}✓ mjkey.txt已配置${NC}"
fi

# ============= 步骤3: 创建Conda环境 =============
echo -e "${YELLOW}[3/5] 创建Conda环境...${NC}"

# 初始化Conda (支持anaconda3完整路径)
if [ -d "$HOME/anaconda3" ]; then
    eval "$($HOME/anaconda3/bin/conda shell.bash hook)"
elif [ -d "$HOME/miniconda3" ]; then
    eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
elif command -v conda &> /dev/null; then
    eval "$(conda shell.bash hook)"
else
    echo -e "${RED}✗ Conda未安装${NC}"
    echo "请先安装Miniconda或Anaconda: https://docs.conda.io/"
    exit 1
fi

# 创建环境
if conda env list | grep -q "derl_lunar_jump"; then
    echo -e "${YELLOW}环境已存在,跳过创建${NC}"
else
    conda create -n derl_lunar_jump python=3.8 -y > /dev/null 2>&1
fi

echo -e "${GREEN}✓ Conda环境创建完成${NC}"

# ============= 步骤4: 安装Python依赖 =============
echo -e "${YELLOW}[4/5] 安装Python依赖...${NC}"

# 激活环境并安装依赖
conda activate derl_lunar_jump

# 设置环境变量 (mujoco200)
export LD_LIBRARY_PATH="$MUJOCO_PATH/bin:${LD_LIBRARY_PATH}"
export MUJOCO_PY_MUJOCO_PATH="$MUJOCO_PATH"
export MUJOCO_PY_MJKEY_PATH="$HOME/.mujoco/mjkey.txt"

# 更新pip
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# 使用conda安装pyyaml（更稳定）
conda install -c conda-forge pyyaml -y > /dev/null 2>&1

# 降级Cython以兼容mujoco_py 2.x
pip install 'Cython<3' --no-deps -q

# 安装其他Python依赖
pip install --upgrade \
    lxml \
    networkx \
    numpy \
    scipy \
    gym==0.17.1 \
    mujoco_py==2.0.2.8 \
    imageio \
    imageio-ffmpeg \
    tqdm \
    tensorboard \
    torch \
    attrs \
    > /dev/null 2>&1

echo -e "${GREEN}✓ Python依赖安装完成${NC}"

# ============= 步骤5: 验证安装 =============
echo -e "${YELLOW}[5/5] 验证安装...${NC}"

python << 'PYEOF'
import sys
import os

# 检查关键环境变量
print("环境变量检查:")
print("-" * 40)
if 'LD_LIBRARY_PATH' in os.environ:
    ld_path = os.environ['LD_LIBRARY_PATH']
    if 'mujoco' in ld_path.lower():
        print("✓ LD_LIBRARY_PATH 已配置")
    else:
        print("⚠ LD_LIBRARY_PATH 已设置但不含MuJoCo路径")
else:
    print("⚠ LD_LIBRARY_PATH 未设置")

packages = [
    'numpy',
    'yaml',
    'lxml',
    'gym',
    'networkx',
    'imageio',
    'scipy',
    'tqdm',
    'torch',
]

print("\n已安装的依赖包:")
print("-" * 40)

success = 0
fail = 0

for pkg in packages:
    try:
        mod = __import__(pkg)
        version = getattr(mod, '__version__', 'unknown')
        print("✓ {:<15} (v{})".format(pkg, version))
        success += 1
    except ImportError as e:
        print("✗ {:<15} 失败: {}".format(pkg, str(e)))
        fail += 1

print("-" * 40)
print("总计: {} 成功, {} 失败\n".format(success, fail))

if fail == 0:
    print("✓ 所有关键依赖安装成功!")
else:
    print("⚠ 有{}个包失败,请检查错误信息".format(fail))
PYEOF

# ============= 配置环境变量 =============
echo -e "${BLUE}配置环境变量${NC}"

# 添加到.bashrc
if ! grep -q "MUJOCO_PY_MUJOCO_PATH" "$HOME/.bashrc"; then
    cat >> "$HOME/.bashrc" << 'BASHRC_END'

# DERL MuJoCo 2.0 环境变量
export MUJOCO_PATH="$HOME/.mujoco/mujoco200"
export LD_LIBRARY_PATH="$MUJOCO_PATH/bin:${LD_LIBRARY_PATH}"
export MUJOCO_PY_MUJOCO_PATH="$MUJOCO_PATH"
export MUJOCO_PY_MJKEY_PATH="$HOME/.mujoco/mjkey.txt"
BASHRC_END
    echo -e "${GREEN}✓ 环境变量已配置${NC}"
fi

# 添加conda激活脚本
mkdir -p "$HOME/anaconda3/envs/derl_lunar_jump/etc/conda/activate.d"
cat > "$HOME/anaconda3/envs/derl_lunar_jump/etc/conda/activate.d/derl_env.sh" << 'CONDA_END'
#!/bin/bash
export MUJOCO_PATH=$HOME/.mujoco/mujoco200
export LD_LIBRARY_PATH=$MUJOCO_PATH/bin:${LD_LIBRARY_PATH}
export MUJOCO_PY_MUJOCO_PATH=$MUJOCO_PATH
export MUJOCO_PY_MJKEY_PATH=$HOME/.mujoco/mjkey.txt
CONDA_END

chmod +x "$HOME/anaconda3/envs/derl_lunar_jump/etc/conda/activate.d/derl_env.sh"

# ============= 最终总结 =============
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 安装完成!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo "已安装的依赖:"
echo ""
echo "系统库:"
echo "  - libgl1-mesa-dev/glx (OpenGL)"
echo "  - libglew-dev (GLEW)"
echo "  - libosmesa6-dev (OSMesa)"
echo "  - libopenmpi-dev (OpenMPI)"
echo "  - libglfw3-dev (GLFW)"
echo "  - xserver-xorg-dev (X11)"
echo "  - build-essential (编译器)"
echo ""
echo "Python包:"
echo "  - numpy, scipy"
echo "  - gym==0.17.1 (RL框架)"
echo "  - mujoco_py==2.0.2.8 (MuJoCo绑定)"
echo "  - pyyaml, lxml, networkx (工具库)"
echo "  - imageio, imageio-ffmpeg (视频处理)"
echo "  - tensorboard, tqdm, attrs (辅助库)"
echo "  - torch (神经网络框架)"
echo ""
echo "MuJoCo:"
echo "  - mujoco200 (已安装,兼容mujoco_py)"
echo "  - mjkey.txt (许可证)"
echo ""
echo "下一步:"
echo "  1. 激活环境:  conda activate derl_lunar_jump"
echo "  2. 验证框架:  python test_lunar_jump_setup.py"
echo "  3. 启动训练:  python tools/evolution.py --config configs/evo/lunar_jump.yml"
echo ""
echo -e "${GREEN}========================================${NC}\n"
