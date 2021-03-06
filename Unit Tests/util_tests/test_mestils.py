import unittest
from Utils import mestils
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
        multi_message_str = " ".join(["test"] * 401)
        self.assertEqual(
            len(mestils.chunk_message(multi_message_str)), 2)
        # test performance
        start = time()
        mestils.chunk_message(" ".join(["test"] * 1000000))
        print(f"""DTWMChanWorship._test_inner finished in {time() - start} seconds
    with 5 million characters as inputs""")

    def test_list_join(self):
        """Check that it joins the items into a grammatical list"""
        self.assertEqual(mestils.list_join(
            (
                "one", "two", "three", "four"
            )
        ), "one, two, three and four")
        self.assertEqual(mestils.list_join(
            ("five", "six", "seven", "eight"), "or"
        ), "five, six, seven or eight")

        # test that it only accepts strings within the input
        with self.assertRaises(TypeError):
            mestils.list_join(
                (
                    ("this", "should"),
                    ("fail",)
                )
            )

    def test_search_word(self):
        """Make sure that the regex can detect whole words
        """
        msg = "The quick brown fox jumps over the lazy dog"
        self.assertTrue(mestils.search_word(msg, "quick"))
        self.assertTrue(mestils.search_word(msg, "BroWn"))
        self.assertTrue(mestils.search_word(msg.upper(), "fox"))
        self.assertFalse(mestils.search_word(msg, "bfox"))
        self.assertFalse(mestils.search_word(msg, "notthere"))
        with self.assertRaises(TypeError):
            mestils.search_word(msg, 10)

    def test_get_instagram_links(self):
        """Ensure that Instagram links can be extracted from messages.
        Expects that at least 1 string is returned.
        Check that all links are valid before debugging.
        """
        f = mestils.get_instagram_links  # the name is too long
        test_links = [
            "https://www.instagram.com/p/CEpg-X_gnoQ/?igshid=1wdpesq9044td",
            "https://www.instagram.com/p/CErxme8jDsH/?igshid=accz6fofjvvt",
            "https://www.instagram.com/p/CEsBXWzD_3V/?igshid=5n13fjr0ivxm",
            "https://www.instagram.com/p/CEsFNDLpk4Y/?igshid=of1burcypbe9",
            "https://www.instagram.com/p/CErzRpXDzOi/?igshid=wupmq9npqew5",
        ]
        # private links should still be returned
        private_link = "https://www.instagram.com/p/CEX3iwulAuDq5RFjcI497Hn-vJR27kekHNWASY0/?igshid=pe4425ayywlk"
        self.assertTrue(f(test_links[0]))  # test with no extra words
        self.assertTrue(f(f"Here is a link: {test_links[1]}"))
        self.assertTrue(
            f(f"Here is a link: {test_links[2]} and another {test_links[3]}"))
        self.assertTrue(f(f"Word joined with link{test_links[4]}"))
        self.assertTrue(f(private_link), "Failed to extract private link.")

    def test_is_private(self):
        """Ensure that private links are correctly identified.
        Check that all links are valid before debugging."""
        public_links = [
            "https://www.instagram.com/p/CEpg-X_gnoQ/?igshid=1wdpesq9044td",
            "https://www.instagram.com/p/CErxme8jDsH/?igshid=accz6fofjvvt",
            "https://www.instagram.com/p/CEsBXWzD_3V/?igshid=5n13fjr0ivxm",
            "https://www.instagram.com/p/CEsFNDLpk4Y/?igshid=of1burcypbe9",
            "https://www.instagram.com/p/CErzRpXDzOi/?igshid=wupmq9npqew5",
        ]
        private_links = [
            "https://www.instagram.com/p/CEX3iwulAuDq5RFjcI497Hn-vJR27kekHNWASY0/?igshid=pe4425ayywlk",
            "https://www.instagram.com/p/CEsa5dsDv-BG5cmQQE7hDnVB-6RQsbjsmjA1Rw0/?igshid=s8ohcqjdx0dg",
        ]
        for link in public_links:
            self.assertFalse(mestils.is_private(
                link), "This is a public link.")
        for link in private_links:
            self.assertTrue(mestils.is_private(link), "This link is private.")

    def test_get_private_instagram_link(self):
        """Integration test for get_instagram_links and is_private"""
        msg = ("Public link: https://www.instagram.com/p/CEpg-X_gnoQ/?igshid=1wdpesq9044td\n"
               + "Private link: https://www.instagram.com/p/CEX3iwulAuDq5RFjcI497Hn-vJR27kekHNWASY0/?igshid=pe4425ayywlk\n"
               + "Public link 2: https://www.instagram.com/p/CErxme8jDsH/?igshid=accz6fofjvvt\n"
               + "Private link 2: https://www.instagram.com/p/CEsa5dsDv-BG5cmQQE7hDnVB-6RQsbjsmjA1Rw0/?igshid=s8ohcqjdx0dg\n")
        links = mestils.get_instagram_links(msg)
        self.assertEqual(list(map(mestils.is_private, links)),
                         [False,
                          True,
                          False,
                          True])

    def test_get_links(self):
        """Test that it retrieves all links in some text but doesn't return non-links."""
        test_string = '''Thing yes https://i.ytimg.com/an_webp/YYvHLGF8HSw/mqdefault_6s.webp?du=3000&sqp=CLCa1_sF&rs=AOn4CLDINW4tRLWunYLw9HiHgtlnmcimRg
https://www.youtube.com/watch?v=AYZOHt6kz6Y ayaya
Nice link bro https://images.ctfassets.net/hrltx12pl8hq/4f6DfV5DbqaQUSw0uo0mWi/ff068ff5fc855601751499d694c0111a/shutterstock_376532611.jpg?fit=fill&w=800&h=300  end
https://theindianrover.com/wp-content/uploads/2020/05/10-Top-Websites-for-awesome-free-and-royalty-free-photos-e1531386171536.jpg
https://images.ctfassets.net/hrltx12pl8hq/VZW7M82mrxByGHjvze4wu/216d9ff35b6980d850d108a50ae387bf/Carousel_01_FreeTrial.jpg?fit=fill&w=800&h=450
python.org
census.daybreakgames.com/get/ps2/item?name.en=PSA-02 Diamondback'''

        expected = ["https://i.ytimg.com/an_webp/YYvHLGF8HSw/mqdefault_6s.webp?du=3000&sqp=CLCa1_sF&rs=AOn4CLDINW4tRLWunYLw9HiHgtlnmcimRg",
                    "https://www.youtube.com/watch?v=AYZOHt6kz6Y",
                    "https://images.ctfassets.net/hrltx12pl8hq/4f6DfV5DbqaQUSw0uo0mWi/ff068ff5fc855601751499d694c0111a/shutterstock_376532611.jpg?fit=fill&w=800&h=300",
                    "https://theindianrover.com/wp-content/uploads/2020/05/10-Top-Websites-for-awesome-free-and-royalty-free-photos-e1531386171536.jpg",
                    "https://images.ctfassets.net/hrltx12pl8hq/VZW7M82mrxByGHjvze4wu/216d9ff35b6980d850d108a50ae387bf/Carousel_01_FreeTrial.jpg?fit=fill&w=800&h=450",
                    ]
        result = mestils.get_links(test_string)
        self.assertEqual(result, expected)

    def test_has_emote(self):
        """Check if emotes are detected properly"""
        tests = [
            "laugh:546357041891901464"
            ":w_ayaya:622141714655870982>"
            ":02Salute:483120555990712322>"
            "<:02Salute:483120555990712322>"
            "<:MeguGasm:538051441705615370>"
            "<:w_komi_yes:622139235738058793>"
            "<a:an_rainbow_100_pretty_gay:590549490482544651>"
        ]
        outputs = [mestils.is_emote(test) for test in tests]
        self.assertEqual([True] * len(tests), outputs)


if __name__ == '__main__':
    unittest.main()
