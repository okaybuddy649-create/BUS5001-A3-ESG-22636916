import json, subprocess, sys, requests

PROJECT = "project-314f93e3-d840-40fd-98d"
LOC = "australia-southeast1"
BASE = f"https://{LOC}-dialogflow.googleapis.com/v3"
PARENT = f"projects/{PROJECT}/locations/{LOC}"
TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "x-goog-user-project": PROJECT}

def call(method, path, body=None, params=None):
    r = requests.request(method, f"{BASE}/{path}", headers=H, json=body, params=params)
    if r.status_code >= 300:
        print("ERROR", method, path, r.status_code, r.text[:800]); sys.exit(1)
    return r.json() if r.text else {}

def msg(*lines):
    return {"messages": [{"text": {"text": [l]}} for l in lines]}

def ff(*lines, presets=None):
    f = msg(*lines) if lines else {}
    if presets:
        f["setParameterActions"] = [{"parameter": k, "value": v} for k, v in presets.items()]
    return f

# ---------- Agent ----------
existing = call("GET", f"{PARENT}/agents").get("agents", [])
agent = next((a for a in existing if a["displayName"] == "EcoReport ESG Incident Assistant"), None)
if agent:
    print("Agent already exists, deleting to rebuild cleanly")
    call("DELETE", agent["name"])
agent = call("POST", f"{PARENT}/agents", {
    "displayName": "EcoReport ESG Incident Assistant",
    "defaultLanguageCode": "en", "timeZone": "Australia/Melbourne",
    "description": "BUS5001 A3 Q1 - Sustainability incident reporting assistant (prototype)"})
A = agent["name"]; FLOW = agent["startFlow"]
print("Agent:", A)

# ---------- Entity types ----------
def entity(name, values):
    return call("POST", f"{A}/entityTypes", {
        "displayName": name, "kind": "KIND_MAP", "enableFuzzyExtraction": False,
        "entities": [{"value": v, "synonyms": [v.lower()] + s} for v, s in values]})["name"]

ET_TYPE = entity("incident_type", [
    ("Water leak", ["water leak", "leak", "leaking", "leaking tap", "dripping tap", "burst pipe", "flooding", "water running", "water"]),
    ("Energy waste", ["energy waste", "lights left on", "lights on", "air conditioning", "aircon", "air con", "heater left on", "heating on", "equipment left running", "wasting power", "energy"]),
    ("Waste contamination", ["waste contamination", "contaminated recycling", "recycling contamination", "contaminated bins", "wrong bin", "overflowing bin", "recycling", "rubbish"]),
    ("Unsafe disposal", ["unsafe disposal", "chemical spill", "chemicals", "dumped chemicals", "batteries in the bin", "hazardous waste", "e-waste", "oil spill", "chemical drums"]),
    ("Other facilities issue", ["other", "something else", "facilities issue", "other issue", "broken", "smell"]),
])
ET_BLD = entity("building", [
    ("Building A", ["building a", "block a", "a block"]),
    ("Building B", ["building b", "block b", "b block"]),
    ("Building C", ["building c", "block c", "c block"]),
    ("Building D", ["building d", "block d", "d block"]),
    ("Library", ["library", "the library"]),
    ("Cafeteria", ["cafeteria", "canteen", "food court"]),
    ("Car park", ["car park", "carpark", "parking"]),
])
ET_HAZ = entity("hazard_level", [
    ("Immediate danger", ["immediate danger", "danger", "dangerous", "emergency", "someone could get hurt", "near electrics", "near the power board", "unsafe", "yes someone is at risk"]),
    ("Ongoing", ["ongoing", "still happening", "still running", "getting worse", "it's ongoing", "not dangerous but still happening"]),
    ("Minor", ["minor", "not urgent", "small", "low", "no rush", "just letting you know"]),
])
SYS_ANY = "projects/-/locations/-/agents/-/entityTypes/sys.any"
print("Entities created")

# ---------- Intents ----------
def intent(name, phrases, desc, params=None):
    tps = []
    for p in phrases:
        if isinstance(p, str):
            tps.append({"parts": [{"text": p}], "repeatCount": 1})
        else:  # annotated phrase: list of (text, param_or_None)
            tps.append({"parts": [{"text": t, **({"parameterId": pid} if pid else {})} for t, pid in p], "repeatCount": 1})
    body = {"displayName": name, "description": desc, "trainingPhrases": tps}
    if params: body["parameters"] = params
    return call("POST", f"{A}/intents", body)["name"]

I_START = intent("report.start", [
    "I want to report an issue", "report an issue", "report a problem", "I need to log a sustainability issue",
    "I'd like to report something", "log an incident", "start a report", "report another issue", "I want to make a report",
    "something needs fixing",
    [("There is a ", None), ("water leak", "incident_type"), (" in ", None), ("Building C", "building")],
    [("The ", None), ("air conditioning", "incident_type"), (" is running overnight in ", None), ("Building A", "building")],
    [("The recycling bins are ", None), ("contaminated", None), (" again", None)],
    [("I want to report ", None), ("energy waste", "incident_type")],
    [("There's a ", None), ("chemical spill", "incident_type"), (" near the ", None), ("car park", "building")],
    [("Report a ", None), ("leaking tap", "incident_type"), (" in the ", None), ("library", "building")],
], "User wants to report a sustainability or facilities incident",
   params=[{"id": "incident_type", "entityType": ET_TYPE}, {"id": "building", "entityType": ET_BLD}])
