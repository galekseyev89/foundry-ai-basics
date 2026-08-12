import unittest
from unittest.mock import patch

from foundry_ai_basics.display import read_user_message


class DisplayTests(unittest.TestCase):
    def test_read_user_message_returns_trimmed_keyboard_input(self):
        with patch("builtins.input", return_value="  Hello from the keyboard  "):
            message = read_user_message()

        self.assertEqual(message, "Hello from the keyboard")


if __name__ == "__main__":
    unittest.main()
