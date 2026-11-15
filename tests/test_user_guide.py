import unittest
from homeworkout.models import UserProfile
from homeworkout.service import WorkoutAppService
from fastapi.testclient import TestClient
from web_app import app

class TestUserGuide(unittest.TestCase):
    def setUp(self):
        self.service = WorkoutAppService()
        self.client = TestClient(app)

    def test_profile_user_guide_flag(self):
        # Default should be True
        profile = self.service.get_profile()
        self.assertTrue(profile.show_onboarding_guide)

        # Update to False
        updated = self.service.update_profile(show_onboarding_guide=False)
        self.assertFalse(updated.show_onboarding_guide)

        # Reload from storage
        reloaded = self.service.get_profile()
        self.assertFalse(reloaded.show_onboarding_guide)

        # Restore to True
        self.service.update_profile(show_onboarding_guide=True)
        self.assertTrue(self.service.get_profile().show_onboarding_guide)

    def test_api_profile_user_guide_update(self):
        # Test updating via /api/profile
        res = self.client.post("/api/profile", json={"show_onboarding_guide": False})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["profile"]["show_onboarding_guide"])

        # Reset back to True
        res = self.client.post("/api/profile", json={"show_onboarding_guide": True})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["profile"]["show_onboarding_guide"])

    def test_guide_images_accessible(self):
        # Check static serving of panduan1 and panduan2
        res1 = self.client.get("/workout_data/images/panduan1.png")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.headers["content-type"], "image/png")

        res2 = self.client.get("/workout_data/images/panduan2.png")
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.headers["content-type"], "image/png")

if __name__ == '__main__':
    unittest.main()

