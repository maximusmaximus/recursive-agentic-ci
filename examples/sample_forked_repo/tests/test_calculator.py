import unittest
try:
    from calculator import Calculator
except ImportError:
    from examples.sample_forked_repo.calculator import Calculator

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_addition(self):
        self.assertEqual(self.calc.compute("add", 2, 3), 5)

    def test_subtraction(self):
        self.assertEqual(self.calc.compute("sub", 10, 4), 6)

    def test_multiplication(self):
        self.assertEqual(self.calc.compute("mul", 3, 7), 21)

    def test_prime_detection(self):
        self.assertTrue(self.calc.is_prime(13))
        self.assertFalse(self.calc.is_prime(4))
        self.assertFalse(self.calc.is_prime(1))

if __name__ == "__main__":
    unittest.main()
