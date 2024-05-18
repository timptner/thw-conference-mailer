import locale
import logging

from bs4 import BeautifulSoup, Tag, NavigableString, PageElement
from datetime import datetime


locale.setlocale(locale.LC_ALL, "de_DE")

logger = logging.getLogger(__name__)


def parse(text: str) -> dict:
    soup = BeautifulSoup(text, "html.parser")

    node = soup.find("div", attrs={"class": "courseList"})
    if not isinstance(node, Tag):
        raise Exception("Expected tag not found")

    next_page = get_next_page(node)
    courses = get_courses(node)

    return {
        "next_page": next_page,
        "courses": courses,
    }


def get_next_page(node: Tag) -> str | None:
    navigation_node = node.find("div", attrs={"class": "navIndex"})
    if not isinstance(navigation_node, Tag):
        raise Exception("Expected tag not found")

    page_node = navigation_node.find("ul", attrs={"class": "advancedSearch left"})
    if not isinstance(page_node, Tag):
        raise Exception("Expected tag not found")

    next_page = navigation_node.find("a", attrs={"class": "forward"})
    if next_page is None:
        return None

    if not isinstance(next_page, Tag):
        raise Exception("Expected tag not found")

    return next_page.attrs["href"]


class Course:
    def __init__(
        self,
        location: str,
        title: str,
        start: datetime,
        end: datetime,
        deadline: datetime | None,
        last_minute: dict | None,
    ) -> None:
        self.location = location
        self.title = title
        self.start = start
        self.end = end
        self.deadline = deadline
        if last_minute:
            self.last_minute = {
                "url": last_minute["url"],
                "seats": last_minute["seats"],
            }

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"Course<{self.title}>"


def get_courses(node: Tag) -> list[Course]:
    courses_node = node.find("div", attrs={"class": "teaserlist"})
    if not isinstance(courses_node, Tag):
        raise Exception("Expected tag not found")

    courses = []
    for course_node in courses_node.find_all("div", attrs={"class": "teaser course"}):
        location = course_node.find("span", attrs={"class": "metadata"}).string
        title_node = course_node.find("h2")
        if not isinstance(title_node, Tag):
            raise Exception("Expected tag not found")

        details = title_node.find("a")
        if details is None:
            title = title_node.string or ""
        else:
            if not isinstance(details, Tag):
                raise Exception("Expected tag not found")

            title = details.string or ""

        dates = course_node.find("dl", attrs={"class": "docData"})
        dates = [
            datetime.strptime(item.string, "%a. %d.%m.%Y, %H:%M Uhr")
            for item in dates.find_all("dd")
        ]
        start = dates[0]
        end = dates[1]

        registration = course_node.find("dl", attrs={"class": "courseAction docData"})
        if isinstance(registration, Tag):
            registration = [
                datetime.strptime(item.string, "%d.%m.%Y")
                for item in registration.find_all("dd")
            ]
            deadline = registration[0]
        else:
            deadline = None

        last_minute_node = course_node.find("p", attrs={"class": "courseAction"})
        if isinstance(last_minute_node, Tag):
            link = last_minute_node.find("a")
            if not isinstance(link, Tag):
                raise Exception("Expected tag not found")

            url = link.attrs["href"]
            seats = link.string
            if seats is None:
                raise Exception("Expected string not found")

            seats = int(
                seats.removeprefix("Noch")
                .removesuffix("Last-Minute-Plätze verfügbar")
                .strip()
            )
            last_minute = {
                "url": url,
                "seats": seats,
            }
        else:
            last_minute = None
        course = Course(location, title, start, end, deadline, last_minute)
        courses.append(course)

    return courses
