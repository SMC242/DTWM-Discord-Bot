"""Handles getting things from Instagram links."""

import requests
from bs4 import BeautifulSoup
from typing import *
from Utils import common

class _ElementGetter:
    """Gets the element from the Instagram link.
    Base class for getting things from Instagram links.
    
    ATTRIBUTES
    element:  async_property[str]
        The HTML element found by the class.
    url:  str
        The page to get the element from.
    tag:  Optional[str]
        Only elements with this tag will be returned.
    cls:  Optional[str]
        The class of the element to get.
        Inspect the element with a browser to get its class.
    id:  Optional[str]
        The id of the element to get.
        Inspect the element with a browser to get its id.
    """

    def __init__(self, url: str, tag: str = None,
                 class_: str = None,
                 id_: str = None):
        """Use await self.elements to fetch the element.
        
        ARGUMENTS
        url:
            The page to get the element from.
        Either class_ or id_ must be passed.
        tag:
            Elements tagged with this will be found.
            Do not include the <> parentheses.
        class_:
            The class of the element to get.
            Inspect the element with a browser to get its class.
        id_:
            The id of the element to get.
            Inspect the element with a browser to get its id.
            
        RAISES
        ValueError: neither class_ nor id_ was passed."""
        self.url = url
        # require either class_ or id_
        if not any((tag, class_, id_)):
            raise ValueError("Neither class_ nor id_ was passed.")
        self.tag = tag
        self.cls = class_
        self.id = id_

    @property
    def elements(self) -> List[Optional[str]]:
        """Get the element from the URL identified by
        either self.cls or self.id.
        
        RETURNS
        List[]: no elements were found.
        List[str]: the elements that were found."""
        # get the HTML
        html = requests.get(self.url).text
        # parse the HTML
        soup = BeautifulSoup(html, "html.parser")
        # debugging info
        if common.DEV_VERSION:
            with open("./Text Files/HTMLDump.txt", "w+", encoding = "utf-8") as f:
                f.write(f"url = {self.url}\n")
                f.write(soup.prettify())

        return soup.find_all(self.tag, class_ = self.cls,
                                 id = self.id)


class InstagramImages(_ElementGetter):
    """Gets the link to the first image from the
    provided link."""

    def __init__(self, url: str):
        super().__init__(url, tag = "img", class_ = "KL4Bh")

    @property
    def image(self) -> Optional[str]:
        """Get the image from the link.

        RETURNS
        None: no image found.
        str: the link to the image."""
        element = self.elements[0]
        # check that an element was found
        if not element:
            return None
        soup = BeautifulSoup(element, "html.parser")
        print(soup.contents)