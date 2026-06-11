import re
import sys

EU_COUNTRIES = {
    "uk", "united kingdom", "england", "scotland", "wales", "northern ireland",
    "germany", "deutschland", "france", "netherlands", "holland", "sweden", "spain",
    "italy", "poland", "portugal", "belgium", "austria", "switzerland", "denmark",
    "norway", "finland", "ireland", "czech republic", "czechia", "romania",
    "hungary", "greece", "croatia", "slovakia", "slovenia", "estonia", "latvia",
    "lithuania", "luxembourg", "malta", "cyprus", "bulgaria", "serbia",
    "gb", "de", "fr", "nl", "se", "es", "it", "pl", "pt", "be", "at", "ch",
    "dk", "no", "fi", "ie", "cz", "ro", "hu", "gr", "hr", "sk", "si", "ee",
    "lv", "lt", "lu", "mt", "cy", "bg", "rs",
}

EU_CITIES = {
    "london", "ldn", "berlin", "amsterdam", "paris", "stockholm", "dublin",
    "barcelona", "madrid", "lisbon", "warsaw", "vienna", "zurich", "geneva",
    "copenhagen", "oslo", "helsinki", "brussels", "rome", "milan", "munich",
    "hamburg", "frankfurt", "bucharest", "budapest", "prague", "zagreb",
    "vilnius", "riga", "tallinn", "edinburgh", "manchester", "bristol",
    "cambridge", "oxford", "london, uk", "berlin, germany",
}

EU_FLAGS = {
    "🇬🇧", "🇩🇪", "🇫🇷", "🇳🇱", "🇸🇪", "🇪🇸", "🇮🇹", "🇵🇱", "🇵🇹", "🇧🇪",
    "🇦🇹", "🇨🇭", "🇩🇰", "🇳🇴", "🇫🇮", "🇮🇪", "🇨🇿", "🇷🇴", "🇭🇺", "🇬🇷",
    "🇭🇷", "🇸🇰", "🇸🇮", "🇪🇪", "🇱🇻", "🇱🇹", "🇱🇺", "🇲🇹", "🇨🇾", "🇧🇬", "🇷🇸",
}


def is_eu_location(text: str) -> bool:
    if not text:
        return False
    for flag in EU_FLAGS:
        if flag in text:
            return True
    normalised = text.lower().strip()
    parts = re.split(r"[,/|·•\s]+", normalised)
    for part in parts:
        part = part.strip()
        if part in EU_COUNTRIES or part in EU_CITIES:
            return True
    print(f"[eu_loc MISS] {text!r}", file=sys.stderr)
    return False
