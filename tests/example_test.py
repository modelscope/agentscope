# -*- coding: utf-8 -*-
""" Example for a unit test."""
import unittest


class ExampleTest(unittest.TestCase):
    """
    ExampleTest for a unit test.
    """

    def setUp(self) -> None:
        """Init for ExampleTest."""
        self.num_a = 1
        self.num_b = 0

    def test_dummy(self) -> None:
        """Dummy test."""
        self.assertGreater(self.num_a, self.num_b)


if __name__ == "__main__":
    unittest.main()
