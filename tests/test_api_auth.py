import unittest
from fastapi.testclient import TestClient
from web_app import app

class TestWebAuthAndAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["database"]["connected"])
        print("Health check response:", data)

    def test_guest_mode_works(self):
        # Guest request without auth token
        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_guest"])
        self.assertFalse(data["authenticated"])

    def test_register_and_login_flow(self):
        import uuid
        uid = str(uuid.uuid4())[:6]
        username = f"user_{uid}"
        email = f"user_{uid}@example.com"
        password = "strongpassword123"

        # 1. Register
        reg_res = self.client.post("/api/auth/register", json={
            "username": username,
            "email": email,
            "password": password,
            "name": f"User {uid}"
        })
        self.assertEqual(reg_res.status_code, 200)
        reg_data = reg_res.json()
        self.assertTrue(reg_data["success"])
        token = reg_data["token"]
        self.assertIsNotNone(token)

        # 2. Authenticated /me request
        headers = {"Authorization": f"Bearer {token}"}
        me_res = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.json()
        self.assertTrue(me_data["authenticated"])
        self.assertEqual(me_data["user"]["username"], username)

        # 3. Save a workout log as this user
        log_res = self.client.post("/api/session/save_log", headers=headers, json={
            "routine_id": "routine_full_body_ignition",
            "routine_title": "Full Body Ignition",
            "duration_spent_seconds": 450,
            "total_routine_duration_seconds": 450,
            "calories_burned": 52.0,
            "completed_steps_count": 8,
            "total_steps_count": 8,
            "status": "COMPLETED"
        })
        self.assertEqual(log_res.status_code, 200)

        # 4. Verify history belongs to this user
        hist_res = self.client.get("/api/history", headers=headers)
        self.assertEqual(hist_res.status_code, 200)
        hist_data = hist_res.json()
        self.assertGreaterEqual(len(hist_data), 1)
        self.assertEqual(hist_data[0]["routine_id"], "routine_full_body_ignition")

        # 5. Login
        login_res = self.client.post("/api/auth/login", json={
            "identifier": email,
            "password": password
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(login_res.json()["success"])

if __name__ == '__main__':
    unittest.main()

