import unittest
import mestils
from time import time

class test_mestils(unittest.TestCase):
    def test_chunk_message(self):
        """Check that the input is correctly split up."""
        # test with 0 chants to see if an empty message is sent
        with self.assertRaises(ValueError):
            mestils.chunk_message("")
        # test with < 2k characters
        self.assertEqual(len(mestils.chunk_message(">={")), 1)
        # test with > 2k characters
        self.assertEqual(len(" ".join(["test"] * 401)), 2)
        # test performance
        start = time()
        self.cog._chant_inner()
        print(f"""DTWMChanWorship._test_inner finished in {time() - start} seconds
    with 5 million characters as inputs""")

if __name__ == '__main__':
    unittest.main()
