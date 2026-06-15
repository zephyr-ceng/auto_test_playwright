import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def _pytest_targets(suite: str) -> list[str]:
    if suite == "ui":
        return ["tests/ui", "-m", "not api"]
    if suite == "api":
        return ["tests/api", "-m", "api and not destructive_api and not external_api"]
    if suite == "all":
        return [
            "tests/ui",
            "tests/api",
            "-m",
            "not destructive_api and not external_api",
        ]
    raise ValueError(f"Unknown suite: {suite}")


def run() -> None:
    parser = argparse.ArgumentParser(description="Run UI/API pytest suites and generate Allure reports.")
    parser.add_argument(
        "--suite",
        choices=["ui", "api", "all"],
        default="ui",
        help="Suite to run. Default keeps the historical behavior: UI only.",
    )
    parser.add_argument(
        "--no-allure-html",
        action="store_true",
        help="Run pytest only and skip allure generate.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    base_reports = project_root / "reports"
    results_dir = base_reports / "results"
    html_out = base_reports / "html"

    if results_dir.exists():
        print(f"--- Step 0: clean old Allure results {results_dir} ---")
        shutil.rmtree(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        *_pytest_targets(args.suite),
        "--alluredir",
        str(results_dir),
    ]
    print(f"--- Step 1: run pytest suite={args.suite} ---")
    print(" ".join(pytest_cmd))
    ret = subprocess.run(pytest_cmd)

    if ret.returncode == 5:
        print("No tests matched the selected suite/markers.")
    elif ret.returncode > 1:
        print(f"Pytest execution error, exit code: {ret.returncode}")
        sys.exit(ret.returncode)

    if args.no_allure_html:
        return

    if html_out.exists():
        print(f"--- Step 2: clean old Allure HTML {html_out} ---")
        shutil.rmtree(html_out)

    print("--- Step 3: generate Allure HTML ---")
    try:
        cmd = ["allure", "generate", str(results_dir), "-o", str(html_out)]
        subprocess.run(cmd, check=True, shell=(sys.platform == "win32"))
        print("-" * 30)
        print("Allure report generated")
        print(f"Results: {results_dir}")
        print(f"HTML: {html_out}")
        print("-" * 30)
    except FileNotFoundError:
        print("Error: allure command line tool was not found in PATH.")
    except subprocess.CalledProcessError as exc:
        print(f"Allure generation failed, exit code: {exc.returncode}")


if __name__ == "__main__":
    run()
