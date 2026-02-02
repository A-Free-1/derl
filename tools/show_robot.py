#!/usr/bin/env python
"""
MuJoCo 实时可视化工具 - 显示已生成的机器人xml文件
用法: ./show_robot.sh 0
     ./show_robot.sh 100
"""

import argparse
import os
import sys
from pathlib import Path

from mujoco_py import MjSim, MjViewer, load_model_from_xml


def show_robot(index, output_dir="output/lunar_jump"):
    """显示指定索引的机器人"""
    
    # 获取xml文件夹
    xml_dir = os.path.join(output_dir, "xml")
    if not os.path.exists(xml_dir):
        print(f"❌ XML文件夹不存在: {xml_dir}")
        return False
    
    # 列出所有xml文件
    xml_files = sorted([f for f in os.listdir(xml_dir) if f.endswith('.xml')])
    if not xml_files:
        print(f"❌ 没有找到XML文件: {xml_dir}")
        return False
    
    if index >= len(xml_files):
        print(f"❌ 索引超出范围: {index} (总共{len(xml_files)}个文件)")
        return False
    
    xml_filename = xml_files[index]
    xml_filepath = os.path.join(xml_dir, xml_filename)
    unimal_id = Path(xml_filename).stem
    
    print(f"\n{'='*60}")
    print(f"🤖 可视化机器人 #{index}")
    print(f"{'='*60}")
    print(f"文件名: {xml_filename}")
    print(f"ID: {unimal_id}")
    print(f"总数: {len(xml_files)}")
    print(f"\n💡 操作说明:")
    print(f"   右键拖动 - 旋转视角")
    print(f"   滚轮 - 缩放")
    print(f"   ESC或关闭窗口 - 退出")
    print(f"{'='*60}\n")
    
    try:
        # 直接从文件加载XML（这样可以获得已保存的完整机器人）
        print(f"📂 加载XML: {xml_filepath}")
        with open(xml_filepath, 'r') as f:
            xml_str = f.read()
        
        # 修复XML：取消注释floor
        # 原XML中floor被注释了，需要启用它以获得视觉参考
        if '<!-- <geom name="floor"' in xml_str:
            xml_str = xml_str.replace(
                '<!-- <geom name="floor" type="plane" pos="0 0 0" size="50 50 1" material="grid"/> -->',
                '<geom name="floor" type="plane" pos="0 0 0" size="50 50 1" material="grid"/>'
            )
            print("✏️  已启用floor（地板）")
        
        # 创建MuJoCo模型和仿真
        model = load_model_from_xml(xml_str)
        sim = MjSim(model)
        
        # 调试：打印模型信息
        print(f"\n📊 模型信息:")
        print(f"   Bodies: {model.nbody}")
        print(f"   Geoms: {model.ngeom}")
        print(f"   Joints: {model.njnt}")
        
        # 仿真一步来获取几何体位置
        sim.step()
        
        if model.ngeom > 0:
            geom_positions = sim.data.geom_xpos
            print(f"   几何体位置范围:")
            print(f"     X: [{geom_positions[:, 0].min():.2f}, {geom_positions[:, 0].max():.2f}]")
            print(f"     Y: [{geom_positions[:, 1].min():.2f}, {geom_positions[:, 1].max():.2f}]")
            print(f"     Z: [{geom_positions[:, 2].min():.2f}, {geom_positions[:, 2].max():.2f}]")
            
            # 自动计算摄像头距离和焦点（基于实际的几何体位置）
            max_extent = max(
                geom_positions[:, 0].max() - geom_positions[:, 0].min(),
                geom_positions[:, 1].max() - geom_positions[:, 1].min(),
                geom_positions[:, 2].max() - geom_positions[:, 2].min()
            )
            center = [
                (geom_positions[:, 0].min() + geom_positions[:, 0].max()) / 2,
                (geom_positions[:, 1].min() + geom_positions[:, 1].max()) / 2,
                (geom_positions[:, 2].min() + geom_positions[:, 2].max()) / 2,
            ]
            # 确保摄像头距离足够看到整个机器人
            cam_distance = max(max_extent * 3, 2.5)
            
            print(f"\n   自动摄像头:")
            print(f"     距离: {cam_distance:.2f}")
            print(f"     焦点: [{center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f}]")
        else:
            cam_distance = 4.0
            center = [0, 0, 0.5]
            print(f"   ⚠️  没有几何体，使用默认摄像头")
        
        # 创建查看器并设置摄像头
        viewer = MjViewer(sim)
        
        # 设置摄像头参数 - 固定视角，但每帧手动更新焦点跟随机器人
        viewer.cam.distance = cam_distance
        viewer.cam.elevation = -20  # 从上方俯视
        viewer.cam.azimuth = 45     # 侧视角
        
        # 获取躯干body的ID用于跟踪
        try:
            torso_body_id = sim.model.body_name2id("torso/0")
        except:
            torso_body_id = 1  # 如果找不到则使用默认ID
        
        print("✅ 可视化已启动")
        print("   机器人正在运动...")
        print("   按 ESC 或关闭窗口退出\n")
        
        # 运行仿真循环
        import time
        frame = 0
        try:
            while True:
                sim.step()
                
                # 每帧更新摄像头焦点以跟踪机器人躯干
                # 这样机器人运动时视角会自动跟随
                if torso_body_id >= 0 and torso_body_id < sim.model.nbody:
                    torso_pos = sim.data.body_xpos[torso_body_id]
                    # 保持摄像头距离和角度，但改变焦点跟随机器人
                    viewer.cam.lookat[:] = [torso_pos[0], torso_pos[1], torso_pos[2] * 0.7]
                
                viewer.render()
                frame += 1
                if frame % 1000 == 0:
                    print(f"   已运行 {frame} 帧...")
                time.sleep(0.001)
        except KeyboardInterrupt:
            pass
        
        print(f"\n✋ 已关闭（运行了 {frame} 帧）")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="MuJoCo实时可视化已生成的机器人",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  ./show_robot.sh 0          # 显示第0个机器人
  ./show_robot.sh 100        # 显示第100个机器人
  ./show_robot.sh 1158       # 显示最后一个机器人
        """
    )
    parser.add_argument(
        "index",
        type=int,
        help="机器人索引 (从0开始)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/lunar_jump",
        help="output文件夹路径 (默认: output/lunar_jump)"
    )
    
    args = parser.parse_args()
    
    success = show_robot(args.index, args.output_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
