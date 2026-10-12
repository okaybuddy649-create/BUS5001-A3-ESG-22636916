import subprocess, sys, time, requests
P = "project-314f93e3-d840-40fd-98d"
BASE = f"https://dialogflow.googleapis.com/v2/projects/{P}/agent"
TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
H = {"Authorization": f"Bearer {TOKEN}", "x-goog-user-project": P, "Content-Type": "application/json"}

def call(m, path, body=None, params=None):
    r = requests.request(m, f"{BASE}{path}", headers=H, json=body, params=params)
    if r.status_code >= 300:
        print("ERROR", m, path, r.status_code, r.text[:600]); sys.exit(1)
    return r.json() if r.text else {}

def ctx(name, life=5): return {"name": f"projects/{P}/agent/sessions/-/contexts/{name}", "lifespanCount": life}
def cname(name): return f"projects/{P}/agent/sessions/-/contexts/{name}"
def msgs(*t): return [{"text": {"text": [x]}} for x in t]

# clean slate: delete custom intents/entities from earlier runs
for it in call("GET", "/intents").get("intents", []):
    if not it["displayName"].startswith("Default"):
        call("DELETE", "/intents/" + it["name"].split("/")[-1])
for et in call("GET", "/entityTypes").get("entityTypes", []):
    call("DELETE", "/entityTypes/" + et["name"].split("/")[-1])

def entity(name, values):
    call("POST", "/entityTypes", {"displayName": name, "kind": "KIND_MAP", "enableFuzzyExtraction": False,
         "entities": [{"value": v, "synonyms": [v.lower()] + s} for v, s in values]})
entity("incident_type", [
    ("Water leak", ["water leak", "leak", "leaking", "leaking tap", "dripping tap", "burst pipe", "flooding", "water running"]),
    ("Energy waste", ["energy waste", "lights left on", "lights on", "air conditioning", "aircon", "air con", "heater left on", "equipment left running", "wasting power"]),
    ("Waste contamination", ["waste contamination", "contaminated recycling", "recycling contamination", "contaminated bins", "wrong bin", "overflowing bin", "recycling"]),
    ("Unsafe disposal", ["unsafe disposal", "chemical spill", "chemicals", "dumped chemicals", "batteries in the bin", "hazardous waste", "e-waste", "oil spill"]),
    ("Other facilities issue", ["other", "something else", "facilities issue", "other issue"]),
])
entity("building", [
    ("Building A", ["building a", "block a"]), ("Building B", ["building b", "block b"]),
    ("Building C", ["building c", "block c"]), ("Building D", ["building d", "block d"]),
    ("Library", ["library", "the library"]), ("Cafeteria", ["cafeteria", "canteen"]), ("Car park", ["car park", "carpark", "parking"]),
])
entity("hazard_level", [
    ("Immediate danger", ["immediate danger", "danger", "dangerous", "emergency", "someone could get hurt", "near electrics", "near the power board", "unsafe", "yes someone is at risk"]),
    ("Ongoing", ["ongoing", "still happening", "still running", "getting worse", "not dangerous but still happening"]),
    ("Minor", ["minor", "not urgent", "small", "low", "no rush", "just letting you know"]),
])
print("Entities created")

def tp(*phrases):
    out = []
    for p in phrases:
        if isinstance(p, str): out.append({"type": "EXAMPLE", "parts": [{"text": p}]})
        else: out.append({"type": "EXAMPLE", "parts": [{"text": t, **({"entityType": "@" + a, "alias": a, "userDefined": True} if a else {})} for t, a in p]})
    return out

def param(name, et, prompts, mandatory=True):
    return {"displayName": name, "value": "$" + name, "entityTypeDisplayName": et, "mandatory": mandatory, "prompts": prompts}

def intent(body): call("POST", "/intents", body); print(" +", body["displayName"])

