import random
import string
from datetime import datetime, timedelta
from typing import Optional


class RandomManager:
    __SURNAMES = [
        "赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈",
        "褚", "卫", "蒋", "沈", "韩", "杨", "朱", "秦", "尤", "许",
        "何", "吕", "施", "张", "孔", "曹", "严", "华", "金", "魏",
        "陶", "姜", "戚", "谢", "邹", "喻", "柏", "水", "窦", "章",
    ]

    __GIVEN_NAME_CHARS = list(
        "伟芳娜秀敏静丽强磊军洋勇艳杰娟涛明超秀英霞平刚桂英慧峰"
        "鹏飞鑫雪楠玲丹萍倩婷宇晨泽浩俊博子轩思涵雨桐梓涵一诺嘉怡"
    )

    __MOBILE_PREFIXES = [
        "130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
        "150", "151", "152", "153", "155", "156", "157", "158", "159",
        "166", "171", "172", "173", "175", "176", "177", "178",
        "180", "181", "182", "183", "184", "185", "186", "187", "188", "189",
        "191", "198", "199",
    ]

    @staticmethod
    def random_chinese_name(two_char_given_name_ratio: float = 0.8) -> str:
        surname = random.choice(RandomManager.__SURNAMES)
        given_len = 2 if random.random() < two_char_given_name_ratio else 1
        given = "".join(random.choice(RandomManager.__GIVEN_NAME_CHARS) for _ in range(given_len))
        return f"{surname}{given}"

    @staticmethod
    def random_common_chars(length: int, chars: Optional[str] = None) -> str:
        if length <= 0:
            raise ValueError("length must be > 0")
        charset = chars or (string.ascii_letters + string.digits)
        return "".join(random.choice(charset) for _ in range(length))

    @staticmethod
    def random_digits(length: int) -> str:
        if length <= 0:
            raise ValueError("length must be > 0")
        return "".join(random.choice(string.digits) for _ in range(length))

    @staticmethod
    def random_date(start: str = "1970-01-01", end: str = "2030-12-31") -> str:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        if start_dt > end_dt:
            raise ValueError("start must be <= end")
        days = (end_dt - start_dt).days
        picked = start_dt + timedelta(days=random.randint(0, days))
        return picked.strftime("%Y-%m-%d")

    @staticmethod
    def random_phone() -> str:
        prefix = random.choice(RandomManager.__MOBILE_PREFIXES)
        suffix = "".join(random.choice(string.digits) for _ in range(8))
        return f"{prefix}{suffix}"

    @staticmethod
    def random_gender(text: bool = True):
        value = random.choice(["male", "female"])
        if text:
            return "男" if value == "male" else "女"
        return value

    @staticmethod
    def random_gender_number():
        return random.randint(1, 2)


if __name__ == "__main__":
    random_manager = RandomManager()
    print(random_manager.random_gender())
    print(random_manager.random_phone())
    print(random_manager.random_date())
    print(random_manager.random_chinese_name())
    print(random_manager.random_common_chars(400))
