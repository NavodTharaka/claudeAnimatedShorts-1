import json, sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
R = Path(__file__).resolve().parent.parent
yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file(str(R / "token.json")))
NEW = {
"g_5x_OdNryM":"Why Do We Get Allergies? The Immune System's False Alarm",
"tSQ9Vb-dV0s":"Why Your Body Attacks Harmless Things (Allergies Explained)",
"4BbWs3vAr_g":"Why Your Body Attacks Harmless Things (Allergies Explained) Part 2",
"wvWvo-bK4AQ":"Why Your Body Attacks Harmless Things (Allergies Explained) Part 3",
"9MrlEkFYXwM":"Why Your Body Attacks Harmless Things (Allergies Explained) Part 4",
"LUlsJxItpDE":"What Happens To Your Body While You Sleep?",
"kRJoPozMx5Y":"What Happens In Your Body During Deep Sleep?",
"_KwXqepNOYI":"Why Your Body Repairs Itself While You Sleep",
"3tyQSQJpFfg":"What Does Your Immune System Do While You Sleep?",
"zf6JF-f3jAY":"Why Is Your Brain Still Active When You Sleep?",
"asXV8O0h9B0":"How Does Your Body Clock Control Your Sleep?",
"v1zJ41Mu_mI":"Why Do We Forget Things? What Happens In Your Brain",
"IDckHpZDHuQ":"What Happens Inside Your Body When a Virus Attacks?",
"YvJ95FkrENc":"Why Does Your Body Get a Fever When You're Sick?",
"NWI86n1Wd-U":"Why Do You Feel So Tired When You're Sick?",
"_vxZtnnCRmQ":"Why Do You Get So Much Mucus When You're Sick?",
"7Ob1ktDjQLs":"How Does Your Body Recover After Being Sick?",
"SaaPec31rHM":"What Happens Inside Your Mouth When You Eat?",
"ocAp_Dlnf84":"What Really Happens To Your Food In The Stomach?",
"yX10EEgBNmw":"Where Does Your Food Go After the Stomach?",
}
vs = yt.videos().list(part="snippet", id=",".join(NEW)).execute()["items"]
(R/"out/curion-report/title-backup.json").write_text(json.dumps({v["id"]: v["snippet"]["title"] for v in vs}, ensure_ascii=False, indent=1), encoding="utf-8")
for v in vs:
    s = v["snippet"]; old = s["title"]; s["title"] = NEW[v["id"]]
    for k in ("thumbnails","channelTitle","localized","publishedAt","channelId","liveBroadcastContent"): s.pop(k, None)
    yt.videos().update(part="snippet", body={"id": v["id"], "snippet": s}).execute()
    print("OK", v["id"], "|", NEW[v["id"]].encode("ascii","replace").decode())
