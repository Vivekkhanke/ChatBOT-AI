import unittest

import config


class GeminiConfigRegressionTest(unittest.TestCase):

    def test_config_model_is_not_retired_alias(self):
        retired_aliases = {"gemini-2.0-flash", "gemini-2.5-flash"}
        self.assertNotIn(config.GEMINI_MODEL, retired_aliases)
        self.assertTrue(config.GEMINI_MODEL.strip())


if __name__ == "__main__":
    unittest.main()
