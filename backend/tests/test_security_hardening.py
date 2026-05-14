import asyncio
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SEED_DEMO", "false")

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.dependencies import get_optional_user
from app.models.user import OTPVerification, Session as UserSession, User
from app.routers import resume as resume_router
from app.services.auth_service import AuthService


class FakeQuery:
    def __init__(self, result=None):
        self.result = result
        self.updated_with = None

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.result

    def update(self, values):
        self.updated_with = values
        return 1


class FakeDB:
    def __init__(self, query_map):
        self.query_map = query_map
        self.added = []
        self.commits = 0

    def query(self, model):
        return self.query_map[model]

    def add(self, item):
        self.added.append(item)

    def commit(self):
        self.commits += 1


class SecurityHardeningTests(unittest.TestCase):
    def test_password_reset_never_returns_otp(self):
        user = types.SimpleNamespace(id=7, email="owner@example.com")
        user_query = FakeQuery(user)
        otp_query = FakeQuery()
        db = FakeDB({
            User: user_query,
            OTPVerification: otp_query,
        })

        with patch("app.services.auth_service.generate_otp", return_value="123456"), patch(
            "app.services.auth_service.get_otp_expiry",
            return_value="2099-01-01T00:00:00Z",
        ):
            response = AuthService.request_password_reset(db, user.email)

        self.assertEqual(response, {"message": "If the email exists, an OTP has been sent."})
        self.assertNotIn("otp_code", response)
        self.assertEqual(otp_query.updated_with, {"used": True})
        self.assertEqual(len(db.added), 1)
        self.assertEqual(db.commits, 1)

    def test_optional_user_rejects_invalidated_sessions(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dead-session")
        user = types.SimpleNamespace(id=9, is_active=True)
        db = FakeDB({
            User: FakeQuery(user),
            UserSession: FakeQuery(None),
        })

        with patch("app.auth.dependencies.decode_access_token", return_value={"sub": "9"}):
            result = asyncio.run(get_optional_user(credentials, db))

        self.assertIsNone(result)

    def test_optional_user_accepts_active_session(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="live-session")
        user = types.SimpleNamespace(id=11, is_active=True)
        db = FakeDB({
            User: FakeQuery(user),
            UserSession: FakeQuery(types.SimpleNamespace(is_active=True)),
        })

        with patch("app.auth.dependencies.decode_access_token", return_value={"sub": "11"}):
            result = asyncio.run(get_optional_user(credentials, db))

        self.assertIs(result, user)

    def test_resume_file_helper_rejects_cross_user_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_upload_dir = resume_router.UPLOAD_DIR
            resume_router.UPLOAD_DIR = Path(tmpdir)
            try:
                owner_dir = resume_router.UPLOAD_DIR / "1"
                other_dir = resume_router.UPLOAD_DIR / "2"
                owner_dir.mkdir(parents=True)
                other_dir.mkdir(parents=True)
                good_file = owner_dir / "resume.txt"
                bad_file = other_dir / "resume.txt"
                good_file.write_text("ok", encoding="utf-8")
                bad_file.write_text("nope", encoding="utf-8")

                resolved = resume_router._resolve_user_file_path(str(good_file), user_id=1)
                self.assertEqual(resolved, good_file.resolve())

                with self.assertRaises(HTTPException):
                    resume_router._resolve_user_file_path(str(bad_file), user_id=1)
            finally:
                resume_router.UPLOAD_DIR = original_upload_dir

    def test_production_requires_strong_secret_key(self):
        code = (
            "import os, sys; "
            f"sys.path.insert(0, r'{BACKEND_ROOT}'); "
            "os.environ['DATABASE_URL']='postgresql://user:pass@localhost:5432/testdb'; "
            "os.environ['ENVIRONMENT']='production'; "
            "os.environ['SECRET_KEY']=''; "
            "import app.auth.utils"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY must be set", result.stderr)

    def test_production_app_disables_public_uploads_and_legacy_routes_by_default(self):
        code = (
            "import os, sys; "
            f"sys.path.insert(0, r'{BACKEND_ROOT}'); "
            "os.environ['DATABASE_URL']='postgresql://user:pass@localhost:5432/testdb'; "
            "os.environ['ENVIRONMENT']='production'; "
            "os.environ['SECRET_KEY']='x' * 64; "
            "os.environ.pop('ENABLE_LEGACY_COMPAT_ROUTES', None); "
            "import app.main as main; "
            "names = [getattr(route, 'name', '') for route in main.app.routes]; "
            "paths = [getattr(route, 'path', '') for route in main.app.routes if hasattr(route, 'path')]; "
            "assert 'uploads' not in names; "
            "assert '/api/logs' not in paths; "
            "print('ok')"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