# 1. Report start with slot filling
intent({"displayName": "report.start",
    "trainingPhrases": tp("I want to report an issue", "report an issue", "report a problem", "I need to log a sustainability issue",
        "log an incident", "start a report", "report another issue", "I want to make a report",
        [("There is a ", None), ("water leak", "incident_type"), (" in ", None), ("Building C", "building")],
        [("The ", None), ("air conditioning", "incident_type"), (" is running overnight in ", None), ("Building A", "building")],
        [("I want to report ", None), ("energy waste", "incident_type")],
        [("There's a ", None), ("chemical spill", "incident_type"), (" near the ", None), ("car park", "building")],
        [("Report a ", None), ("leaking tap", "incident_type"), (" in the ", None), ("library", "building")]),
    "parameters": [
        param("incident_type", "@incident_type", ["What kind of issue is it? You can say water leak, energy waste, waste contamination, unsafe disposal, or other facilities issue.",
 ]),
        param("building", "@building", ["Which building is it in? For example Building A, Building C, the Library or the Car park.",
 ]),
        param("location_detail", "@sys.any", ["Where exactly in that building? A floor, room or landmark is enough."]),
    ],
    "messages": msgs("Thanks. Is anyone at risk right now? Say 'immediate danger', 'ongoing' if it's still happening but safe, or 'minor'."),
    "outputContexts": [ctx("report", 10), ctx("awaiting_severity", 2)]})

# 2. Branch A: danger -> urgent escalation
intent({"displayName": "severity.danger", "inputContextNames": [cname("awaiting_severity")],
    "trainingPhrases": tp("immediate danger", "danger", "it's dangerous", "emergency", "someone could get hurt", "it's near the power board",
                          "yes someone is at risk", "it's unsafe", "water is near electrics", "people could slip"),
    "messages": msgs("This looks urgent. If anyone is in immediate danger, move away from the area and call 000 now.",
                     "I've flagged this as Priority 1 for the on-call Workplace Health and Safety and Facilities team: #report.incident_type at #report.building, #report.location_detail. They aim to respond within 1 hour.",
                     "Is there anything else? Say 'report another issue' or 'that's all'."),
    "outputContexts": [ctx("awaiting_severity", 0), ctx("report", 0), ctx("anything_else", 2)]})

# 3. Branch B: ongoing/minor -> review
intent({"displayName": "severity.routine", "inputContextNames": [cname("awaiting_severity")],
    "trainingPhrases": tp([("", None), ("ongoing", "hazard_level")], [("", None), ("minor", "hazard_level")], [("it's ", None), ("still happening", "hazard_level")],
                          [("", None), ("not urgent", "hazard_level")], [("it's ", None), ("minor", "hazard_level"), (" really", None)], [("", None), ("getting worse", "hazard_level")]),
    "parameters": [param("hazard_level", "@hazard_level", ["Is it ongoing or minor?"])],
    "messages": msgs("Here's your report. Issue: #report.incident_type. Location: #report.building, #report.location_detail. Severity: $hazard_level.",
                     "Shall I submit it? Say 'yes' to submit or 'change' to start again."),
    "outputContexts": [ctx("awaiting_severity", 0), ctx("awaiting_confirm", 2), ctx("report", 5)]})

# 4. Severity clarification fallback (context-specific)
intent({"displayName": "severity.fallback", "isFallback": True, "inputContextNames": [cname("awaiting_severity")],
    "messages": msgs("Sorry, I need to know how serious it is. Please say one of: immediate danger, ongoing, or minor."),
    "outputContexts": [ctx("awaiting_severity", 2), ctx("report", 10)]})

# 5. Confirm / change
intent({"displayName": "report.confirm", "inputContextNames": [cname("awaiting_confirm")],
    "trainingPhrases": tp("yes", "yes submit it", "confirm", "that's correct", "submit", "looks good", "yep send it", "correct", "yes please"),
    "messages": msgs("Thanks, your report has been submitted and routed to the team responsible for #report.incident_type issues. Ongoing issues are actioned within 24 hours and minor issues within 5 working days, and the report is included in the monthly ESG dashboard.",
                     "Is there anything else? Say 'report another issue' or 'that's all'."),
    "outputContexts": [ctx("awaiting_confirm", 0), ctx("report", 0), ctx("anything_else", 2)]})
