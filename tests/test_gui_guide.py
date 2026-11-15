import unittest
import os
import customtkinter as ctk

class TestGuiGuideModal(unittest.TestCase):
    def test_modal_import_and_structure(self):
        # Verify gui_app can be imported and UserGuideModal exists
        import gui_app
        self.assertTrue(hasattr(gui_app, 'UserGuideModal'))
        self.assertTrue(hasattr(gui_app.FitPulseApp, 'show_user_guide_modal'))

if __name__ == '__main__':
    unittest.main()