I_CONFIRM = intent("report.confirm", ["yes", "yes submit it", "confirm", "that's correct", "submit", "looks good", "yep send it", "correct", "yes please"],
                   "User confirms the report summary")
I_CHANGE = intent("report.change", ["change it", "that's wrong", "no change it", "edit the report", "I need to fix something", "no that's not right", "change the details"],
                  "User wants to correct the report")
I_CANCEL = intent("report.cancel", ["cancel", "cancel my report", "forget it", "stop", "never mind", "cancel everything", "I don't want to report anymore"],
                  "User cancels the report at any point")
I_HUMAN = intent("agent.handoff", ["talk to a person", "speak to a human", "can I talk to someone", "real person please", "connect me to staff", "I need a human", "call someone"],
                 "User asks for a human at any point")
I_SENS = intent("sensitive.conduct", ["my manager is harassing me", "someone is bullying me at work", "I want to report a colleague's behaviour",
                 "a coworker made discriminatory comments", "I'm being treated unfairly because of my disability", "I want to report misconduct",
                 "my supervisor keeps making jokes about me", "I feel unsafe around a colleague", "I want to report fraud", "I want to make a whistleblower report"],
                "Sensitive conduct or governance concern - must be referred, not recorded")
I_END = intent("chat.end", ["that's all", "no thanks", "nothing else", "bye", "I'm done", "no that's it", "thanks bye"], "User ends the conversation")
print("Intents created")

# ---------- Pages (create shells, then fill) ----------
names = ["Welcome", "Incident Details", "Review Report", "Urgent Escalation", "Report Logged", "Cancelled", "Human Handoff", "Confidential Referral"]
P = {n: call("POST", f"{FLOW}/pages", {"displayName": n})["name"] for n in names}
END = f"{FLOW}/pages/END_SESSION"
CLEAR = {"incident_type": None, "building": None, "location_detail": None, "hazard_level": None, "assigned_team": None, "priority": None}

def patch_page(n, body):
    call("PATCH", P[n], dict(displayName=n, **body),
         params={"updateMask": ",".join(k for k in body)})

patch_page("Welcome", {
    "entryFulfillment": ff("Hi, I'm EcoReport, the sustainability incident assistant. I can log energy waste, water leaks, waste contamination, unsafe disposal or other facilities issues and send them to the right team.",
                           "Please don't include personal details about other people. Say 'report an issue' to begin, or 'talk to a person' at any time."),
    "transitionRoutes": [{"intent": I_START, "targetPage": P["Incident Details"]}]})

def form_param(name, entity_type, prompt, nm1, nm2, required=True):
    return {"displayName": name, "entityType": entity_type, "required": required,
            "fillBehavior": {"initialPromptFulfillment": msg(prompt),
                             "repromptEventHandlers": [
                                 {"event": "sys.no-match-1", "triggerFulfillment": msg(nm1)},
                                 {"event": "sys.no-match-2", "triggerFulfillment": msg(nm2)},
                                 {"event": "sys.no-match-3", "triggerFulfillment": msg("I'm having trouble understanding, so I'll pass you to a person who can help."), "targetPage": P["Human Handoff"]},
                                 {"event": "sys.no-input-1", "triggerFulfillment": msg("Are you still there? " + prompt)}]}}

patch_page("Incident Details", {
    "form": {"parameters": [
        form_param("incident_type", ET_TYPE,
                   "What kind of issue is it? You can say water leak, energy waste, waste contamination, unsafe disposal, or other facilities issue.",
                   "Sorry, I didn't catch the type of issue. Is it a water leak, energy waste, waste contamination, unsafe disposal, or something else?",
                   "Let's try one word: water, energy, recycling, chemicals, or other?"),
        form_param("building", ET_BLD,
                   "Which building is it in? For example Building A, Building C, the Library or the Car park.",
                   "I didn't recognise that building. Our sites are Buildings A to D, the Library, the Cafeteria and the Car park. Which one?",
                   "Please say just the building name, for example 'Building C'."),
        form_param("location_detail", SYS_ANY,
                   "Where exactly in that building? A floor, room or landmark is enough.",
                   "Just a floor or room number is fine.", "For example 'level 2 kitchen'."),
        form_param("hazard_level", ET_HAZ,
                   "Is anyone at risk right now? Say 'immediate danger', 'ongoing' if it's still happening but safe, or 'minor'.",
                   "Sorry, how serious is it: immediate danger, ongoing, or minor?",
                   "Please choose one: danger, ongoing, or minor."),
    ]},
    "transitionRoutes": [
        {"condition": '$page.params.status = "FINAL" AND $session.params.hazard_level = "Immediate danger"', "targetPage": P["Urgent Escalation"]},
        {"condition": '$page.params.status = "FINAL" AND $session.params.incident_type = "Unsafe disposal"', "targetPage": P["Urgent Escalation"]},
        {"condition": '$page.params.status = "FINAL"', "targetPage": P["Review Report"]},
    ]})

