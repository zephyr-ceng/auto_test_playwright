import csv
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "data" / "rule" / "new_patient_manage"
UI_TEST_ROOT = PROJECT_ROOT / "tests" / "ui"

UI_CASE_OUTPUT_CSV = SOURCE_ROOT / "new_patient_manage_ui_automation_cases.csv"

GENERATED_OUTPUTS = {
    "new_patient_manage_case_summary.csv",
    UI_CASE_OUTPUT_CSV.name,
}

BASE_COLUMNS = [
    "功能区分",
    "来源CSV",
    "是否已生成自动化case",
    "自动化case匹配依据",
]

ROOT_FILE_FEATURES = {
    "create_patient_form_case.csv": "新建患者表单",
}

# Patient-management UI tests that currently exist but do not carry a rule case
# id in the source. These rows are still useful for coverage comparison, but the
# match should remain explicit and auditable.
TITLE_AUTOMATION_MAP = {
    "删除患者二次确认": "test_delete_patient_after_create",
    "确认删除患者成功后刷新列表": "test_delete_patient_after_create",
    "切换每页条数": "test_count_patients",
    "按患者姓名点击查询": "test_select_patients",
    "点击详情进入患者工作区": "test_select_design",
}

CASE_ID_RE = re.compile(r"(?:UI-[A-Z]+|SPEC-DIFF)-[0-9]{3}")


def get_feature_name(path: Path) -> str:
    if path.parent == SOURCE_ROOT:
        return ROOT_FILE_FEATURES.get(path.name, path.stem)
    return path.parent.name


def collect_current_case_ids() -> set[str]:
    case_ids: set[str] = set()
    for path in UI_TEST_ROOT.glob("test_*.py"):
        text = path.read_text(encoding="utf-8")
        case_ids.update(CASE_ID_RE.findall(text))
    return case_ids


def collect_source_csvs() -> list[Path]:
    return sorted(
        path
        for path in SOURCE_ROOT.rglob("*.csv")
        if path.name not in GENERATED_OUTPUTS
    )


def build_ui_case_rows() -> tuple[list[str], list[dict[str, str]]]:
    current_case_ids = collect_current_case_ids()
    source_headers: list[str] = []
    ui_case_rows: list[dict[str, str]] = []

    for path in collect_source_csvs():
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                for field in reader.fieldnames:
                    if field not in source_headers:
                        source_headers.append(field)

            feature_name = get_feature_name(path)
            source_csv = path.relative_to(SOURCE_ROOT).as_posix()

            for row in reader:
                if row.get("自动化类型") != "UI自动化":
                    continue

                case_id = row.get("用例编号", "")
                title = row.get("用例标题", "")
                matched_by = ""

                if case_id in current_case_ids:
                    matched_by = f"用例编号精确命中：{case_id}"
                elif title in TITLE_AUTOMATION_MAP:
                    matched_by = f"标题/行为匹配：{TITLE_AUTOMATION_MAP[title]}"

                ui_case_rows.append(
                    {
                        "功能区分": feature_name,
                        "来源CSV": source_csv,
                        **row,
                        "是否已生成自动化case": "是" if matched_by else "否",
                        "自动化case匹配依据": matched_by,
                    }
                )

    return BASE_COLUMNS[:2] + source_headers + BASE_COLUMNS[2:], ui_case_rows


def main() -> None:
    fieldnames, rows = build_ui_case_rows()
    with UI_CASE_OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    automated_count = sum(1 for row in rows if row["是否已生成自动化case"] == "是")
    print(f"wrote: {UI_CASE_OUTPUT_CSV}")
    print(f"ui automation rows: {len(rows)}")
    print(f"generated automation rows: {automated_count}")


if __name__ == "__main__":
    main()
