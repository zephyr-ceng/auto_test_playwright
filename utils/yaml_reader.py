from pathlib import Path
import re
from typing import Any, Dict, Optional
import yaml
from pygments import style


class YamlManager:
    """YAML 工具类：读取/写入 YAML，并输出日志。"""

    def __init__(self, log):
        self.__logger = log
        self.__project_root = Path(__file__).resolve().parents[1]

    def __resolve_path(self, file_path: str) -> Path:
        """
        解析路径：
        - 绝对路径：直接使用
        - 相对路径：按项目根目录解析
        """
        p = Path(file_path)
        if p.is_absolute():
            return p
        return self.__project_root / p

    def read(self, file_path: str) -> Optional[Any]:
        """读取 YAML 文件并返回解析结果，失败返回 None。"""
        p = self.__resolve_path(file_path)
        try:
            if not p.exists():
                self.__logger.error(f"YAML file not found: {p}")
                return None

            with p.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # self._logger.info(f"Read YAML file: {p}")
            return data
        except Exception as e:
            self.__logger.error(f"Failed to read YAML file {p}: {e}")
            return None

    def write(self, file_path: str, data: Any) -> bool:
        """写入 YAML 文件，成功返回 True，失败返回 False。"""
        p = self.__resolve_path(file_path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8") as f:
                # --- 核心修改：创建一个临时的 Dumper 行为描述器 ---
                class QuotedDumper(yaml.SafeDumper):
                    def represent_data(self, node_data):
                        # 如果检测到是字符串类型，强制指定其展示样式为双引号
                        if isinstance(node_data, str):
                            return self.represent_scalar('tag:yaml.org,2002:str', node_data, style='"')
                        return super().represent_data(node_data)

                # -----------------------------------------------

                # 替换默认的 Dumper
                yaml.dump(data, f, Dumper=QuotedDumper, allow_unicode=True)
            self.__logger.info(f"Wrote YAML file: {p}")
            return True
        except Exception as e:
            self.__logger.error(f"Failed to write YAML file {p}: {e}")
            return False

    def update(self, file_path: str, updates: Dict[str, Any]) -> bool:
        """Update top-level YAML keys while keeping existing file format as-is."""
        if not isinstance(updates, dict):
            self.__logger.error("updates must be a dict")
            return False

        p = self.__resolve_path(file_path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.exists():
                raw = p.read_text(encoding="utf-8")
            else:
                raw = ""

            lines = raw.splitlines(keepends=True)

            def _inline_yaml(value: Any) -> str:
                style = '"' if isinstance(value, str) else None
                dumped = yaml.safe_dump(
                    value,
                    allow_unicode=True,
                    default_flow_style=True,
                    sort_keys=False,
                    width=10_000_000,
                    default_style=style
                ).strip()
                if dumped.endswith("\n..."):
                    dumped = dumped[:-4].strip()
                if dumped == "...":
                    dumped = "null"
                return dumped or "null"

            def _replace_or_append(key: str, value: Any) -> None:
                nonlocal lines
                key_re = re.compile(rf"^([ \t]*){re.escape(str(key))}\s*:")
                key_str = str(key)
                new_line = f"{key_str}: {_inline_yaml(value)}\n"

                match_idx = None
                for idx, line in enumerate(lines):
                    if key_re.match(line):
                        match_idx = idx
                        break

                if match_idx is None:
                    if lines and not lines[-1].endswith("\n"):
                        lines[-1] = lines[-1] + "\n"
                    lines.append(new_line)
                    return

                end_idx = match_idx + 1
                while end_idx < len(lines):
                    cur = lines[end_idx]
                    if cur.startswith(" ") or cur.startswith("\t") or cur.strip() == "":
                        end_idx += 1
                        continue
                    break
                lines[match_idx:end_idx] = [new_line]

            for k, v in updates.items():
                _replace_or_append(k, v)

            p.write_text("".join(lines), encoding="utf-8")
            self.__logger.info(f"Updated YAML file (in-place): {p}")
            return True
        except Exception as e:
            self.__logger.error(f"Failed to update YAML file {p}: {e}")
            return False


if __name__ == "__main__":
    from utils.logger import Logger

    logger = Logger("yaml_manager")
    file_path = "data/design_page.yaml"
    data = YamlManager(logger).read(file_path)
    print(data.get("url"))
