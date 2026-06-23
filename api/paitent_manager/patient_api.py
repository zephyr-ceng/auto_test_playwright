from requests import Response

from api.common.client import HTTPClient
from api.login_verification.login import Login


class PatientAPIS(Login):
    def __init__(self, client: HTTPClient):
        super().__init__(client)

    def add_patient(
            self,
            name: str,
            gender: int | None = None,
            date_of_birth: int | None = None,
            identity_card: str | None = None,
            telephone: str | None = None,
            desc: str | None = None,
    ) -> Response:
        """Create a patient through gateway command 13002; only name is required."""
        payload = {"name": name}
        optional_fields = {
            "gender": gender,
            "dateOfBirth": date_of_birth,
            "identityCard": identity_card,
            "telephone": telephone,
            "desc": desc,
        }
        payload.update({key: value for key, value in optional_fields.items() if value is not None})
        return self.client.send_request("POST", command="13002", json=payload)
