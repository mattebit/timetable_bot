import datetime
import pickle

import requests
from bs4 import BeautifulSoup, PageElement
import re

import common.classes.lecture as lecture
import common.classes.course as course
from common.methods.utils import University


def fetch_unibz_lectures(year: int = 2023) -> list[lecture.Lecture]:
    """
    Args:
        year: the academic year you want to fetch

    Returns:

    """
    date_from = f"{year}-09-01"
    #date_to = f"{year}-10-01"
    date_to = f"{year+1}-07-31"
    page = 1

     #url = f"https://www.unibz.it/it/timetable/?sourceId=unibz&fromDate={date_from}&toDate={date_to}&page={page}"

    lectures : list[lecture.Lecture] = []

    done = False
    while not done:
        # TODO: do the request
        resp = requests.get(
            f"https://www.unibz.it/en/timetable/?sourceId=unibz&searchByKeywords=Lecture"
            f"&fromDate={date_from}&toDate={date_to}&page={page}")
        try:
            for i in parse_unibz_page(resp.text, str(year)):
                lectures.append(i)
        except ValueError as e:
            done = True
        print(f"Page {page} fetched")
        page += 1

    return lectures

def parse_unibz_page(html_content:str, year: str = 2023) -> list[lecture.Lecture]:
    """
    Parse the content of the unibz html page containing the lectures
    https://www.unibz.it/it/timetable/
    Args:
        html_content: the html content of the unibz timetable webpage
        year: the year the html page refer to

    Returns: the list of lecture found
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    div = soup.find("div", {"class": "g g-8@lg g-pull-4@lg g-12@print"})

    if "No results found" in str(div):
        raise ValueError("done")

    if len(div) == 0:
        raise ValueError("Invalid html content")

    txt = str(div)

    soup = BeautifulSoup(txt, 'html.parser')
    divs = soup.find_all("article", {"class": "u-cf u-push-btm"})

    res : list[lecture.Lecture] = []

    for d in divs:
        for lec in parse_unibz_day(d, year):
            res.append(lec)

    return res


def parse_unibz_day(div: PageElement, year: str = 2023) -> list[lecture.Lecture]:
    """
    Parse an unibz day pageElement, it is a specific div in the html content
    Args:
        div: the pageElement containing an unibz timetable day
        year: The year of interest in the format YYYY

    Returns: the list of parsed lectures
    """
    res : list[lecture.Lecture] = []

    txt = str(div)
    soup = BeautifulSoup(txt, 'html.parser')

    day_html = soup.find("h2", {"class": "u-h4 u-push-btm"})
    day_str = purify_str(day_html.string)
    #print(f"Day: {day_str}")

    l = soup.find("div", {"class": "g g-8@md u-padd-top-4@md"})
    items = l.findChildren("div", recursive=False)
    for item in items:
        item_content = parse_unibz_item(item)

        if item_content is None:
            continue

        location_str, hour_str, type_str, name_str, teacher_str = item_content

        hour = hour_str.split(" - ")
        timestamp_start_str = f"{day_str} {year}, {hour[0]}"
        timestamp_end_str = f"{day_str} {year}, {hour[1]}"
        #https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        dt_start = datetime.datetime.strptime(timestamp_start_str, "%A, %d %b %Y, %H:%M")
        dt_end = datetime.datetime.strptime(timestamp_end_str, "%A, %d %b %Y, %H:%M")

        lec = lecture.Lecture()
        lec.event.name = name_str
        lec.event.location = location_str
        lec.event.begin = dt_start
        lec.event.end = dt_end
        lec.event.description = f"Type:{type_str}\nHost: {teacher_str}"
        res.append(lec)

    return res


def parse_unibz_item(item: PageElement) -> None or (str,str,str,str,str):
    """
    Parse an unibz html item element (a lecture or something else) from the timetable
    Args:
        item: the item to parse

    Returns: a tuple of 5 strings, representing:
        - The location of the item
        - The hour range of the item
        - The type of the item
        - The name of the item
        - The name of the teacher or host
    """
    #print("\nITEM:")
    location_str = ""
    hour_str = ""
    type_str = ""
    name_str = ""
    teacher_str = ""

    soup = BeautifulSoup(str(item), 'html.parser')

    # Location
    location_html = soup.find("p", {"class": "u-push-btm-quarter u-tt-caps u-fs-sm u-c-theme u-fw-bold"})
    if location_html.string is not None:
        location_str = purify_str(location_html.string)
        #print(f"Location: {location_str}")

    # type
    type_html = soup.find("span", {"class": "u-c-mute"})
    type_str = type_html.string
    #print(f"type: {type_str}")

    if type_str.lower() != "lecture" and type_str.lower() != "optional lecture":
        return None

    # hour
    hour_html = soup.find("p", {"class": "u-push-btm-none u-tt-caps u-fs-sm u-fw-bold"})
    #print(f"hour: {hour_html}")
    hour_str = str(hour_html)
    pattern = "\d\d:\d\d\s-\s\d\d:\d\d"
    m = re.findall(pattern, hour_str)
    if len(m) == 0:
        # FIXME: some lectures don't have an end
        return None

    hour_str = str(m[0])
    #print(f"hour: {hour_str}")

    # name
    name_html = soup.find("h3", {"class": "u-h5 u-push-btm-1"})
    name_str = purify_str(name_html.string)
    #print(f"name: {name_str}")

    teacher_html = soup.find("a", {"class": "actionLink actionLink-small actionLink-thin"})
    #print(f"teacher: {teacher_html}")
    pattern = ".*<span>(.*)<\/span>"
    m = re.match(pattern, "".join(str(teacher_html).split("\n")))
    if m is not None:
        teacher_str = m.group(1)
        #print(f"teacher: {teacher_str}")

    return location_str, hour_str, type_str, name_str, teacher_str

def purify_str(s:str) -> str:
    s = s.strip()
    pattern = "\n"
    s = re.sub(pattern, " ", s)
    pattern = "(\s){2,}"
    s = re.sub(pattern, " ", s)
    return s

def fetch_cache_unibz_courses(cache_path: str, year_to_fetch:int = 2022):
    """
    Fetches and saves in the specified file all the unibz courses, serializing data with pickle
    Args:
        year_to_fetch: the academic year to fetch
        cache_path: the path where to store all courses and lectures
    """
    lectures = fetch_unibz_lectures(year_to_fetch)

    courses = course.group_lectures_in_courses(lectures, University.UNIBZ)

    with open(cache_path, "wb") as f:
        pickle.dump(courses, f, pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    exit()
    f = open("../../../docs/unibz_api/response.html", "r")
    txt = f.read()
    lectures = parse_unibz_page(txt)

    for i in lectures:
        print(i)
