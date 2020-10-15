import unittest
import memtils


class test_memtils(unittest.TestCase):
    def test_NameParser(self):
        """Check that names are correctly parsed"""
        def func(name): return memtils.NameParser(
            name).parsed  # shorten the function name
        # test for the average use cases
        self.assertEqual(func("[DTWM] benmitchellmtbV5, monster energy"),
                         "benmitchellmtbV5")
        # the accents should be removed without destroying the characters
        self.assertEqual(func("ápplés; chööse"),
                         "apples; choose", "Failed to normalise accents")
        # spacer
        # spacer
        # spacer
        self.assertEqual(func("z̝̺͔̼̘̥̱̮̩̈́̉̑͛̎ͣ͒̊͒͛ͪ̈́͐̀͊ͯ̄͘͢͠͝͠a͐̀̃͂ͩ͏̶͓̼̥̖̦͕ͅlͫ̅͗̈́̄ͥ͜͡͏͙̗͉͇̩̲͉͖̞͓g̶͓̜̼̥͍͈̭͖̰̻̝̘͇̽͒̐̈ͬ̏̎̾̄̏̒́̈́ͥͥ̇͑͢͝͡͞ô̷̧̡̲͚̝̼̌̀͂͋̇̊͜ ̰̮̼͎̰͚̘̒͊͂ͮ͂͐̂̅͌ͬͨ̒͗ͥͥ̑̽̽̈́͠͡i̸̡̛̛̬̱͙̙̰̟͋̒̉͋̏̈̑ͯ͢s̵̎͌ͮ͋̅͂̋͋ͩ͊̎̍ͨ҉̧̭̘̣̯͕͇̬̲̮̥̘̞̤̭̘͖̟ͅ ̓͛͌͌͏̶̤͈̦͔͍̭͕͈̘̝͔̮̪a̙̼͓̤̺̺̬̱̟̓̎̄̕͞ṉ̸̸̸͔͈̤͎̻̯̻̝̖͖̭͚̈́̐̊͛̏̓́ͬͅn̸̷̶̢͖̲̣̮̾̔͋̏̋ͪ͌͊͠ỏ̴͉̱̜͔̦̳̟̺͎̞̤̻͈̼̞͚̦̄̌͐ͮ̓̒͛̕y̐̒ͫ͛̂̊̂͑͋̓̾͐ͥ̌ͭ́̕͏͏̪͖̝͈̰̝̻͈̥͖͍̫̳̯̱͈͕į̶͎̘͔̫̣̬͕̺͐ͦ̊̑͊ͦ͟͞ͅn̶̰̰̱̤̤͉̳̱̼̦̉ͮ̐͆ͫ̈̇͊̾̑̿͊̊̄̅ͨ̀g̪͓̗̜ͥ̋͋̓͐̒̏͋ͯͦ͂ͧ̃̋̂͑͊͢͜"),
                         # spacer
                         # spacer
                         "zalgo is annoying", "Failed to parse Zalgo")  # >={ people love their Zalgo. This should destroy it

        # edge cases
        with self.assertRaises(ValueError):
            func("")
        with self.assertRaises(TypeError):
            func(-3.56)
        # the whitespace should be stripped
        self.assertEqual(func("  .strip tease  "), ".strip tease")

        # test uncommonly-used features
        self.assertEqual(memtils.NameParser("[TAG] Tag test", check_tag=False).parsed,
                         "[TAG] Tag test", "Failed to keep the tag.")
        self.assertEqual(memtils.NameParser("I have / a title", check_titles=False).parsed,
                         "I have / a title", "Failed to keep the title.")
        self.assertEqual(memtils.NameParser("ápéúúíóá", remove_weird_chars=True).parsed,
                         "p", "Failed to destroy accented character.")
        self.assertEqual(func("I l!ke sym0ls >_<"), "I lke symb0ls",
                         "Failed to remove symbols and keep numbers.")
        self.assertEqual(memtils.NameParser("1 l1k3 numb3r5", check_numbers=True).parsed,
                         "lk numbr")
        self.assertEqual(memtils.NameParser("ayaYa", case=True).parsed,
                         "AYAYA", "Failed to raise case.")
        self.assertEqual(memtils.NameParser("loWErCASe", case=False).parsed,
                         "lowercase", "Failed to raise case.")


if __name__ == '__main__':
    unittest.main()
