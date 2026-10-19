"""
Region / SubRegion mapping for the WPP2024 country panel.

Source of truth: the grouping supplied by the team (USER_REGIONS below).
The UN file uses *official* country names ("Russian Federation"), the team list uses
short names ("Russia"), so names are resolved through an explicit ALIASES table and the
resolution is ASSERTED to be complete and one-to-one (see `resolve_user_list`).

Territories / dependencies that are in the UN file but NOT in the team list
(Puerto Rico, Hong Kong, Greenland, ...) are assigned using the UN's own ParentID
subregion hierarchy, and are flagged with RegionSource = "un_hierarchy".
"""
import re

USER_REGIONS = {
    "Africa": {
        "Northern Africa": ["Algeria", "Egypt", "Libya", "Morocco", "Sudan", "Tunisia"],
        "Eastern Africa": ["Burundi", "Comoros", "Djibouti", "Eritrea", "Ethiopia", "Kenya", "Madagascar",
                           "Malawi", "Mauritius", "Mozambique", "Rwanda", "Seychelles", "Somalia",
                           "South Sudan", "Uganda", "Tanzania", "Zambia", "Zimbabwe"],
        "Middle Africa": ["Angola", "Cameroon", "Central African Republic", "Chad", "Congo", "DR Congo",
                          "Equatorial Guinea", "Gabon", "São Tomé and Príncipe"],
        "Southern Africa": ["Botswana", "Eswatini", "Lesotho", "Namibia", "South Africa"],
        "Western Africa": ["Benin", "Burkina Faso", "Cabo Verde", "Côte d’Ivoire", "Gambia", "Ghana", "Guinea",
                           "Guinea-Bissau", "Liberia", "Mali", "Mauritania", "Niger", "Nigeria", "Senegal",
                           "Sierra Leone", "Togo"],
    },
    "Asia": {
        "Central Asia": ["Kazakhstan", "Kyrgyzstan", "Tajikistan", "Turkmenistan", "Uzbekistan"],
        "Eastern Asia": ["China", "Japan", "Mongolia", "North Korea", "South Korea"],
        "South-eastern Asia": ["Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar", "Philippines",
                               "Singapore", "Thailand", "Timor-Leste", "Viet Nam"],
        "Southern Asia": ["Afghanistan", "Bangladesh", "Bhutan", "India", "Iran", "Maldives", "Nepal",
                          "Pakistan", "Sri Lanka"],
        "Western Asia": ["Armenia", "Azerbaijan", "Bahrain", "Cyprus", "Georgia", "Iraq", "Israel", "Jordan",
                         "Kuwait", "Lebanon", "Oman", "Qatar", "Saudi Arabia", "Syria", "Türkiye",
                         "United Arab Emirates", "Yemen", "State of Palestine (observer state)"],
    },
    "Europe": {
        "Eastern Europe": ["Belarus", "Bulgaria", "Czechia", "Hungary", "Moldova", "Poland", "Romania",
                           "Russia", "Slovakia", "Ukraine"],
        "Northern Europe": ["Denmark", "Estonia", "Finland", "Iceland", "Ireland", "Latvia", "Lithuania",
                            "Norway", "Sweden", "United Kingdom"],
        "Southern Europe": ["Albania", "Andorra", "Bosnia and Herzegovina", "Croatia", "Greece", "Italy",
                            "Malta", "Montenegro", "North Macedonia", "Portugal", "San Marino", "Serbia",
                            "Slovenia", "Spain", "Holy See (observer)"],
        "Western Europe": ["Austria", "Belgium", "France", "Germany", "Liechtenstein", "Luxembourg", "Monaco",
                           "Netherlands", "Switzerland"],
    },
    "Americas": {
        "Caribbean": ["Antigua and Barbuda", "Bahamas", "Barbados", "Cuba", "Dominica", "Dominican Republic",
                      "Grenada", "Haiti", "Jamaica", "Saint Kitts and Nevis", "Saint Lucia",
                      "Saint Vincent and the Grenadines", "Trinidad and Tobago"],
        "Central America": ["Belize", "Costa Rica", "El Salvador", "Guatemala", "Honduras", "Mexico",
                            "Nicaragua", "Panama"],
        "South America": ["Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador", "Guyana",
                          "Paraguay", "Peru", "Suriname", "Uruguay", "Venezuela"],
        "Northern America": ["Canada", "United States"],
    },
    "Oceania": {
        "Australia and New Zealand": ["Australia", "New Zealand"],
        "Melanesia": ["Fiji", "Papua New Guinea", "Solomon Islands", "Vanuatu"],
        "Micronesia": ["Kiribati", "Marshall Islands", "Micronesia (Federated States of)", "Nauru", "Palau"],
        "Polynesia": ["Samoa", "Tonga", "Tuvalu"],
    },
}

# team-list name  ->  exact UN `Location` string used in the WPP file
ALIASES = {
    "Bolivia": "Bolivia (Plurinational State of)",
    "Brunei": "Brunei Darussalam",
    "DR Congo": "Democratic Republic of the Congo",
    "Iran": "Iran (Islamic Republic of)",
    "Laos": "Lao People's Democratic Republic",
    "Micronesia (Federated States of)": "Micronesia (Fed. States of)",
    "Moldova": "Republic of Moldova",
    "North Korea": "Dem. People's Republic of Korea",
    "Russia": "Russian Federation",
    "São Tomé and Príncipe": "Sao Tome and Principe",
    "South Korea": "Republic of Korea",
    "State of Palestine (observer state)": "State of Palestine",
    "Syria": "Syrian Arab Republic",
    "Tanzania": "United Republic of Tanzania",
    "United States": "United States of America",
    "Venezuela": "Venezuela (Bolivarian Republic of)",
    "Holy See (observer)": "Holy See",
}

# UN subregion label (as it appears in the WPP file hierarchy) -> team SubRegion label
UN_SUBREGION_TO_TEAM = {
    "Australia/New Zealand": "Australia and New Zealand",
    "South-Eastern Asia": "South-eastern Asia",
}
# Canada, USA, Bermuda, Greenland, Saint Pierre & Miquelon hang off UN geographic region 918
UN_NORTHERN_AMERICA_PARENT_ID = 918


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("’", "'")).strip().casefold()


def subregion_to_region():
    return {sub: reg for reg, subs in USER_REGIONS.items() for sub in subs}


def resolve_user_list(un_country_names):
    """
    Map every team-list name onto exactly one UN country name.
    Returns DataFrame-like list of dicts. Raises AssertionError on any unresolved or duplicate name.
    """
    un_lookup = {_norm(n): n for n in un_country_names}
    rows, seen = [], {}
    for region, subs in USER_REGIONS.items():
        for sub, names in subs.items():
            for name in names:
                target = ALIASES.get(name, name)
                key = _norm(target)
                assert key in un_lookup, f"UNRESOLVED team-list name: {name!r} (looked for {target!r})"
                un_name = un_lookup[key]
                assert un_name not in seen, f"DUPLICATE: {un_name!r} listed under {seen[un_name]} and {sub}"
                seen[un_name] = sub
                rows.append({"team_name": name, "Location": un_name, "Region": region, "SubRegion": sub})
    return rows
