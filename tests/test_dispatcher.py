import os
import unittest
from src.hermes.dispatcher import RepoGenome, DynamicSkillDispatcher

class TestDynamicDispatcher(unittest.TestCase):
    def setUp(self):
        self.sample_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "sample_forked_repo"))
        self.dispatcher = DynamicSkillDispatcher()

    def test_repo_genome_fingerprint(self):
        genome = RepoGenome(self.sample_repo)
        fp = genome.compute_fingerprint()

        self.assertTrue(fp["has_tests"])
        self.assertTrue(fp["has_web_routes"])
        self.assertIn("recursive-ci", fp["skill_affinities"])
        self.assertIn("sandbox-benchmark-runner", fp["skill_affinities"])
        self.assertIn("product-analytics-optimizer", fp["skill_affinities"])

    def test_micro_catalog_compactness(self):
        catalog = self.dispatcher.get_micro_catalog()
        self.assertEqual(len(catalog), 5)
        # Verify micro-catalog is lightweight (< 100 words total)
        total_words = sum(len(v.split()) for v in catalog.values())
        self.assertLess(total_words, 40)

    def test_event_driven_jit_resolution(self):
        affinities = ["recursive-ci", "sandbox-benchmark-runner", "telemetry-diagnostics"]

        # 1. Crash event should only resolve telemetry-diagnostics
        skills = self.dispatcher.resolve_active_skills("crash_alert", affinities)
        self.assertEqual(skills, ["telemetry-diagnostics"])

        # 2. Maintainer approval should only resolve sandbox-benchmark-runner
        skills = self.dispatcher.resolve_active_skills("maintainer_approved", affinities)
        self.assertEqual(skills, ["sandbox-benchmark-runner"])

        # 3. Webhook latency event for repo without web routes should resolve nothing
        skills = self.dispatcher.resolve_active_skills("p95_latency_spike", ["recursive-ci"])
        self.assertEqual(skills, [])

    def test_mount_and_eviction_lifecycle(self):
        content = self.dispatcher.mount_skill("recursive-ci")
        self.assertIsNotNone(content)
        self.assertIn("recursive-ci", self.dispatcher.mounted_skills)

        # Evict skill after execution
        self.dispatcher.evict_skill("recursive-ci")
        self.assertNotIn("recursive-ci", self.dispatcher.mounted_skills)
        self.assertEqual(len(self.dispatcher.mounted_skills), 0)

if __name__ == "__main__":
    unittest.main()
