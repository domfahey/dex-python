"""Job title parsing for company/role extraction.

This module provides utilities to parse job title strings that contain
both role and company information separated by "at" or "@".

Example:
    >>> from dex_python.enrichment import parse_job_title
    >>> result = parse_job_title("Software Engineer at Google")
    >>> print(result)
    {'role': 'Software Engineer', 'company': 'Google'}
"""

import re


def parse_job_title(job_title: str | None) -> dict[str, str | None]:
    """Parse job title to extract role and company.

    Handles common patterns like:
    - "Software Engineer at Google"
    - "Developer @ Microsoft"
    - "VP and NJ State Counsel at Fidelity National Title Group"

    Args:
        job_title: Job title string to parse.

    Returns:
        Dict with 'role' and 'company' keys. Company is None if
        no "at" or "@" separator found.
    """
    if job_title is None:
        return {"role": None, "company": None}

    if not job_title:
        return {"role": "", "company": None}

    # Pattern matches " at " or " @ " (case-insensitive)
    pattern = r"\s+(?:at|@)\s+"
    match = re.split(pattern, job_title, maxsplit=1, flags=re.IGNORECASE)

    if len(match) == 2:
        role = match[0].strip()
        company = match[1].strip()
        return {"role": role, "company": company}

    # No company pattern found - entire title is the role
    return {"role": job_title.strip(), "company": None}
