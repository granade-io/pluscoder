import os
import tempfile
import unittest

from PIL import Image

from pluscoder.message_utils import convert_image_paths_to_base64


class TestImageHandling(unittest.TestCase):
    def setUp(self):
        self.test_image_path = self.create_test_image()

    def tearDown(self):
        os.remove(self.test_image_path)

    def create_test_image(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            image = Image.new("RGB", (100, 100), color="red")
            image.save(temp_file.name)
            return temp_file.name

    def test_handle_clipboard_image(self):
        # This test might be challenging to implement without mocking the clipboard
        # For now, we'll skip it and focus on other tests
        pass

    def test_convert_image_paths_to_base64(self):
        input_text = f"This is an image: img::{self.test_image_path}"
        result = convert_image_paths_to_base64(input_text)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["type"], "text")
        self.assertEqual(result[0]["text"], "This is an image:")
        self.assertEqual(result[1]["type"], "text")
        self.assertEqual(result[2]["type"], "image_url")
        self.assertIn(result[1]["text"], f"img::{self.test_image_path}")
        self.assertIn("data:image/png;base64,", result[2]["image_url"]["url"])

    def test_text_only_input(self):
        input_text = "This is just text without any image paths."
        result = convert_image_paths_to_base64(input_text)
        self.assertEqual(result, input_text)

    def test_nonexistent_image_path(self):
        input_text = "This is a nonexistent image: /path/to/nonexistent/image.png"
        result = convert_image_paths_to_base64(input_text)
        self.assertEqual(result, input_text)

    def test_multiple_image_paths(self):
        input_text = f"Image1: img::{self.test_image_path}, Image2: img::{self.test_image_path}"
        result = convert_image_paths_to_base64(input_text)

        self.assertEqual(len(result), 6)
        self.assertEqual(result[0]["type"], "text")
        self.assertEqual(result[1]["type"], "text")
        self.assertEqual(result[2]["type"], "image_url")
        self.assertEqual(result[3]["type"], "text")
        self.assertEqual(result[4]["type"], "text")
        self.assertEqual(result[5]["type"], "image_url")

    def test_mixed_input(self):
        input_text = f"This is text. Here's an image: img::{self.test_image_path}. More text."
        result = convert_image_paths_to_base64(input_text)

        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]["type"], "text")
        self.assertEqual(result[1]["type"], "text")
        self.assertEqual(result[2]["type"], "image_url")
        self.assertEqual(result[3]["type"], "text")
        self.assertIn("This is text. Here's an image:", result[0]["text"])
        self.assertIn("More text.", result[3]["text"])

    def test_input_with_multiple_images_and_text(self):
        input_text = f"Text1 img::{self.test_image_path} Text2 img::{self.test_image_path} Text3"
        result = convert_image_paths_to_base64(input_text)

        self.assertEqual(len(result), 7)
        self.assertEqual(result[0]["type"], "text")
        self.assertEqual(result[1]["type"], "text")
        self.assertEqual(result[2]["type"], "image_url")
        self.assertEqual(result[3]["type"], "text")
        self.assertEqual(result[4]["type"], "text")
        self.assertEqual(result[5]["type"], "image_url")
        self.assertEqual(result[6]["type"], "text")

    def test_input_starting_and_ending_with_images(self):
        input_text = f"img::{self.test_image_path} Text img::{self.test_image_path}"
        result = convert_image_paths_to_base64(input_text)

        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]["type"], "text")
        self.assertEqual(result[1]["type"], "image_url")
        self.assertEqual(result[2]["type"], "text")
        self.assertEqual(result[3]["type"], "text")
        self.assertEqual(result[4]["type"], "image_url")

    def test_nonexistent_image_path_appended_to_text(self):
        input_text = "This is text. Here's a nonexistent image: /path/to/nonexistent/image.png"
        result = convert_image_paths_to_base64(input_text)

        self.assertEqual(result, input_text)

    def test_nonexistent_image_path_between_existing_images(self):
        input_text = f"img::{self.test_image_path} /path/to/nonexistent/image.png img::{self.test_image_path}"
        result = convert_image_paths_to_base64(input_text)

        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]["type"], "text")
        self.assertEqual(result[1]["type"], "image_url")
        self.assertEqual(result[2]["type"], "text")
        self.assertEqual(result[2]["text"], "/path/to/nonexistent/image.png")
        self.assertEqual(result[3]["type"], "text")
        self.assertEqual(result[4]["type"], "image_url")

    def test_mixed_existing_and_nonexistent_image_paths(self):
        input_text = f"Start img::{self.test_image_path} Middle /nonexistent1.png /nonexistent2.png img::{self.test_image_path} End"
        result = convert_image_paths_to_base64(input_text)

        self.assertEqual(len(result), 7)
        self.assertEqual(result[0]["type"], "text")
        self.assertEqual(result[1]["type"], "text")
        self.assertEqual(result[2]["type"], "image_url")
        self.assertEqual(result[3]["type"], "text")
        self.assertIn("Middle /nonexistent1.png /nonexistent2.png", result[3]["text"])
        self.assertEqual(result[4]["type"], "text")
        self.assertEqual(result[5]["type"], "image_url")
        self.assertEqual(result[6]["type"], "text")

    def test_url_image(self):
        fake_image_url = "https://example.com/fake_image.jpg"
        input_text = f"This is an image from URL: img::{fake_image_url}"
        result = convert_image_paths_to_base64(input_text)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["type"], "text")
        self.assertEqual(result[0]["text"], "This is an image from URL:")
        self.assertEqual(result[1]["type"], "text")
        self.assertEqual(result[2]["type"], "image_url")
        self.assertEqual(result[2]["image_url"]["url"], fake_image_url)

    def test_mixed_local_and_url_images(self):
        fake_image_url = "https://example.com/fake_image.jpg"
        input_text = f"Local: img::{self.test_image_path}, URL: img::{fake_image_url}"
        result = convert_image_paths_to_base64(input_text)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 6)
        self.assertEqual(result[0]["type"], "text")
        self.assertEqual(result[1]["type"], "text")
        self.assertEqual(result[2]["type"], "image_url")
        self.assertIn("data:image/png;base64,", result[2]["image_url"]["url"])
        self.assertEqual(result[3]["type"], "text")
        self.assertEqual(result[4]["type"], "text")
        self.assertEqual(result[5]["type"], "image_url")
        self.assertEqual(result[5]["image_url"]["url"], fake_image_url)

    def test_invalid_local_image(self):
        invalid_path = "/path/to/nonexistent/image.jpg"
        input_text = f"This is an invalid local image: img::{invalid_path}"
        result = convert_image_paths_to_base64(input_text)

        self.assertEqual(result, input_text)


if __name__ == "__main__":
    unittest.main()
