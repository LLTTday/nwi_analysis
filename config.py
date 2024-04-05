colors = ["orangered", "yellow", "lightgreen", "darkolivegreen"]

nwi_labels = [
    "Least Walkable",
    "Below Average Walkability",
    "Above Average Walkability",
    "Most Walkable",
]

field_dict = {
    "Total": {
        "Population": "B02001_001E",
    },
    "Race": {
        "White": "B02001_002E",
        "Black": "B02001_003E",
        "Native American": "B02001_004E",
        "Asian": "B02001_005E",
        "Pacific Islander": "B02001_006E",
        "Other": "B02001_007E",
        "Two or More": "B02001_008E",
    },
    "Ethnicity": {
        "Hispanic": "B03002_003E",
        "Non-Hispanic": "B03002_002E",
    },
    "Income": {
        "Less than $10,000": "B19001_002E",
        "$10,000 to $14,999": "B19001_003E",
        "$15,000 to $19,999": "B19001_004E",
        "$20,000 to $24,999": "B19001_005E",
        "$25,000 to $29,999": "B19001_006E",
        "$30,000 to $34,999": "B19001_007E",
        "$35,000 to $39,999": "B19001_008E",
        "$40,000 to $44,999": "B19001_009E",
        "$45,000 to $49,999": "B19001_010E",
        "$50,000 to $59,999": "B19001_011E",
        "$60,000 to $74,999": "B19001_012E",
        "$75,000 to $99,999": "B19001_013E",
        "$100,000 to $124,999": "B19001_014E",
        "$125,000 to $149,999": "B19001_015E",
        "$150,000 to $199,999": "B19001_016E",
        "$200,000 or more": "B19001_017E",
    },
    "Education": {
        "Less than High School": "B15003_002Z",
        "HS Grad/GED": "B15003_003Z",
        "Some College": "B15003_004Z",
        "Associate's Degree": "B15003_021E",
        "Bachelor's Degree": "B15003_022E",
        "Master's Degree": "B15003_023E",
        "Professional Degree": "B15003_024E",
        "Doctorate": "B15003_025E",
    },
    "Homeownership": {
        "Owner Occupied": "B25008_002E",
        "Renter Occupied": "B25008_003E",
    },
    "Age": {
        "Under 18": "B01001_003Z",
        "18 to 24": "B01001_004Z",
        "25 to 34": "B01001_005Z",
        "35 to 44": "B01001_006Z",
        "45 to 54": "B01001_007Z",
        "55 to 64": "B01001_008Z",
        "65 to 74": "B01001_009Z",
        "75 to 84": "B01001_010Z",
        "85 and Over": "B01001_011Z",
    },
    "Transportation": {
        "Single Occupancy Vehicle": "B08301_002E",
        "Carpool": "B08301_003E",
        "Public Transit": "B08301_010E",
        "Walking": "B08301_019E",
        "Bicycle": "B08301_018E",
        "Other": "B08301_020E",
        "Work from Home": "B08301_021E",
    },
}

fields = [value for sub_dict in field_dict.values() for value in sub_dict.values()]

demo_cats = {
    "Age": "",
    "Race": "",
    "Ethnicity": "",
    "Income": "",
    "Education": "",
    "Homeownership": "",
    "Transportation": "",
}
