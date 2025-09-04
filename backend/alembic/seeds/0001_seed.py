from app.db.base import seed, seed_ref, get_ref_value_id
from pathlib import Path


def seed_0001():


    ref_type_id: int = seed("ref_type", {"name" : "Shepherd Actions", "code": "SH_ACTION", "description": "Actions taken by Shepherds during case"})
    seed_ref(ref_type_id, [["INTEL", "Intelligence Work-up", ""],
                             ["SAR", "SAR Response ", ""],
                             ["CM", "Community Management", ""],
                             ["OPS", "Operations", ""]])

    ref_type_id: int = seed("ref_type", {"name" : "Victim Living Status", "code": "LIVING", "description": "Whether the missing person is living or deceased"})
    seed_ref(ref_type_id, [["A", "Alive", ""],
                           ["D", "Deceased ", ""],
                           ["U", "Unknown", ""]])

    ref_type_id: int = seed("ref_type", {"name" : "Exploitation", "code": "EXPLOIT", "description": "Types of exploitation"})
    seed_ref(ref_type_id, [["CSEC", "CSEC", ""],
                           ["CSAM ", "CSAM", ""],
                           ["CB", "Cyber Bullying", ""],
                           ["ST", "Sextortion", ""],
                           ["G", "Grooming", ""],
                           ["ATR", "Adult Trafficking", ""]])

    ref_type_id: int = seed("ref_type", {"name" : "Case Classfication", "code": "CASE_CLASS", "description": "Case Classification   "})
    seed_ref(ref_type_id, [["MIS", "Missing/Endangered", ""],
                           ["HT", "Human Trafficking/Exploitation ", ""],
                           ["OPS", "Operations", ""],
                           ["INV", "Investigative", ""]])

    ref_type_id: int = seed("ref_type", {"name" : "Found By", "code": "FOUND_BY", "description": "How the victim was found"})
    seed_ref(ref_type_id, [["SH", "Shepherds", ""],
                           ["FAM", "Family", ""],
                           ["SELF", "Returned (Self)", ""],
                           ["LE", "LE", ""]])

    ref_type_id: int = seed("ref_type", {"name" : "Ministry Types", "code": "MINISTRY", "description": "Types of ministry provided"})
    seed_ref(ref_type_id, [["BAS", "Basic Needs", ""],
                           ["LT", "Lodging/Transportation", ""],
                           ["REF", "Referrals", ""],
                           ["MIN", "Ministry Connection", ""]])

    ref_type_id: int = seed("ref_type", {"name" : "Person's Relationship to Case", "code": "PER_REL", "description": "Relationship of a person (non-investigative subjects, eg Agency, LE, etc.) to the case"})
    seed_ref(ref_type_id, [["LE", "Law Enforcement", ""],
                           ["SS", "Social Services", ""],
                           ["JP", "Juvenile Probation", ""],
                           ["OTH", "Other", ""]])

    ref_type_id: int = seed("ref_type", {"name" : "Race", "code": "RACE", "description": "Race of a person. "})
    seed_ref(ref_type_id, [["A", "Asian"],
                           ["BR", "Biracial"],
                           ["B", "Black"],
                           ["H", "Hispanic"],
                           ["PI", "Pacific Islander"],
                           ["U", "Unknown"],
                           ["W", "White"],
                           ["NA", "Native American"]])

    ref_type_id: int = seed("ref_type", {"name" : "Requested By", "code": "REQ_BY", "description": "Who requested assistance"})
    seed_ref(ref_type_id, [["AG", "Agency"],
                           ["FAM", "Family"],
                           ["LE", "Law Enforcement"],
                           ["NGO", "Non-governmental Organization"],
                           ["RES", "Research"]])

    ref_type_id: int = seed("ref_type", {"name" : "Scope", "code": "SCOPE", "description": "Scope of Search"})
    seed_ref(ref_type_id, [["NAT", "National"],
                           ["RGN", "Regional"],
                           ["TBS", "Big Search"]])

    ref_type_id: int = seed("ref_type", {"name" : "Sex", "code": "SEX", "description": "Person's sex"})
    seed_ref(ref_type_id, [["F", "Female"],
                           ["M", "Male"]])

    ref_type_id: int = seed("ref_type", {"name" : "Social Media Platform", "code": "SM_PLATFORM", "description": "Social media platform name"})
    seed_ref(ref_type_id, [["CA", "Cash App"],
                           ["DATE", "Dating Site"],
                           ["DIS", "Discord"],
                           ["FB", "Facebook"],
                           ["IG", "Instagram"],
                           ["LI", "LinkedIn"],
                           ["FIN", "Financial"],
                           ["SNAP", "Snapchat"],
                           ["TIK", "TikTok"],
                           ["VEN", "Venmo"],
                           ["X", "X"],
                           ["OTH", "Other"]])

    ref_type_id: int = seed("ref_type", {"name" : "State", "code": "STATE", "description": "US state"})
    seed_ref(ref_type_id, [["AL", "Alabama"],
                           ["AK", "Alaska"],
                           ["AZ", "Arizona"],
                           ["AR", "Arkansas"],
                           ["CA", "California"],
                           ["CO", "Colorado"],
                           ["CT", "Connecticut"],
                           ["DE", "Delaware"],
                           ["FL", "Florida"],
                           ["GA", "Georgia"],
                           ["HI", "Hawaii"],
                           ["ID", "Idaho"],
                           ["IL", "Illinois"],
                           ["IN", "Indiana"],
                           ["IA", "Iowa"],
                           ["KS", "Kansas"],
                           ["KY", "Kentucky"],
                           ["LA", "Louisiana"],
                           ["ME", "Maine"],
                           ["MD", "Maryland"],
                           ["MA", "Massachusetts"],
                           ["MI", "Michigan"],
                           ["MN", "Minnesota"],
                           ["MS", "Mississippi"],
                           ["MO", "Missouri"],
                           ["MT", "Montana"],
                           ["NE", "Nebraska"],
                           ["NV", "Nevada"],
                           ["NH", "New Hampshire"],
                           ["NJ", "New Jersey"],
                           ["NM", "New Mexico"],
                           ["NY", "New York"],
                           ["NC", "North Carolina"],
                           ["ND", "North Dakota"],
                           ["OH", "Ohio"],
                           ["OK", "Oklahoma"],
                           ["OR", "Oregon"],
                           ["PA", "Pennsylvania"],
                           ["RI", "Rhode Island"],
                           ["SC", "South Carolina"],
                           ["SD", "South Dakota"],
                           ["TN", "Tennessee"],
                           ["TX", "Texas"],
                           ["UT", "Utah"],
                           ["VT", "Vermont"],
                           ["VA", "Virginia"],
                           ["WA", "Washington"],
                           ["WV", "West Virginia"],
                           ["WI", "Wisconsin"],
                           ["WY", "Wyoming"],
                           ["DC", "District of Columbia"],
                           ["AS", "American Samoa"],
                           ["GU", "Guam"],
                           ["MP", "Northern Mariana Islands"],
                           ["PR", "Puerto Rico"],
                           ["VI", "U.S. Virgin Islands"]])

    ref_type_id: int = seed("ref_type", {"name" : "Case Status", "code": "STATUS", "description": "Status of the case"})
    seed_ref(ref_type_id, [["OPEN", "Open"],
                           ["CLOSED", "Closed"],
                           ["INACT", "Inactive"]])

    ref_type_id: int = seed("ref_type", {"name" : "Subject relation to victim/case", "code": "SUB_REL", "description": "Relationship of the subject persont to the victim or the case"})
    seed_ref(ref_type_id, [["AD", "Adopted"],
                           ["AU", "Biological Aunt/Uncle"],
                           ["BP", "Biological Parent"],
                           ["DCF", "DCF Home"],
                           ["FOS", "Foster"],
                           ["GP", "Grandparent"],
                           ["SIB", "Sibling"],
                           ["SPAR", "Step-parent"],
                           ["AC", "Acquaintance"],
                           ["BGF", "Boyfriend/Girlfriend"],
                           ["FACF", "Facility Friend"],
                           ["FAMF", "Family Friend"],
                           ["FR", "Friend"],
                           ["NB", "Neighbor"],
                           ["OA", "Other Adult"],
                           ["SM", "Schoolmate"],
                           ["SMF", "Social Media Friend"],
                           ["SP", "Spouse"],
                           ["UNK", "Unknown"],
                           ["OTH", "Other"]])

    ref_type_id: int = seed("ref_type", {"name" : "Team Role", "code": "TEAM_ROLE", "description": "Role of a Shepherds volunteer on a team"})
    seed_ref(ref_type_id, [["LEAD", "Leader", "100"],
                           ["ASST", "Assistant Leader", "200"],
                           ["CADV", "Case Advocate", "300"],
                           ["INTEL", "Lead Analyst", "400"],
                           ["OO", "OSINT/Operations", "500"],
                           ["MIN", "Ministry", "600"]])

    ref_type_id: int = seed("ref_type", {"name" : "Yes/No/Unk", "code": "YNU", "description": "Boolean with uncertainty"})
    seed_ref(ref_type_id, [["Y", "Yes"], ["N", "No"], ["U", "Unknown"]])

    ref_type_id: int = seed("ref_type", {"name" : "Yes/No/Unk/Maybe", "code": "YNUM", "description": "Boolean with unknown & maybe"})
    seed_ref(ref_type_id, [["Y", "Yes"], ["N", "No"], ["NA", "N/A"], ["U", "Unknown"], ["M", "Maybe"]])

    ref_type_id: int = seed("ref_type", {"name" : "Mobile Carrier", "code": "MOBILE", "description": "Mobile carrier vendor"})
    seed_ref(ref_type_id, [["ATT", "AT&T"],
                           ["SPR", "Sprint"],
                           ["TMO", "T-Mobile"],
                           ["VZ", "Verizon"],
                           ["BST", "Boost"],
                           ["MET", "Metro PCS"],
                           ["TRC", "Tracfone"],
                           ["MINT", "Mint Mobile"],
                           ["OTH", "Other"]])

    ref_type_id: int = seed("ref_type", {"name" : "Voice Over IP", "code": "VOIP", "description": "VOIP Vendor"})
    seed_ref(ref_type_id, [["FB", "Facebook"],
                           ["IG", "Instagram"],
                           ["VO", "Vonage"],
                           ["TN", "Text Now"],
                           ["GH", "Grasshopper"],
                           ["GV", "Google Voice"],
                           ["ZM", "Zoom"],
                           ["GM", "Google Meet"],
                           ["Oth", "Other"]])

    ref_type_id: int = seed("ref_type", {"name" : "CSEC", "code": "CSEC", "description": "Commercial Sexual Exploitation of a Child"})
    seed_ref(ref_type_id, [["CON", "Confirmed"],
                           ["IND", "Indicators"],
                           ["N", "No"],
                           ["SUS", "Suspected"],
                           ["UNK", "Unknown"]])

    ref_type_id: int = seed("ref_type", {"name" : "Missing Status", "code": "MSTAT", "description": ""})
    seed_ref(ref_type_id, [["END", "Endangered"],
                           ["RUN", "Runaway"],
                           ["UNK", "Unknown"]])

    ref_type_id: int = seed("ref_type", {"name" : "Missing Classification", "code": "MCLASS", "description": ""})
    seed_ref(ref_type_id, [["EXP", "Endangered"],
                           ["INV", "Involuntary"],
                           ["LAB", "Labor"],
                           ["NON", "None"],
                           ["UNK", "Unknown"]])

    ref_type_id: int = seed("ref_type", {"name" : "Search Urgency Age", "code": "SU_AGE", "description": "Subject's age"})
    seed_ref(ref_type_id, [["PRE", "Pre-teen (7-12)", "1"],
                           ["TEEN", "Teen (13-16)", "2"],
                           ["TA", "Teen/Adault (17+)", "3"]])

    ref_type_id: int = seed("ref_type", {"name" : "Search Urgency Fitness", "code": "SU_FIT", "description": "Subject's physical fitness"})
    seed_ref(ref_type_id, [["UNF", "Unfit", "1"],
                           ["FIT", "Fit", "2"],
                           ["VF", "Very Fit", "3"]])

    ref_type_id: int = seed("ref_type", {"name" : "Search Urgency Medical Condition", "code": "SU_MED", "description": "Subject's medical condition"})
    seed_ref(ref_type_id, [["ILL", "Known illness requiring medication", "1"],
                           ["SPEC", "Special needs/Cognitive delay", "1"],
                           ["SUS", "Suspected illness or injury", "2"],
                           ["H", "Healthy", "3"]])

    ref_type_id: int = seed("ref_type", {"name" : "Search Urgency Risk", "code": "SU_RISK", "description": "Subject's personal risk factors"})
    seed_ref(ref_type_id, [["EXPL", "Known history of molestation/exploitation", "1"],
                           ["SUI", "Despondent/suicidal ideation", "1"],
                           ["DRUG", "Drug or gang involvement", "2"],
                           ["RUN", "History of running away", "3"],
                           ["N", "No known history of risk", "4"]])

    ref_type_id: int = seed("ref_type", {"name" : "Search Urgency Online Risk", "code": "SU_ONL", "description": "Subject's online risk factors"})
    seed_ref(ref_type_id, [["EXPL", "Known online exploitation/extorsion/grooming", "1"],
                           ["SEX", "Known online sexual activity", "1"],
                           ["SUS", "Suspected exploitation or grooming", "2"],
                           ["N", "No known history of risk", "3"]])

    ref_type_id: int = seed("ref_type", {"name" : "Search Family Dynamics", "code": "SU_FAM", "description": "Subject's family dynamics"})
    seed_ref(ref_type_id, [["LE", "Law Enforcement/Social Services involvement", "1"],
                           ["DRUG", "Drug or Gang involvement by family", "1"],
                           ["AB", "Suspected family abuse", "2"],
                           ["TRAU", "Recent trauma or loss", "2"],
                           ["CHA", "Recent changes in family structure", "2"],
                           ["N", "No identified risk factors within family", "3"]])

    ref_type_id: int = seed("ref_type", {"name" : "Search Behavioral", "code": "SU_BE", "description": "Subject's behavioral risk factors"})
    seed_ref(ref_type_id, [["FR", "Recent negative change in friends/peer group", "1"],
                           ["SN", "Sneaking out or sneaking friends in the house", "1"],
                           ["SB", "Secretive behaviors/hiding phone activity", "2"],
                           ["ANG", "Increasing anger/explosive behavior", "2"],
                           ["SEX", "Questioning sexuality/aggressive sexual behavior", "2"],
                           ["N", "No identified behavioral", "3"]])

    ref_type_id: int = seed("ref_type", {"name" : "Social Media Status", "code": "SM_STAT", "description": "Status of social media account"})
    seed_ref(ref_type_id, [["NA", "Not Applicable"],
                           ["NF", "Not found"],
                           ["OA", "Open/Active"],
                           ["OI", "Open/Inactive"],
                           ["P", "Private"]])

    ref_type_id: int = seed("ref_type", {"name" : "Alias Status", "code": "SM_ALIAS", "description": "Status of alias drop"})
    seed_ref(ref_type_id, [["NA", "Not Applicable"],
                           ["NF", "Waiting (Alias dropped)"],
                           ["R", "Alias rejected"],
                           ["OA", "Alias accepted"],
                           ["OI", "Monitoring"]])

    ref_type_id: int = seed("ref_type", {"name" : "Social Media Investigated", "code": "SM_INV", "description": "Progress of social media investigation"})
    seed_ref(ref_type_id, [["CL", "Confirmed as NOT the person"],
                           ["CONF", "Confirmed as the person"],
                           ["UNC", "Unconfirmed"],
                           ["UNK", "Unknown"]])

    ref_type_id: int = seed("ref_type", {"name" : "Activity source", "code": "ACT_SOURCE", "description": "Source of intelligence from OSINT activity"})
    seed_ref(ref_type_id, [["BV", "Been Verified"],
                           ["CAM", "Cameras"],
                           ["FAM", "Family"],
                           ["IDI", "IDi"],
                           ["INT", "Interview"],
                           ["IS", "Internet Search"],
                           ["LE", "Law Enforcement"],
                           ["NEWS", "News Report"],
                           ["SN", "Skopenow"],
                           ["SL", "Spotlight"],
                           ["TEL", "Telephone call"],
                           ["TEX", "Text Message"],
                           ["TIP", "Tip"],
                           ["TV", "TV"],
                           ["Oth", "Other"]])

    ref_type_id: int = seed("ref_type", {"name" : "Activity reported to", "code": "ACT_REP", "description": "Who was intelligence reported to?"})
    seed_ref(ref_type_id, [["BV", "Incident Commander"],
                           ["CAM", "Mapping"],
                           ["FAM", "Ops Chief"],
                           ["IDI", "Plans Chief"],
                           ["INT", "Brad"],
                           ["IS", "Shannon"],
                           ["LE", "Law Enforcement"],
                           ["NEWS", "Case Lead"],
                           ["Oth", "Other"]])

    ref_type_id: int = seed("ref_type", {"name" : "Timeline entry type", "code": "TL_TYPE", "description": "Type of timeline entry."})
    seed_ref(ref_type_id, [["F", "Fact"],
                           ["T", "Tip"],
                           ["R", "Rumor"],
                           ["OTH", "Other"]])

    ref_type_id: int = seed("ref_type", {"name" : "Operation type", "code": "OP_TYPE", "description": "Type of operation."})
    seed_ref(ref_type_id, [["CC", "Community Contact)"],
                           ["KT", "Knock & Talk"],
                           ["M", "Ministry"],
                           ["O", "Overwatch"],
                           ["R", "Reconnaissance"],
                           ["OTH", "Other"]])

    ref_type_id: int = seed("ref_type", {"name" : "Operation Subject Legal", "code": "OP_SUB_LEG", "description": "LE status of subject person"})
    seed_ref(ref_type_id, [["JC", "Juvenile OTTIC Criminal offenses)"],
                           ["JN", "Juvenile OTTIC non-criminal"],
                           ["W", "Adult warrant"],
                           ["N", "No warrant"]])

    ref_type_id: int = seed("ref_type", {"name" : "Communications channel", "code": "OP_COMMS", "description": "Comms channel for operation."})
    seed_ref(ref_type_id, [["1", "1"],
                           ["2", "2"],
                           ["3", "3"],
                           ["4", "4"],
                           ["5", "5"],
                           ["6", "6"],
                           ["7", "7"]])

    ref_type_id: int = seed("ref_type", {"name" : "Operation assignment", "code": "OP_ROLE", "description": "Operation role."})
    seed_ref(ref_type_id, [["TL", "Team Lead"],
                           ["SO", "Safety Officer"],
                           ["MED", "Medic"],
                           ["IO", "Intel/Ops"],
                           ["MIN", "Ministry"],
                           ["OTH", "Other"]])

    vc_id:int = seed("victimology_category", {"category": "General Questions", "sort_order": 1})
    seed("victimology", [
        {"victimology_category_id": vc_id, "sort_order": 1, "question": "Do neighbors have cameras?", "follow_up": "Location? Address? Contacts?"},
        {"victimology_category_id": vc_id, "sort_order": 2, "question": "Have they run before?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 3, "question": "Has there been a note found?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 4, "question": "Do they have favorite places they like to go, or eat, hangout at?", "follow_up": ""}])

    vc_id:int = seed("victimology_category", {"category": "Are there any known", "sort_order": 2})
    seed("victimology", [
        {"victimology_category_id": vc_id, "sort_order": 1, "question": "Mental health issues?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 2, "question": "Medical issues?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 3, "question": "Prescription medications?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 4, "question": "Is your child Sexually Active?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 5, "question": "Illicit drugs or Alcohol?", "follow_up": ""}])

    vc_id:int = seed("victimology_category", {"category": "Have they experienced", "sort_order": 3})
    seed("victimology", [
        {"victimology_category_id": vc_id, "sort_order": 1, "question": "Any sort of trauma", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 2, "question": "Major catastrophy i.e. fire, MVA, Severe injury, natural disaster", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 3, "question": "Loss of a loved one", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 4, "question": "Break up", "follow_up": "With whom?"},
        {"victimology_category_id": vc_id, "sort_order": 5, "question": "Abuse", "follow_up": ""}])

    vc_id:int = seed("victimology_category", {"category": "Behavior", "sort_order": 4})
    seed("victimology", [
        {"victimology_category_id": vc_id, "sort_order": 1, "question": "Have they ever talked about  hurting themselves?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 2, "question": "Any changes in behavior; more docile, more unwilling to disagree or make eye contact?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 3, "question": "Have they been acting recklessly or overly aggressive lately?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 4, "question": "Have they been withdrawing from activities they were fond of, or been spending less time with friends than is normal?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 5, "question": "Have their sleeping habits changed; are they sleeping too much or too little?", "follow_up": ""}])

    vc_id:int = seed("victimology_category", {"category": "Is it possible", "sort_order": 5})
    seed("victimology", [
        {"victimology_category_id": vc_id, "sort_order": 1, "question": "They may have used any electronics they have access to, for interacting with someone that you have never met, or are unaware of?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 2, "question": "Your child has received or transmitted sexual images on the internet?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 3, "question": "They had been sexually exploited/trafficked in the past?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 4, "question": "Do they have friends/ acquaintances who may have been exploited/trafficked?", "follow_up": "Who?"},
        {"victimology_category_id": vc_id, "sort_order": 5, "question": "Have they been showing up with items (phones, clothing, make up, etc) that they do not seem to have the money to buy themselves?", "follow_up": ""}])

    vc_id:int = seed("victimology_category", {"category": "Interests and Likes", "sort_order":6})
    seed("victimology", [
        {"victimology_category_id": vc_id, "sort_order": 1, "question": "Are they a gamer?", "follow_up": "What games?"},
        {"victimology_category_id": vc_id, "sort_order": 2, "question": "Goth, cheerleader, artsy, outdoorsy?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 3, "question": "Do they belong to any clubs?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 4, "question": "Free spirit, questioning/confused over their sexuality?", "follow_up": ""},
        {"victimology_category_id": vc_id, "sort_order": 5, "question": "Have they ever mentioned places they would like to travel to?", "follow_up": ""}])


    seed("qualification", [
        {"name": "Fundamentals"},
        {"name": "Case Advocacy"},
        {"name": "OSINT Analyst"},
        {"name": "Operations"},
        {"name": "Tactical Operations Center"},
        {"name": "FBI Background Check"},
        {"name": "Concealed Carry Permit"},
        {"name": "Stop The Bleed"},
        {"name": "FEMA IS-100"},
        {"name": "FEMA IS-200"}
    ])

    role_id: int = seed("role", {"name": "Administration", "code": "ADMIN", "description": "Admin role."})

    org_id: int  = seed('organization', {"name": "Called2Rescue", "state_id": get_ref_value_id("STATE", "FL")})
    app_user_id = seed("app_user", {"email": "jsburton@gmail.com", "password_hash": "$pbkdf2-sha256$29000$n1NqLSWEkPJeC4EQYqyVMg$DQ3w24lr3LDKF663lmBO4E1D6lB3x2ZWbdZhDNBjkfA", "is_active": True})
    seed("app_user_role", {"app_user_id": app_user_id, "role_id": role_id})

    # Try to load a local profile picture; if it doesn't exist, seed without it
    img_path = Path(__file__).parent / "jeff_burton_pfp.jpg"
    person_payload = {
        "first_name": "Jeff",
        "last_name": "Burton",
        "email": "jsburton@gmail.com",
        "phone": "7152225655",
        "telegram": "jeffburton",
        "organization_id": org_id,
        "app_user_id": app_user_id,
    }
    if img_path.exists():
        with img_path.open("rb") as f:
            person_payload["profile_pic"] = f.read()
    seed("person", person_payload);



    seed("system_setting", {"name": "system_email", "value" : "jsburton@gmail.com"})
    seed("system_setting", {"name": "system_telegram_api_id", "value" : "22078170"})
    seed("system_setting", {"name": "system_telegram_api_hash", "value" : "ed21b3193c355e1ca5e7e5000ea36fbb"})
    seed("system_setting", {"name": "system_telegram_session", "value" : "1AZWarzgBu4hkWEoJzKphEIinzYE7Lf7abjok7VYvQaHfgnTTQaynlA-7-ukdYC0Rv9sSKLqLzCPMZjEpcHcFpjpzHVd6gCSw8WKBLvz15MsEdBlnp1CiexzAaM573DOBscOD_YAEjU2X9vydGvjNfN8WYTl8i5D_pRua1q0gLbXjIzE60ZsiNagcMfAt1tf5Dkf9rDI282sKO2ofOvGPNhRrjmoTFwL7aaTjz7k98QoMzk87DLYFY2bdu2Per5ITyD9ipfjZcbl1Xpvy_IgfVMSt1ClKmiNsAbtmaLlHvTtMjEZ8KSWbnRFPIRQgtR_v09kV6WUVvj1yf45z4QLZfQmCjCze9_s="})


    leader_role_id:int = seed("role", {"name": "Leadership", "code": "LEADER", "description": "Can see all cases and organize teams."})
    member_role_id: int = seed("role", {"name": "Team Member", "code": "MEMBER", "description": "Member of a team, can see assigned cases."})
    outside_role_id: int = seed("role", {"name": "Outside", "code": "OUTSIDE", "description": "Outside organization, limited permissions."})

    perm_id :int = seed("permission", {"name": "Admin panel", "code": "ADMIN", "description": "Administration panel."})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "Teams", "code": "TEAMS", "description": "Show teams."})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": leader_role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": member_role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "Teams", "code": "TEAMS.MODIFY", "description": "Add/change teams."})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "Organizations", "code": "ORGS", "description": "Edit organizations."})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "Qualifications", "code": "QUALIFICATIONS", "description": "Edit qualifications."})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "ER's/Trauma Centers", "code": "HOSPITAL_ER", "description": "Edit hospital ER's/Trauma Centers."})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "RFI Sources", "code": "RFI_SOURCES", "description": "Edit RFI sources"})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})

    perm_id :int = seed("permission", {"name": "Events", "code": "EVENTS", "description": "Search events"})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": leader_role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": member_role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "Modify Events", "code": "EVENTS.MODIFY", "description": "Add/change events"})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})


    perm_id :int = seed("permission", {"name": "Contacts", "code": "CONTACTS", "description": "Contacts"})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": leader_role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": member_role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "Modify Contacts", "code": "CONTACTS.MODIFY", "description": "Add/change contacts"})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": leader_role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": member_role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "Modify Contacts", "code": "CONTACTS.ALL_SUBJECTS", "description": "Add/change contacts"})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})


    perm_id :int = seed("permission", {"name": "Cases", "code": "CASES", "description": "Cases"})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": leader_role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": member_role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "Modify Cases", "code": "CASES.MODIFY", "description": "Add/change cases"})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": leader_role_id, "permission_id": perm_id})
    seed("role_permission", {"role_id": member_role_id, "permission_id": perm_id})
    perm_id :int = seed("permission", {"name": "See All Cases", "code": "CASES.ALL_CASES", "description": "See all cases"})
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})