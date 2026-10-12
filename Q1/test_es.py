import subprocess, requests, uuid, json, html
P = "project-314f93e3-d840-40fd-98d"
TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
H = {"Authorization": f"Bearer {TOKEN}", "x-goog-user-project": P}
URL = f"https://dialogflow.googleapis.com/v2/projects/{P}/agent/sessions/%s:detectIntent"
out = []
def convo(title, turns):
    sid = uuid.uuid4().hex[:12]
    out.append(f"\n===== {title} =====")
    for t in turns:
        q = requests.post(URL % sid, headers=H, json={"queryInput": {"text": {"text": t, "languageCode": "en"}}}).json().get("queryResult", {})
        bot = " ".join(" ".join(m["text"]["text"]) for m in q.get("fulfillmentMessages", []) if "text" in m) or q.get("fulfillmentText", "")
        out.append(f"USER: {t}\n   [intent: {q.get('intent',{}).get('displayName','?')} | conf {q.get('intentDetectionConfidence',0):.2f} | params {json.dumps(q.get('parameters',{}))}]\nBOT:  {bot}")
convo("1. Standard report -> review -> confirm", ["hi", "I want to report an issue", "energy waste", "Building A", "level 3 open-plan office", "ongoing", "yes", "that's all"])
convo("2. One-sentence report (annotated phrase pre-fills slots)", ["There is a water leak in Building C", "level 2 kitchen", "minor", "change it"])
convo("3. Branch: immediate danger -> urgent escalation", ["report a problem", "chemical spill", "car park", "near the loading dock", "someone could get hurt", "that's all"])
convo("4. Fallback and clarification", ["report an issue", "water leak", "Library", "ground floor toilets", "banana", "ongoing", "yes"])
convo("5. Off-topic then human handoff", ["what's the weather like", "talk to a person"])
convo("6. Sensitive conduct -> confidential referral", ["my manager keeps making jokes about my wheelchair"])
convo("7. Cancel mid-report", ["report an issue", "recycling", "cancel"])
txt = "\n".join(out)
open("transcripts.txt", "w").write(txt)
open("index.html", "w").write("<pre id='t'>" + html.escape(txt) + "</pre>")
print("TESTS DONE")
