import shutil
import subprocess
import sys
from pathlib import Path


def run():
    # 1. 路径设置
    project_root = Path(__file__).resolve().parent
    base_reports = project_root / "reports"
    results_dir = base_reports / "results"  # Allure 原始结果目录
    html_out = base_reports / "html"  # Allure HTML 报告目录

    # 每次运行前清理旧的结果，避免历史测试混入本次报告
    if results_dir.exists():
        print(f"--- Step 0: 清理旧的 Allure 原始结果 {results_dir} ---")
        shutil.rmtree(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    # 2. 运行 Pytest 并输出 Allure 原始数据
    print(f"--- Step 1: 运行 Pytest，结果输出到 {results_dir} ---")
    ret = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--alluredir", str(results_dir)]
    )

    # 允许测试失败(returncode=1)，但其他错误直接退出
    if ret.returncode > 1:
        print(f"Pytest 运行异常，退出码: {ret.returncode}")
        sys.exit(ret.returncode)

    # 3. 清理旧的 HTML 报告
    if html_out.exists():
        print(f"--- Step 2: 清理旧的 HTML 报告 {html_out} ---")
        shutil.rmtree(html_out)

    # 4. 生成 Allure HTML 报告
    print("--- Step 3: 生成 Allure HTML 报告 ---")
    try:
        cmd = ["allure", "generate", str(results_dir), "-o", str(html_out)]
        subprocess.run(cmd, check=True, shell=(sys.platform == "win32"))

        print("-" * 30)
        print("报告生成成功")
        print(f"原始数据: {results_dir}")
        print(f"HTML 报告: {html_out}")
        print("-" * 30)
    except FileNotFoundError:
        print("错误: 未在系统 PATH 中找到 allure 命令行工具。")
    except subprocess.CalledProcessError as e:
        print(f"Allure 生成失败，退出码: {e.returncode}")


if __name__ == "__main__":
    run()
