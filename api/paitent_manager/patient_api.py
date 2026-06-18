from typing import Any, Dict, Optional
from requests import Response
from api.common.client import HTTPClient
from api.login_verification.login import Login


class PatientAPI:
    def __init__(self, base_url: str, ) -> None:
        self.base_url = base_url
        self.client = HTTPClient(self.base_url)
       