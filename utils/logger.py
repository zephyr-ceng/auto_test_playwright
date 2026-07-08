
import logging
from pathlib import Path
from typing import Optional


class Logger:
	"""简单的 Logger 封装（不限制文件大小）。

	初始化时传入文件名（不含路径或扩展名），会在项目 `logs/` 目录下创建对应的日志文件。

	示例：
		log = Logger("test")
		log.info("hello")

	参数：
		filename: 日志文件名（例如 'test' -> logs/test.log）
		level: 日志级别，默认 INFO
		log_dir: 可选，指定日志目录，默认在项目根的 `logs/`
	"""

	def __init__(
		self,
		filename: str,
		level: int = logging.INFO,
		log_dir: Optional[str] = None,
	):
		if not filename or not isinstance(filename, str):
			raise ValueError("filename must be a non-empty string")

		# 默认 logs 目录位于项目根（上两级： utils -> ui-automation-framework），并在其下使用 logs/log 子目录
		if log_dir:
			logs_path = Path(log_dir)
		else:
			# 使用默认日志目录：项目根下的 logs/log
			logs_path = Path(__file__).resolve().parents[1] / "logs" / "log"

		logs_path.mkdir(parents=True, exist_ok=True)
		log_file = logs_path / f"{filename}.log"

		self.__logger = logging.getLogger(filename)
		self.__logger.setLevel(level)

		# 避免重复添加 handler（当同名 logger 被多次初始化时）
		if not self.__logger.handlers:
			fmt = logging.Formatter(
				"%(asctime)s [%(levelname)s] %(name)s - %(message)s",
				datefmt="%Y-%m-%d %H:%M:%S",
			)

			# 使用不限制大小的 FileHandler（不做滚动）
			fh = logging.FileHandler(filename=str(log_file), encoding="utf-8")
			fh.setLevel(level)
			fh.setFormatter(fmt)

			self.__logger.addHandler(fh)

	def info(self, msg: str, *args, **kwargs) -> None:
		"""记录 info 级别日志"""
		self.__logger.info(msg, *args, **kwargs)

	def error(self, msg: str, *args, **kwargs) -> None:
		"""记录 error 级别日志"""
		self.__logger.error(msg, *args, **kwargs)

	def warning(self, msg: str, *args, **kwargs) -> None:
		"""记录 warning 级别日志"""
		self.__logger.warning(msg, *args, **kwargs)

	def debug(self, msg: str, *args, **kwargs) -> None:
		"""记录 debug 级别日志"""
		self.__logger.debug(msg, *args, **kwargs)

	def get_logger(self) -> logging.Logger:
		"""返回底层 logging.Logger 实例（如果需要高级操作）"""
		return self.__logger


if __name__ == "__main__":
	# 简单自测：在控制台和 logs/ 下写入几条日志
	test_logger = Logger("test_logger")
	test_logger.debug("This is a DEBUG message")
	test_logger.info("This is an INFO message")
	test_logger.warning("This is a WARNING message")
	test_logger.error("This is an ERROR message")

	# 打印实际写入的日志文件路径（在项目根的 logs/log 下）
	logs_file = Path(__file__).resolve().parents[1] / "logs" / "log" / "test_logger.log"
	print(f"Log file written to: {logs_file}")

