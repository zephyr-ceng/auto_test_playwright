import os
from pathlib import Path


class PathManager:
    def __init__(self, path_dir):
        self.all_subdirs = []
        self.path = self._is_path(path_dir)

    @staticmethod
    def _is_path(path_dir):
        _project_root = Path(__file__).resolve().parents[1]
        p = Path(path_dir)
        if p.is_absolute():
            return p
        else:
            return _project_root / p

    def get_subdirectory(self):
        if self.path.is_dir():
            for root, dirs, files in os.walk(self.path):
                for d in dirs:
                    # 获取完整路径
                    full_path = os.path.join(root, d)
                    self.all_subdirs.append(full_path)

            print(self.all_subdirs)
            return self.all_subdirs
        else:
            raise FileNotFoundError()


if __name__ == "__main__":
    path_manager = PathManager(f"data/dicom")
    path_manager.get_subdirectory()
