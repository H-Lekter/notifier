from typing import Generator, Iterable, cast

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

listpages_div_class = "listpages-div-wrap"

listpages_div_wrap = f"""
[[div_ class="{listpages_div_class}"]]
{{}}
[[/div]]
"""


class Connection:
    """Connection to Wikidot facilitating communications with it."""

    def __init__(self):
        """Connect to Wikidot."""
        self._session = requests.sessions.Session()

    def post(self, url, **kwargs):
        """Make a POST request."""
        return self._session.request("POST", url, **kwargs)

    def module(self, wiki: str, moduleName: str, **kwargs):
        """Call a Wikidot module."""
        response = self.post(
            "http://{}.wikidot.com/ajax-module-connector.php".format(wiki),
            data=dict(
                moduleName=moduleName, wikidot_token7="123456", **kwargs
            ),
            cookies={"wikidot_token7": "123456"},
        ).json()
        if response["status"] != "ok":
            raise RuntimeError(response.get("message") or response["status"])
        return response

    def paginated_module(
        self,
        wiki: str,
        moduleName: str,
        index_key: str,
        index_key_increment=1,
        **kwargs,
    ):
        """Generator that iterates pages of a paginated module response.

        :param wiki: The name of the wiki to query.
        :param moduleName: The name of the module (which will return a
        paginated result) to query.
        :param index_key: The name of the parameter of this module that must be
        incrememented to access the next page.
        :param index_key_increment: The amount by which to increment the
        index key for each page.
        """
        first_page = self.module(wiki, moduleName, **kwargs)
        yield first_page
        page_selectors = cast(
            Tag,
            BeautifulSoup(first_page["body"], "html.parser").find(
                class_="pager"
            ),
        )
        if not page_selectors:
            return
        final_page_selector = cast(
            Tag,
            cast(Tag, page_selectors.select(".target:nth-last-child(2)")[0]).a,
        )
        final_page_index = int(final_page_selector.get_text())
        for page_index in range(1, final_page_index + 1):
            kwargs.update({index_key: page_index * index_key_increment})
            yield self.module(wiki, moduleName, **kwargs)

    def listpages(
        self, wiki: str, *, module_body: str, **kwargs
    ) -> Generator[Tag, None, None]:
        """Execute a ListPages search against a wiki and return all results
        as soup."""
        module_body = listpages_div_wrap.format(module_body)
        items = (
            soup
            for page in self.paginated_module(
                wiki,
                "list/ListPagesModule",
                index_key="offset",
                index_key_increment=250,
                perPage=250,
                module_body=module_body,
                **kwargs,
            )
            for soup in cast(
                Iterable[Tag],
                BeautifulSoup(page["body"], "html.parser").find_all(
                    class_=listpages_div_class
                ),
            )
        )
        return items

    def login(self, username: str, password: str) -> None:
        """Log in to a Wikidot account."""
        print("Logging in...")
        self.post(
            "https://www.wikidot.com/default--flow/login__LoginPopupScreen",
            data=dict(
                login=username,
                password=password,
                action="Login2Action",
                event="login",
            ),
        )

    def get_new_posts(self, wiki):
        """Fetches information about new posts from a wiki's RSS."""
        # TODO

    def get_contacts(self):
        """Get the account's contacts list and their emails in order to be
        able to send email notifications.

        Emails are personal information and are not cached to the database;
        they are discarded as soon as they're used.

        Connection needs to be logged in.
        """
        # TODO
