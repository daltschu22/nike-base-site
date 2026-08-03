import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from main import require_admin


class AdminAuthTests(unittest.TestCase):
    @patch.dict(os.environ, {"ADMIN_API_TOKEN": "configured-secret"})
    def test_accepts_matching_bearer_token(self) -> None:
        self.assertIsNone(require_admin("Bearer configured-secret"))

    @patch.dict(os.environ, {"ADMIN_API_TOKEN": "configured-secret"})
    def test_rejects_invalid_credentials(self) -> None:
        invalid_values = [
            None,
            "",
            "configured-secret",
            "Basic configured-secret",
            "Bearer wrong-secret",
        ]

        for authorization in invalid_values:
            with self.subTest(authorization=authorization):
                with self.assertRaises(HTTPException) as raised:
                    require_admin(authorization)

                self.assertEqual(raised.exception.status_code, 401)
                self.assertEqual(
                    raised.exception.headers,
                    {"WWW-Authenticate": "Bearer"},
                )

    @patch.dict(os.environ, {}, clear=True)
    def test_fails_closed_without_configured_token(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            require_admin(None)

        self.assertEqual(raised.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
