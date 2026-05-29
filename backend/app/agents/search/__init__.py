from .linkedin import search_linkedin
from .indeed import search_indeed, search_glassdoor
from .dice import search_dice, search_jobright

PORTAL_MAP = {
    "linkedin": search_linkedin,
    "indeed": search_indeed,
    "glassdoor": search_glassdoor,
    "dice": search_dice,
    "jobright": search_jobright,
}
