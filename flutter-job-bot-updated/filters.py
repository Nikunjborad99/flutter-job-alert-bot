"""Conservative filters for 3.5-year Flutter freelance candidates."""
import re

ROLE = re.compile(r'\bflutter\b', re.I)
CONTRACT = re.compile(r'\b(freelanc(?:e|er|ing)|contract(?:or|ual)?|independent contractor|project.based|fixed.price|hourly contract)\b', re.I)
FULLTIME = re.compile(r'\b(full.time|permanent|employee only|w-?2 only)\b', re.I)
RESTRICTED = re.compile(r'\b(us|usa|united states|canada|uk|united kingdom|europe|eu|emea|latam|australia)\s*(only|based|residents? only)\b|\bmust (?:be )?(?:located|based|reside) in\b', re.I)
YEARS = re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)\s*(?:\+\s*)?(?:years?|yrs?)\b|\b(?:at least|minimum|min\.?|requires?|required|over)\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b|\b(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)\b', re.I)
HOURLY = re.compile(r'(?:\$|USD\s*)(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(?:\$|USD\s*)?(\d+(?:\.\d+)?)\s*(?:/\s*(?:hr|hour)|per\s*hour)|(?:\$|USD\s*)(\d+(?:\.\d+)?)\s*(?:/\s*(?:hr|hour)|per\s*hour)', re.I)


def experience_ok(text):
    """Accept unspecified years or ranges compatible with 3.5 years; reject clear 5+ minima."""
    matches = list(YEARS.finditer(text))
    if not matches:
        return True
    for m in matches:
        if m.group(1) is not None:
            low, high = float(m.group(1)), float(m.group(2))
            if low <= 3.5 <= high and low <= 5:
                return True
        else:
            minimum = float(m.group(3) or m.group(4))
            if minimum <= 3.5:
                return True
    return False


def hourly_ok(text):
    """Reject explicitly stated USD hourly pay below $15; unknown and fixed budgets are allowed."""
    matches = list(HOURLY.finditer(text))
    if not matches:
        return True
    return any(float(m.group(2) or m.group(3)) >= 15 for m in matches)


def matches(job):
    title = job['title']
    desc = job['description']
    location = job['location']
    job_type = job['job_type']
    combined = ' '.join([title, desc, job_type])
    if not ROLE.search(title):
        return False
    if not CONTRACT.search(combined):
        return False
    if FULLTIME.search(job_type) and not CONTRACT.search(job_type):
        return False
    if re.search(r'\b(on.?site|onsite|hybrid)\b', location, re.I):
        return False
    if RESTRICTED.search(location):
        return False
    # Public remote boards and LinkedIn job alert links are remote sources;
    # geography can still be unspecified and must be checked by the applicant.
    if not experience_ok(combined):
        return False
    if not hourly_ok(combined):
        return False
    return True
