import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Sequence
from utils.random_manager import RandomManager


class CSVManager:
    """CSV 管理器（对外仅建议使用 read_csv / append_row）。"""

    def __init__(self, csv_file: str, logger=None):
        """
        初始化 CSV 管理器。

        参数:
            csv_file: CSV 文件名或绝对路径。相对路径默认写入 data/test_data。
            logger: 可选日志对象。
        """
        self.logger = logger
        self.csv_file = self.__resolve_csv_path(csv_file)
        # 关键步骤：确保目录存在，避免写入时报错
        self.csv_file.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def __resolve_csv_path(csv_file: str) -> Path:
        """解析 CSV 路径；相对路径默认挂到 data/test_data 目录。"""
        csv_path = Path(csv_file)
        if csv_path.is_absolute():
            return csv_path

        project_root = Path(__file__).resolve().parents[1]
        test_data_dir = project_root / "data" / "test_data"
        return test_data_dir / csv_path

    def __read_header(self, encoding: str = "utf-8-sig") -> List[str]:
        """读取表头（内部方法）。"""
        if not self.csv_file.exists() or self.csv_file.stat().st_size == 0:
            return []
        with self.csv_file.open("r", newline="", encoding=encoding) as f:
            reader = csv.reader(f)
            return next(reader, [])

    def __append_values_row(self, values: Sequence[object], fieldnames: Sequence[str], encoding: str = "utf-8-sig") -> str:
        """按“值列表”追加一行（内部方法）。"""
        if len(values) != len(fieldnames):
            raise ValueError("values length must match fieldnames length")

        file_is_empty = (not self.csv_file.exists()) or self.csv_file.stat().st_size == 0
        with self.csv_file.open("a", newline="", encoding=encoding) as f:
            writer = csv.writer(f)
            # 关键步骤：仅首次写入时写表头，避免每次重复写字段名
            if file_is_empty:
                writer.writerow(fieldnames)
            writer.writerow(values)

        if self.logger:
            self.logger.info(f"Appended 1 row to csv: {self.csv_file}")
        return os.fspath(self.csv_file)

    def append_row(self,values: Sequence[object],fieldnames: Optional[Sequence[str]] = None,encoding: str = "utf-8-sig") -> str:
        """
        追加一行数据（对外写接口）。

        用法:
            第一次写入：append_row(values=[...], fieldnames=[...])
            后续写入： append_row(values=[...])  # 自动读取已有表头
        """
        if fieldnames is None:
            fieldnames = self.__read_header(encoding=encoding)
        if not fieldnames:
            raise ValueError("fieldnames are required for first write")
        return self.__append_values_row(values=values, fieldnames=fieldnames, encoding=encoding)

    def read_csv(self, encoding: str = "utf-8-sig") -> List[Dict[str, str]]:
        """
        读取 CSV，返回字典列表。

        返回示例:
            [{"patients_name": "Tom", "age": "18"}]
        """
        if not self.csv_file.exists():
            if self.logger:
                self.logger.warning(f"CSV file does not exist: {self.csv_file}")
            return []

        with self.csv_file.open("r", newline="", encoding=encoding) as f:
            rows = list(csv.DictReader(f))

        if self.logger:
            self.logger.info(f"Read {len(rows)} rows from csv: {self.csv_file}")
        return rows


if __name__ == "__main__":
    # manager = CSVManager("login_test_data.csv")
    # manager.append_row(
    #     values=[1,False,'demo','123','该账号未注册，请联系管理员'],
    #     fieldnames=['序号','是否有效','账号','密码','预期结果'])
    # data = [
    #     [2,False,'','123','请输入用户名!'],
    #     [3,False,'demo','','请输入密码！'],
    #     [4,False,'','',"请输入用户名!;请输入密码!"]
    # ]
    # for row in data:
    #     manager.append_row(row)
    csv_manager = CSVManager('patients_test_date.csv')
    random_manager = RandomManager()
    csv_manager.append_row(
        values=[1, False, '', '', '', '', '', '请填写患者姓名'],
        fieldnames=['序号', '是否有效', '姓名', '生日', '电话', '性别', '备注', '预期结果'])
    data = [
        [2, False, '这是一个超过十字符的文本', '', '', '', '', '姓名最多输入10个字符'],
        [3, False, random_manager.random_chinese_name(), '', random_manager.random_common_chars(3), '', '',
         '手机号格式错误！'],
        [5, False, random_manager.random_chinese_name(), '', random_manager.random_digits(10), '', '',
         '手机号格式错误！'],
        [6, False, random_manager.random_chinese_name(), '', random_manager.random_digits(12), '', '',
         '手机号格式错误！'],
        [6, False, random_manager.random_chinese_name(), '', random_manager.random_phone(), '',
         random_manager.random_common_chars(151), '备注最多150字'],
        # [6, True, random_manager.random_chinese_name(), '', random_manager.random_phone(), '', random_manager.random_common_chars(20), '创建成功'],
    ]
    for row in data:
        csv_manager.append_row(row)

    for case in csv_manager.read_csv():
        print(case)