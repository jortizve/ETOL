import unittest

from vitamin_model_checker.model_checker_interface.explicit.CTL import TCTL

class TCTLTestCase(unittest.TestCase):
    def test_4_pipeline_ag(self):
        result = TCTL.timed_model_checking("AG l3 implies z<12", './data/4-pipeline.txt')
        self.assertNotIn('s3', result['res'])
        self.assertIn('s0', result['res'])
        self.assertIn('s1', result['res'])
        self.assertIn('s2', result['res'])

        result = TCTL.timed_model_checking("AG l3 implies z>=12", './data/4-pipeline.txt')
        self.assertIn('s3', result['res'])

    def test_4_pipeline_ef(self):
        result = TCTL.timed_model_checking("EF l0 and z>=16", './data/4-pipeline.txt')
        self.assertIn('s3', result['res'])
        self.assertIn('s0', result['res'])
        self.assertIn('s1', result['res'])
        self.assertIn('s2', result['res'])