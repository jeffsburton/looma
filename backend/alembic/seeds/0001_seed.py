from .seed import seed


def seed_0001():
    seed(
        'qualification',
        [
            {"name": "Fundamentals", "code": "FUND"},
            {"name": "Case Advocacy", "code": "CADV"},
            {"name": "OSINT Analyst", "code": "OSINT"},
            {"name": "Operations", "code": "OPS"},
            {"name": "Tactical Operations Center", "code": "TOC"},
            {"name": "FBI Background Check", "code": "BACK"},
            {"name": "Concealed Carry Permit", "code": "CCP"},
            {"name": "Stop The Bleed", "code": "STB"},
            {"name": "FEMA IS-100", "code": "F100"},
            {"name": "FEMA IS-200", "code": "F200"}
        ]
    )

    seed("ref_action", [{"name" : "Intelligence Work-up", "code": "INTEL"},
                        {"name" : "SAR Response ", "code": "SAR"},
                        {"name" : "Community Management", "code": "CM"},
                        {"name" : "Operations", "code": "OPS"}])
    seed("ref_alive", [{"name" : "Alive", "code": "A"},
                       {"name" : "Deceased ", "code": "D"},
                       {"name" : "Unknown", "code": "U"}])
    seed("ref_exploitation", [{"name" : "CSEC", "code": "CSEC"},
                              {"name" : "CSAM ", "code": "CSAM"},
                              {"name" : "Cyber Bullying", "code": "CB"},
                              {"name" : "Sextortion", "code": "ST"},
                              {"name" : "Grooming", "code": "G"},
                              {"name" : "Adult Trafficking", "code": "ATR"}])
    seed("ref_case_classification", [{"name" : "Missing/Endangered", "code": "MIS"},
                                     {"name" : "Human Trafficking/Exploitation ", "code": "HT"},
                                     {"name" : "Operations", "code": "OPS"},
                                     {"name" : "Investigative", "code": "INV"}])
    seed("ref_file_type", [{"name" : "Image", "code": "IMG"},
                           {"name" : "Operation Plan", "code": "OPS"},
                           {"name" : "Intel Summary", "code": "INTEL"},
                           {"name" : "Request for Information", "code": "RFI"},
                           {"name" : "End of Day Report", "code": "EOD"},
                           {"name" : "Missing Flyer", "code": "FLYER"},
                           {"name" : "Other", "code": "OTH"}])
    seed("ref_found_by", [{"name" : "Shepherds", "code": "SH"},
                          {"name" : "LE/Family", "code": "FAM"},
                          {"name" : "Returned (Self)", "code": "SELF"},
                          {"name" : "LE", "code": "LE"}])
    seed("ref_ministry", [{"name" : "Basic Needs", "code": "BAS"},
                          {"name" : "Lodging/Transportation", "code": "LT"},
                          {"name" : "Referrals", "code": "REF"},
                          {"name" : "Ministry Connection", "code": "MIN"}])
    seed("ref_per_relation", [{"name" : "Law Enforcement", "code": "LE"},
                              {"name" : "Social Services", "code": "SS"},
                              {"name" : "Juvenile Probation", "code": "JP"},
                              {"name" : "Other", "code": "OTH"}])
    seed("ref_race", [{"name" : "Asian", "code": "A"},
                      {"name" : "Biracial ", "code": "BR"},
                      {"name" : "Black", "code": "B"},
                      {"name" : "Hispanic", "code": "H"},
                      {"name" : "Pacific Islander", "code": "PI"},
                      {"name" : "Unknown", "code": "U"},
                      {"name" : "White", "code": "W"},
                      {"name" : "Native American", "code": "NA"}])
    seed("ref_requested_by", [{"name" : "Agency", "code": "AG"},
                              {"name" : "Family ", "code": "FAM"},
                              {"name" : "Law Enforcement", "code": "LE"},
                              {"name" : "Non-governmental Organization", "code": "NGO"}])
    seed("ref_scope", [{"name" : "National", "code": "NAT"},
                       {"name" : "Regional", "code": "RGN"},
                       {"name" : "TBS", "code": "TBS"}])
    seed("ref_sex", [{"name" : "Female", "code": "F"},
                     {"name" : "Male ", "code": "M"}])
    seed("ref_sm_platform", [{"name" : "Cash App", "code": "CA"},
                             {"name" : "Dating Site", "code": "DATE"},
                             {"name" : "Discord", "code": "DIS"},
                             {"name" : "Facebook", "code": "FB"},
                             {"name" : "Instagram", "code": "IG"},
                             {"name" : "LinkedIn", "code": "LI"},
                             {"name" : "Financial", "code": "FIN"},
                             {"name" : "Snapchat", "code": "SNAP"},
                             {"name" : "TikTok", "code": "TIK"},
                             {"name" : "Venmo", "code": "VEN"},
                             {"name" : "X", "code": "X"},
                             {"name" : "Other", "code": "OTH"}])
    seed(
        "ref_state",
        [
            {"name": "Alabama", "code": "AL"},
            {"name": "Alaska", "code": "AK"},
            {"name": "Arizona", "code": "AZ"},
            {"name": "Arkansas", "code": "AR"},
            {"name": "California", "code": "CA"},
            {"name": "Colorado", "code": "CO"},
            {"name": "Connecticut", "code": "CT"},
            {"name": "Delaware", "code": "DE"},
            {"name": "Florida", "code": "FL"},
            {"name": "Georgia", "code": "GA"},
            {"name": "Hawaii", "code": "HI"},
            {"name": "Idaho", "code": "ID"},
            {"name": "Illinois", "code": "IL"},
            {"name": "Indiana", "code": "IN"},
            {"name": "Iowa", "code": "IA"},
            {"name": "Kansas", "code": "KS"},
            {"name": "Kentucky", "code": "KY"},
            {"name": "Louisiana", "code": "LA"},
            {"name": "Maine", "code": "ME"},
            {"name": "Maryland", "code": "MD"},
            {"name": "Massachusetts", "code": "MA"},
            {"name": "Michigan", "code": "MI"},
            {"name": "Minnesota", "code": "MN"},
            {"name": "Mississippi", "code": "MS"},
            {"name": "Missouri", "code": "MO"},
            {"name": "Montana", "code": "MT"},
            {"name": "Nebraska", "code": "NE"},
            {"name": "Nevada", "code": "NV"},
            {"name": "New Hampshire", "code": "NH"},
            {"name": "New Jersey", "code": "NJ"},
            {"name": "New Mexico", "code": "NM"},
            {"name": "New York", "code": "NY"},
            {"name": "North Carolina", "code": "NC"},
            {"name": "North Dakota", "code": "ND"},
            {"name": "Ohio", "code": "OH"},
            {"name": "Oklahoma", "code": "OK"},
            {"name": "Oregon", "code": "OR"},
            {"name": "Pennsylvania", "code": "PA"},
            {"name": "Rhode Island", "code": "RI"},
            {"name": "South Carolina", "code": "SC"},
            {"name": "South Dakota", "code": "SD"},
            {"name": "Tennessee", "code": "TN"},
            {"name": "Texas", "code": "TX"},
            {"name": "Utah", "code": "UT"},
            {"name": "Vermont", "code": "VT"},
            {"name": "Virginia", "code": "VA"},
            {"name": "Washington", "code": "WA"},
            {"name": "West Virginia", "code": "WV"},
            {"name": "Wisconsin", "code": "WI"},
            {"name": "Wyoming", "code": "WY"},
            # Others: DC and U.S. territories
            {"name": "District of Columbia", "code": "DC"},
            {"name": "American Samoa", "code": "AS"},
            {"name": "Guam", "code": "GU"},
            {"name": "Northern Mariana Islands", "code": "MP"},
            {"name": "Puerto Rico", "code": "PR"},
            {"name": "U.S. Virgin Islands", "code": "VI"},
        ],
    )
    seed("ref_status", [{"name" : "Open", "code": "OPEN"},
                        {"name" : "Closed ", "code": "CLOSED"},
                        {"name" : "Inactive", "code": "INACT"}])
    seed("ref_sub_relation", [{"name" : "Asian", "code": "A"},
                              {"name" : "Biracial ", "code": "BR"},
                              {"name" : "Black", "code": "B"},
                              {"name" : "Hispanic", "code": "H"},
                              {"name" : "Pacific Islander", "code": "PI"},
                              {"name" : "Unknown", "code": "U"},
                              {"name" : "White", "code": "W"},
                              {"name" : "Native American", "code": "NA"}])
    seed(
        'team_role',
        [
            {"name": "Leader", "code": "LEAD"},
            {"name": "Assistant Leader", "code": "ASST"},
            {"name": "Case Advocate", "code": "CADV"},
            {"name": "Lead Analyst", "code": "INTEL"},
            {"name": "OSINT/Operations", "code": "OO"},
            {"name": "Ministry", "code": "MIN"},
        ]
    )



    role_id: int = seed("role", {"name": "Administration", "code": "ADMIN", "description": "Admin role."})
    perm_id :int = seed("permission", {"name": "Admin panel", "code": "ADMIN", "description": "Administration panel."})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "Teams", "code": "TEAMS", "description": "Edit teams."})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "Organizations", "code": "ORGS", "description": "Edit organizations."})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})

    seed("role", {"name": "Leadership", "code": "LEADER", "description": "Can see all cases and organize teams."})
    seed("role", {"name": "Team Member", "code": "MEMBER", "description": "Member of a team, can see assigned cases."})
    seed("role", {"name": "Outside", "code": "OUTSIDE", "description": "Outside organization, limited permissions."})




    org_id: int  = seed('organization', {"name": "Called2Rescue", "ref_state_id": 9})


    app_user_id = seed("app_user", {"first_name": "Jeff", "last_name": "Burton", "email": "jsburton@gmail.com", "password_hash": "$pbkdf2-sha256$29000$n1NqLSWEkPJeC4EQYqyVMg$DQ3w24lr3LDKF663lmBO4E1D6lB3x2ZWbdZhDNBjkfA", "is_active": True})
    seed("app_user_role", {"app_user_id": app_user_id, "role_id": role_id})