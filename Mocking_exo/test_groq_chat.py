import sys
import unittest
from unittest.mock import Mock, patch

import groq_chat as gc


def fake_client(answer="4"):
    """A Mock shaped like the real Groq client: response.choices[0].message.content."""
    choice = Mock()
    choice.message.content = answer
    client = Mock()
    client.chat.completions.create.return_value = Mock(choices=[choice])
    return client


class AskGroqTest(unittest.TestCase):
    def test_returns_the_answer(self):
        self.assertEqual(gc.ask_groq("What is 2+2?", client=fake_client()), "4")

    def test_sends_the_right_request(self):
        client = fake_client()
        gc.ask_groq("What is 2+2?", client=client)
        client.chat.completions.create.assert_called_once_with(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "What is 2+2?"}],
            max_tokens=1024,
        )

    def test_empty_question_never_reaches_the_api(self):
        client = fake_client()
        with self.assertRaises(ValueError):
            gc.ask_groq("   ", client=client)
        client.chat.completions.create.assert_not_called()

    def test_api_down(self):
        client = Mock()
        client.chat.completions.create.side_effect = Exception("API down")
        with self.assertRaisesRegex(Exception, "API down"):
            gc.ask_groq("What is 2+2?", client=client)

    def test_default_client_is_replaced_with_patch(self):
        # No client passed: ask_groq builds Groq() itself, so we swap the whole package
        fake_groq = Mock()
        fake_groq.Groq.return_value = fake_client("Paris")
        with patch.dict(sys.modules, {"groq": fake_groq}):
            self.assertEqual(gc.ask_groq("Capital of France?"), "Paris")
        fake_groq.Groq.assert_called_once_with()


class RetryTest(unittest.TestCase):
    def test_succeeds_after_two_failures(self):
        client = fake_client()
        answer = client.chat.completions.create.return_value
        # side_effect as a list: one item per call, exceptions are raised
        client.chat.completions.create.side_effect = [TimeoutError("slow"), ConnectionError("down"), answer]
        self.assertEqual(gc.ask_with_retry("What is 2+2?", client), "4")
        self.assertEqual(client.chat.completions.create.call_count, 3)

    def test_gives_up_after_the_last_attempt(self):
        client = Mock()
        client.chat.completions.create.side_effect = ConnectionError("API down")
        with self.assertRaises(ConnectionError):
            gc.ask_with_retry("What is 2+2?", client, attempts=2)
        self.assertEqual(client.chat.completions.create.call_count, 2)

    def test_bad_question_is_not_retried(self):
        client = fake_client()
        with self.assertRaises(ValueError):
            gc.ask_with_retry("", client)
        client.chat.completions.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
