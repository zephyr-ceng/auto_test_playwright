import subprocess
import sys
import shutil
from pathlib import Path

def run():
    # 1. 路径设置
    project_root = Path(__file__).resolve().parent
    base_reports = project_root / "reports"
    results_dir = base_reports / "results"  # 原始数据存放地
    html_out = base_reports / "html"        # HTML 报告存放地

    # 确保目录存在
    results_dir.mkdir(parents=True, exist_ok=True)

    # 2. 运行 Pytest 收集结果
    print(f"--- 步骤 1: 运行 Pytest 并保存结果到 {results_dir} ---")
    # 使用 --alluredir 指定结果存放路径
    ret = subprocess.run([sys.executable, "-m", "pytest", "-q", "--alluredir", str(results_dir)])
    
    # 允许测试失败 (ret.returncode == 1)，但如果是其他错误则退出
    if ret.returncode > 1:
        print(f"Pytest 运行异常，退出码: {ret.returncode}")
        sys.exit(ret.returncode)

    # 3. 清理旧的 HTML 报告 (替代 --clean 参数以提高兼容性)
    if html_out.exists():
        print(f"--- 步骤 2: 清理旧报告 {html_out} ---")
        shutil.rmtree(html_out)

    # 4. 使用 Allure 3 生成报告
    print(f"--- 步骤 3: 生成 Allure HTML 报告 ---")
    try:
        # 重点：直接传递结果目录作为参数，-o 指定输出路径
        # 在 Windows 上建议设置 shell=True 
        cmd = ["allure", "generate", str(results_dir), "-o", str(html_out)]
        
        subprocess.run(cmd, check=True, shell=(sys.platform == "win32"))
        
        print("-" * 30)
        print(f"✅ 报告生成成功！")
        print(f"原始数据: {results_dir}")
        print(f"HTML 报告: {html_out}")
        print("-" * 30)
        
    except FileNotFoundError:
        print("❌ 错误: 未在系统变量中找到 allure 命令行工具。")
    except subprocess.CalledProcessError as e:
        print(f"❌ Allure 生成失败。错误代码: {e.returncode}")

if __name__ == "__main__":
    run()