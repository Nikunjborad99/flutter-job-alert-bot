"""Filters for Flutter freelance and contract jobs."""

import re

ROLE = re.compile(r"\bflutter\b", re.I)

CONTRACT = re.compile(
 r"\b(freelanc(?:e|er|ing)|contract(?:or|ual)?|"
 r"independent contractor|project.based|fixed.price|hourly contract)\b",
 re.I,
 )

FULLTIME = re.compile(
 r"\b(full.time|permanent|employee only|w-?2 only)\b",
 re.I,
 )

RESTRICTED = re.compile(
 r"\b(?:us|usa|united states|canada|uk|united kingdom|"
 r"europe|eu|emea|latam|australia)\s+"
 r"(?:only|based|residents? only)\b|"
 r"\bmust\s+(?:be\s+)?(?:located|based|reside)\s+in\b",
 re.I,
 )

YEARS = re.compile(
 r"\b(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*"
 r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b|"
 r"\b(?:at least|minimum|min\.?|requires?|required|over)\s*"
 r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b|"
 r"\b(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)\b",
 re.I,
 )

HOURLY = re.compile(
 r"(?:\$|USD\s*)(\d+(?:\.\d+)?)\s*"
 r"(?:-|–|—|to)\s*(?:\$|USD\s*)?(\d+(?:\.\d+)?)"
 r"\s*(?:/\s*(?:hr|hour)|per\s*hour)\b|"
 r"(?:\$|USD\s*)(\d+(?:\.\d+)?)"
 r"\s*(?:/\s*(?:hr|hour)|per\s*hour)\b",
 re.I,
 )

def experience_ok(text):
 """Accept unspecified experience or requirements compatible with 3 years."""
 matches = list(YEARS.finditer(text))

 if not matches:
 return True

 for match in matches:
 if match.group(1) is not None:
 low = float(match.group(1))
 high = float(match.group(2))

 if low <= 3 and high >= 3:
 return True
 else:
 minimum_text = match.group(3) or match.group(4)
 minimum = float(minimum_text)

 if minimum <= 3:
 return True

 return False

def hourly_ok(text):
 """Reject explicitly stated hourly rates below $15."""
 matches = list(HOURLY.finditer(text))

 if not matches:
 return True

 for match in matches:
 if match.group(2) is not None:
 minimum = float(match.group(1))
 maximum = float(match.group(2))

 if maximum >= 15:
 return True
 else:
 rate = float(match.group(3))
 if rate >= 15:
 return True

 return False

def matches(job):
 title = job.get("title") or ""
 desc = job.get("description") or ""
 location = job.get("location") or ""
 job_type = job.get("job_type") or ""

 combined = " ".join([title, desc, job_type])
 location_text = location.lower()

 if not ROLE.search(title):
 return False

 if not CONTRACT.search(combined):
 return False

 if FULLTIME.search(job_type) and not CONTRACT.search(job_type):
 return False

 # Permit onsite/hybrid work in Surat only.
 surat_location = "surat" in location_text

 if re.search(r"\b(on.?site|onsite|hybrid)\b", location, re.I):
 if not surat_location:
 return False

 if RESTRICTED.search(location):
 return False

 if not experience_ok(combined):
 return False

 if not hourly_ok(combined):
 return False

 return True