TEAMS = {"Water leak": "Facilities Maintenance", "Energy waste": "Energy and Sustainability Office",
         "Waste contamination": "Waste Services", "Other facilities issue": "Facilities Maintenance"}
confirm_routes = [{"intent": I_CONFIRM, "condition": f'$session.params.incident_type = "{t}"',
                   "triggerFulfillment": ff(presets={"assigned_team": team, "priority": "P2"}),
                   "targetPage": P["Report Logged"]} for t, team in TEAMS.items()]
patch_page("Review Report", {
    "entryFulfillment": ff("Here's your report. Issue: $session.params.incident_type. Location: $session.params.building, $session.params.location_detail. Severity: $session.params.hazard_level.",
                           "Shall I submit it? Say 'yes' to submit or 'change' to edit."),
    "transitionRoutes": confirm_routes + [
        {"intent": I_CHANGE, "triggerFulfillment": ff("No problem, let's go through it again.", presets=CLEAR), "targetPage": P["Incident Details"]}]})

patch_page("Urgent Escalation", {
    "entryFulfillment": ff("This looks urgent. If anyone is in immediate danger, move away from the area and call 000 now.",
                           "I've flagged this as Priority 1 for the on-call Workplace Health and Safety and Facilities team: $session.params.incident_type at $session.params.building, $session.params.location_detail. They aim to respond within 1 hour.",
                           "Is there anything else? Say 'report another issue' or 'that's all'.",
                           presets={"assigned_team": "Workplace Health and Safety (on-call)", "priority": "P1"}),
    "transitionRoutes": [
        {"intent": I_START, "triggerFulfillment": ff(presets=CLEAR), "targetPage": P["Incident Details"]},
        {"intent": I_END, "triggerFulfillment": ff("Thanks for reporting this quickly. Stay safe."), "targetPage": END}]})

patch_page("Report Logged", {
    "entryFulfillment": ff("Thanks, your report has been submitted to the $session.params.assigned_team team. Ongoing issues are actioned within 24 hours and minor issues within 5 working days, and the report is included in the monthly ESG dashboard.",
                           "Is there anything else? Say 'report another issue' or 'that's all'."),
    "transitionRoutes": [
        {"intent": I_START, "triggerFulfillment": ff(presets=CLEAR), "targetPage": P["Incident Details"]},
        {"intent": I_END, "triggerFulfillment": ff("Thanks for helping us reduce our environmental footprint. Have a good day."), "targetPage": END}]})

patch_page("Cancelled", {
    "entryFulfillment": ff("Okay, I've cancelled that report and nothing was saved.", presets=CLEAR),
    "transitionRoutes": [{"condition": "true", "targetPage": END}]})

patch_page("Human Handoff", {
    "entryFulfillment": ff("I'll pass you to the Facilities Service Desk. Anything you've told me so far goes with you, so you won't need to repeat it.",
                           "You can also call the desk on extension 4400, Monday to Friday, 8am to 6pm."),
    "transitionRoutes": [{"condition": "true", "targetPage": END}]})

patch_page("Confidential Referral", {
    "entryFulfillment": ff("Thank you for telling me. Concerns about a person's behaviour are handled confidentially by the Integrity and Ethics Office, not by this assistant, so I won't record any details here.",
                           "You can contact them through the confidential Speak Up line or portal, and you can choose to stay anonymous. If you are in danger, call 000.",
                           presets=CLEAR),
    "transitionRoutes": [{"condition": "true", "targetPage": END}]})
print("Pages built")

# ---------- Start Page / flow-level routes and handlers ----------
flow = call("GET", FLOW)
routes = flow.get("transitionRoutes", [])
for r in routes:
    if r.get("intent", "").endswith("00000000-0000-0000-0000-000000000000"):
        r.pop("targetFlow", None); r["targetPage"] = P["Welcome"]; r.pop("triggerFulfillment", None)
routes += [
    {"intent": I_START, "targetPage": P["Incident Details"]},
    {"intent": I_CANCEL, "targetPage": P["Cancelled"]},
    {"intent": I_HUMAN, "targetPage": P["Human Handoff"]},
    {"intent": I_SENS, "targetPage": P["Confidential Referral"]},
]
handlers = [
    {"event": "sys.no-match-default", "triggerFulfillment": msg(
        "Sorry, I didn't get that. I can help you report energy waste, a water leak, waste contamination, unsafe disposal or another facilities issue, or connect you to a person. What would you like to do?")},
    {"event": "sys.no-input-default", "triggerFulfillment": msg("Are you still there? Say 'report an issue' or 'talk to a person'.")},
]
call("PATCH", FLOW, {"transitionRoutes": routes, "eventHandlers": handlers},
     params={"updateMask": "transitionRoutes,eventHandlers"})
print("Flow routes set")
print("DONE. Open: https://conversational-agents.cloud.google.com/projects/%s/locations/%s/agents/%s" % (PROJECT, LOC, A.split('/')[-1]))
