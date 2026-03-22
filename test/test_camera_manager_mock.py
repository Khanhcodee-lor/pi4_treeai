import time
import unittest

import numpy as np

from src.camera.camera_manager import CameraManager


class FakePicamera2:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.config = None
        self.frame_counter = 0

    def create_video_configuration(self, main):
        return {"main": main}

    def configure(self, config):
        self.config = config

    def start(self):
        self.started = True

    def capture_array(self):
        self.frame_counter += 1
        value = self.frame_counter % 255
        return np.full((48, 64, 3), value, dtype=np.uint8)

    def stop(self):
        self.stopped = True


class CameraManagerTest(unittest.TestCase):
    def test_camera_manager_works_with_injected_camera(self):
        camera = CameraManager(width=64, height=48, camera_factory=FakePicamera2)

        try:
            deadline = time.time() + 1.0
            frame = None
            while time.time() < deadline:
                frame = camera.get_frame()
                if frame is not None:
                    break
                time.sleep(0.02)

            self.assertIsNotNone(frame)
            self.assertEqual(frame.shape, (48, 64, 3))
            self.assertTrue(camera.picam2.started)
            self.assertEqual(
                camera.picam2.config,
                {"main": {"size": (64, 48), "format": "BGR888"}},
            )
        finally:
            camera.stop()

        self.assertTrue(camera.picam2.stopped)
        self.assertFalse(camera.running)

    def test_invalid_backend_raises_error(self):
        with self.assertRaises(ValueError):
            CameraManager(backend="invalid-backend", camera_factory=None)


if __name__ == "__main__":
    unittest.main()