intent({"displayName": "report.change", "inputContextNames": [cname("awaiting_confirm")],
    "trainingPhrases": tp("change it", "that's wrong", "no change it", "edit the report", "no that's not right", "change the details", "no"),
    "messages": msgs("No problem, I've cleared those details. Say 'report an issue' to start again."),
    "outputContexts": [ctx("awaiting_confirm", 0), ctx("report", 0)]})

# 6. Global intents: cancel, human, sensitive, end
intent({"displayName": "report.cancel", "resetContexts": True,
    "trainingPhrases": tp("cancel", "cancel my report", "forget it", "stop", "never mind", "cancel everything", "I don't want to report anymore"),
    "messages": msgs("Okay, I've cancelled that report and nothing was saved. Say 'report an issue' if you'd like to start again.")})
intent({"displayName": "agent.handoff", "resetContexts": True,
    "trainingPhrases": tp("talk to a person", "speak to a human", "can I talk to someone", "real person please", "connect me to staff", "I need a human"),
    "messages": msgs("I'll pass you to the Facilities Service Desk. Anything you've told me so far goes with you, so you won't need to repeat it.",
                     "You can also call the desk on extension 4400, Monday to Friday, 8am to 6pm.")})
intent({"displayName": "sensitive.conduct", "resetContexts": True,
    "trainingPhrases": tp("my manager is harassing me", "someone is bullying me at work", "I want to report a colleague's behaviour",
        "a coworker made discriminatory comments", "I'm being treated unfairly because of my disability", "I want to report misconduct",
        "my manager keeps making jokes about my wheelchair", "my supervisor keeps making jokes about me", "I feel unsafe around a colleague", "I want to make a whistleblower report"),
    "messages": msgs("Thank you for telling me. Concerns about a person's behaviour are handled confidentially by the Integrity and Ethics Office, not by this assistant, so I won't record any details here.",
                     "You can contact them through the confidential Speak Up line or portal, and you can choose to stay anonymous. If you are in danger, call 000.")})
intent({"displayName": "chat.end", "resetContexts": True, "endInteraction": True,
    "trainingPhrases": tp("that's all", "no thanks", "nothing else", "bye", "I'm done", "no that's it", "thanks bye"),
    "messages": msgs("Thanks for helping us reduce our environmental footprint. Have a good day.")})

# 7. Update defaults: welcome + fallback
for it in call("GET", "/intents", params={"intentView": "INTENT_VIEW_FULL"}).get("intents", []):
    iid = it["name"].split("/")[-1]
    if it["displayName"] == "Default Welcome Intent":
        call("PATCH", f"/intents/{iid}", {"displayName": it["displayName"], "messages": msgs(
            "Hi, I'm EcoReport, the sustainability incident assistant. I can log energy waste, water leaks, waste contamination, unsafe disposal or other facilities issues and send them to the right team. Please don't include personal details about other people. Say 'report an issue' to begin, or 'talk to a person' at any time.")},
            params={"updateMask": "messages"})
    if it["displayName"] == "Default Fallback Intent":
        call("PATCH", f"/intents/{iid}", {"displayName": it["displayName"], "messages": [{"text": {"text": [
            "Sorry, I didn't get that. I can help you report energy waste, a water leak, waste contamination, unsafe disposal or another facilities issue, or connect you to a person. What would you like to do?",
            "I'm not sure I understood. You can say 'report an issue', 'cancel', or 'talk to a person'."]}}]},
            params={"updateMask": "messages"})
print("Defaults updated")
call("POST", ":train"); time.sleep(25)
print("DONE")
