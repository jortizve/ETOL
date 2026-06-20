import unittest
from vitamin_model_checker.model_checker_interface.explicit.OL import TOL

class TOLTestCase(unittest.TestCase):
    def test_untimed(self):
        result = TOL.model_checking_new("{J1}G!a", './data/small_ol.txt')
        self.assertEqual(result['res'], "Result set: set()")

        result2 = TOL.model_checking_new(str("{J2}Xa"), './data/small_ol.txt')
        self.assertIn('s1', result2['res'])
        self.assertIn('s0', result2['res'])

    def test_small_tol(self):
        result = TOL.model_checking_new("{J101}F!b with x<2", './data/small_ol.txt')
        self.assertIn('s1', result['res'])
        self.assertNotIn('s0', result['res'])
        self.assertIn('s2', result['res'])

    def test_tol(self):
        result = TOL.model_checking_new("({J4}!r U a) with j<=5", "./data/TOL_model.txt")
        self.assertIn('s4', result['res'])
        self.assertIn('s0', result['res'])
        self.assertIn('s2', result['res'])
        self.assertIn('s5', result['res'])
        self.assertNotIn('s1', result['res'])
        self.assertNotIn('s3', result['res'])