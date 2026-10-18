"""Single source of truth for the SubFree UK doorbell table.
Generates data/doorbells.csv, data/doorbells.md and the site (index.html + doorbells.html at the repo root) from ROWS below.
Run from anywhere: python3 build/build.py
"""
import csv, html, json
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
HERE = os.path.dirname(os.path.abspath(__file__))

CHECKED = "18 October 2026"
CARD = 10.00   # ASSUMPTION (not cited): typical price of a 64 GB microSD card / USB stick
MONTHS = 36

# Shared sources (footnote numbers are assigned automatically)
S = {
 "ring_plans": ("Ring UK plans", "https://en-uk.ring.com/pages/plans/"),
 "ring_prod": ("Ring UK: Battery Doorbell 2K", "https://en-uk.ring.com/products/battery-doorbell-2nd-gen"),
 "indy_ring": ("The Independent, Feb 2026", "https://www.independent.co.uk/home-improvement/ring-video-doorbell-subscription-without-b2915224.html"),
 "ha_ring": ("Home Assistant: Ring", "https://www.home-assistant.io/integrations/ring/"),
 "nest_prod": ("Google Store UK: Nest Doorbell", "https://store.google.com/gb/product/nest_doorbell_battery?hl=en-GB"),
 "nest_prem": ("Google Home Premium UK", "https://store.google.com/gb/product/google_home_premium?hl=en-GB"),
 "ha_nest": ("Home Assistant: Nest", "https://www.home-assistant.io/integrations/nest/"),
 "eufy_prod": ("eufy UK: E340", "https://www.eufy.com/uk/products/T8214311"),
 "eufy_cloud": ("eufy UK cloud plans", "https://www.eufy.com/uk/cloud-storage"),
 "verge_eufy": ("The Verge, Nov 2022", "https://www.theverge.com/2022/11/30/23486753/anker-eufy-security-camera-cloud-private-encryption-authentication-storage"),
 "sha_nosub": ("smarthomeassistant.co.uk guide", "https://smarthomeassistant.co.uk/articles/smart-security/best-video-doorbell-no-subscription-uk"),
 "reo_store": ("Reolink UK store", "https://store.reolink.com/gb/video-doorbells/"),
 "reo_batt": ("Reolink UK battery doorbells", "https://store.reolink.com/gb/wireless-doorbell-camera/"),
 "screwfix_reo": ("Screwfix: Reolink Battery", "https://www.screwfix.com/p/reolink-d340b-wired-or-wireless-battery-video-doorbell-black/471ak"),
 "reo_cloud": ("Reolink Cloud plans (EU)", "https://reolink.com/blog/reolink-cloud-in-europa-und-uk/"),
 "ha_reo": ("Home Assistant: Reolink", "https://www.home-assistant.io/integrations/reolink/"),
 "tapo_d230": ("Tapo UK: D230S1", "https://uk.store.tapo.com/products/tapo-d230s1-smart-battery-video-doorbell"),
 "tapo_td21": ("Tapo UK: TD21", "https://uk.store.tapo.com/products/battery-video-doorbell-2k-3mp-colour-night-vision-tapo-td21"),
 "tapo_care": ("Tapo Care UK", "https://uk.store.tapo.com/pages/tapo-care"),
 "ha_tapo": ("HA community forum", "https://community.home-assistant.io/t/tapo-d230-video-stream-in-ha/858436"),
 "er_tapo": ("Expert Reviews: EZVIZ EP3x Pro review", "https://www.expertreviews.co.uk/technology/home-security/ezviz-ep3x-pro-video-doorbell-review"),
 "argos_arlo": ("Argos: Arlo doorbell", "https://www.argos.co.uk/product/4379311"),
 "arlo_faq": ("Arlo UK plans FAQ", "https://www.arlo.com/en_gb/support/faq/subscriptions-and-payments/what-arlo-subscription-plans-and-cloud-recording-options-are-available"),
 "arlo_blog": ("Arlo UK blog", "https://www.arlo.com/en_gb/blog/smart-security/should-you-have-a-video-doorbell-without-a-subscription"),
 "arlo_hubcompat": ("Arlo SmartHub compatibility", "https://www.arlo.com/en_gb/support/faq/connectivity-and-integrations/arlo-smarthub-and-base-station-compatibility"),
 "amz_arlohub": ("Amazon UK: Arlo SmartHub", "https://www.amazon.co.uk/Arlo-Certified-Accessory-Designed-Floodlight/dp/B08516SJZ9"),
 "tr_arlo": ("Trusted Reviews, 2026", "https://www.trustedreviews.com/reviews/arlo-essential-3-2k-security-camera"),
 "ambient_arlo": ("The Ambient", "https://www.the-ambient.com/reviews/arlo-pro-6-2k-review/"),
 "amz_aqara": ("Amazon UK: Aqara G4", "https://www.amazon.co.uk/Aqara-Doorbell-Included-Recognition-Automations/dp/B0BPHTL7MG"),
 "aqara_eu": ("Aqara EU store", "https://eu.aqara.com/products/aqara-video-doorbell-g4"),
 "ha_homekit": ("Home Assistant: HomeKit Device", "https://www.home-assistant.io/integrations/homekit_controller"),
 "amz_blink": ("Amazon UK: Blink 2K+", "https://www.amazon.co.uk/blink-battery-doorbell-2k-/dp/B0G62K1Y6C"),
 "camel_sm2": ("camelcamelcamel (Sync Module 2)", "https://uk.camelcamelcamel.com/product/B08BJ9ZCZC"),
 "blink_plans": ("Blink UK plans", "https://blinkforhome.com/plans-uk"),
 "blink_sm2": ("Blink Sync Module 2 FAQ", "https://support.blinkforhome.com/en_GB/faq-sm2/faq-sync-module-2"),
 "ha_blink": ("Home Assistant: Blink", "https://www.home-assistant.io/integrations/blink/"),
 "amz_ep3x": ("Amazon UK: EZVIZ EP3x Pro", "https://www.amazon.co.uk/EZVIZ-Dual-Lens-Doorbell-Detection-EP3X/dp/B0F2DXSGFD"),
 "ezviz_blog": ("EZVIZ UK: no-subscription guide", "https://www.ezviz.com/uk/blog/detail/best-video-doorbells-without-monthly-subscription-fees/2609214160772537"),
 "ezviz_cloud": ("EZVIZ CloudPlay (EU prices)", "https://www.ezviz.com/page/cloudplay"),
 "ha_ezviz": ("Home Assistant: EZVIZ", "https://www.home-assistant.io/integrations/ezviz/"),
 "ertech_db2": ("ER Tech (UK retailer)", "https://www.ertech.co.uk/product/db2-pro/"),
 "eagle_hik": ("Eagle Security Solutions", "https://eaglesecuritysolutions.co.uk/p/door-entry-systems/wireless-intercoms/hikvision-ds-kb6003-wip-video-doorbell-fully-installed/"),
 "hik_ds": ("Hikvision datasheet", "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000083/S000000126/S000000127/OFR000160/M000001570/Data_Sheet/UD04258B_Spec-of-DS-KB6003-WIP-Wi-Fi-Doorbell_V1.4.6_20170519.pdf"),
}

# rec: 'yes' records free out of the box / 'kit' needs extra hardware or very limited / 'no'
# score parts: rec 0-2, live 0-1, alerts 0-1, ai 0-1, storage_in_box 0-1, ha 0-2  (max 8)
ROWS = [
dict(id="ring", brand="Ring", model="Battery Video Doorbell 2K", rec="no", power=["battery","wired"], ha=0,
 price=79.99, price_note="Ring UK, in stock", price_src="ring_prod",
 extra=0, extra_note="", free_records=False,
 sub=4.99, sub_name="Ring Solo",
 best="Alexa households happy to pay the monthly plan",
 catch="Saves no video at all unless you pay £4.99 a month.",
 storage="None. No on-device or hub storage.", live="Yes", alerts="Yes, motion and button-press alerts",
 ai="Paid (person, package and vehicle alerts on Ring's plans page)",
 history="None", paywalled="All recording and playback (up to 180 days), smart alerts, Extended Live View; 24/7 recording is £3/month extra per device",
 sub_text="Ring Solo £4.99/month or £49.99/year (1 device). Multi £7.99/month, AI Pro £15.99/month",
 ha_text="Official integration, but it goes through Ring's cloud. No local-only option.",
 wifi="2.4 GHz only",
 score=dict(rec=0,live=1,alerts=1,ai=0,storage=0,ha=0),
 src=["ring_prod","ring_plans","indy_ring","ha_ring"],
 unverified="Ring's product page lists 'Package Alerts' as included on all doorbells, but its plans page lists package alerts as paid."),
dict(id="nest", brand="Google Nest", model="Doorbell (battery)", rec="kit", power=["battery","wired"], ha=0,
 price=179.99, price_note="Google Store UK", price_src="nest_prod",
 extra=0, extra_note="", free_records=False,
 sub=8.00, sub_name="Google Home Premium Standard",
 best="Google Home households who want polished smart alerts",
 catch="Only 3 hours of free history. Anything longer is £8 a month.",
 storage="None", live="Yes", alerts="Yes",
 ai="Partly. Google advertises people/parcel/animal/vehicle alerts, but lists 'intelligent alerts' under Premium",
 history="3 hours of event clips", paywalled="30 or 60 days of history, intelligent alerts, familiar faces, Gemini search. No 24/7 recording on this model at any price",
 sub_text="Google Home Premium Standard £8/month (£80/year); Advanced £16/month (£160/year)",
 ha_text="Official integration, but it goes through Google's cloud (Cloud Push) and needs a one-off US$5 Google developer fee.",
 wifi="Not checked",
 score=dict(rec=1,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["nest_prod","nest_prem","ha_nest"],
 unverified="Which smart alerts stay free is unclear: Google's own pages contradict each other."),
dict(id="eufy-e340", brand="eufy", model="Video Doorbell E340", rec="yes", power=["battery","wired"], ha=1,
 price=169.99, price_note="eufy UK", price_src="eufy_prod",
 extra=0, extra_note="8 GB storage built in", free_records=True,
 sub=3.99, sub_name="eufy Cloud Backup Basic",
 best="Busy doorsteps with lots of parcels: a second camera looks straight down",
 catch="Expensive, Home Assistant support is unofficial, and eufy had a cloud-privacy scandal in 2022.",
 storage="8 GB in the doorbell; optional HomeBase S380 (16 GB, expandable)", live="Yes", alerts="Yes",
 ai="Free: person and package detection on the device",
 history="Yes, event clips kept locally", paywalled="Nothing essential; cloud backup is optional",
 sub_text="Optional Cloud Backup £3.99/month or £39.99/year (1 device); £12.99/month for all devices",
 ha_text="Community add-on only (eufy_security), which still logs in through your eufy account.",
 wifi="Not checked",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=1),
 src=["eufy_prod","eufy_cloud","verge_eufy","sha_nosub"],
 unverified="Home Assistant details come from a third-party guide and haven't been tested."),
dict(id="reo-wifi", brand="Reolink", model="Video Doorbell WiFi", rec="yes", power=["wired"], ha=2,
 price=93.49, price_note="Reolink UK sale price (RRP £109.99)", price_src="reo_store",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=3.49, sub_name="Reolink Cloud single-device",
 best="Homes with existing doorbell wiring, plus Home Assistant or NVR users",
 catch="Needs doorbell transformer wiring, and the microSD card is sold separately.",
 storage="microSD (up to 256 GB) and/or a Reolink NVR; RTSP/ONVIF", live="Yes", alerts="Yes",
 ai="Free: person detection", history="Yes, motion-triggered or 24/7 recording to card or NVR",
 paywalled="Nothing. Reolink Cloud is optional",
 sub_text="Optional Reolink Cloud. UK price not confirmed; EU from €3.59/month (1 device)",
 ha_text="Official, fully local integration (Local Push, top 'Platinum' quality rating); works with no internet connection.",
 wifi="Dual-band (per third-party guide)",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=2),
 src=["reo_store","ha_reo","reo_cloud","sha_nosub"],
 unverified="Reolink Cloud UK price (£3.49/month is used in the sums; it comes from a third-party post)."),
dict(id="reo-poe", brand="Reolink", model="Video Doorbell PoE", rec="yes", power=["poe"], ha=2,
 price=69.99, price_note="Reolink UK sale price (RRP £99.99)", price_src="reo_store",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=3.49, sub_name="Reolink Cloud single-device",
 best="The most reliable, fully local setup, if you can run an Ethernet cable",
 catch="Needs an Ethernet cable to the door and a PoE switch or injector.",
 storage="microSD and/or NVR; RTSP/ONVIF", live="Yes", alerts="Yes", ai="Free: person detection",
 history="Yes, motion-triggered or 24/7 recording", paywalled="Nothing",
 sub_text="Optional Reolink Cloud. UK price not confirmed; EU from €3.59/month (1 device)",
 ha_text="Official, fully local integration (Local Push, Platinum).", wifi="Wired Ethernet",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=2),
 src=["reo_store","ha_reo","reo_cloud"],
 unverified="Reolink Cloud UK price."),
dict(id="reo-batt", brand="Reolink", model="Video Doorbell (Battery)", rec="yes", power=["battery","wired"], ha=1,
 price=99.99, price_note="Screwfix, includes 64 GB card (Reolink UK also £99.99)", price_src="screwfix_reo",
 extra=0, extra_note="64 GB card included (Screwfix)", free_records=True,
 sub=3.49, sub_name="Reolink Cloud single-device",
 best="Battery install with 5 GHz Wi-Fi and no fees",
 catch="Footage sits on a card in the doorbell itself unless you pay about £50 more for the Home Hub bundle.",
 storage="microSD in the doorbell, or a Home Hub indoors (up to 1 TB)", live="Yes", alerts="Yes",
 ai="Free: person, vehicle and package detection", history="Yes, on card or hub", paywalled="Nothing",
 sub_text="Optional Reolink Cloud. UK price not confirmed; EU from €3.59/month (1 device)",
 ha_text="Official Reolink integration; battery models are best connected through a Reolink Home Hub.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=1),
 src=["screwfix_reo","reo_batt","ha_reo"],
 unverified="Home Assistant support for this exact model through the Home Hub. Hub bundle £149.99 vs £99.99 on its own."),
dict(id="tapo-d230", brand="TP-Link Tapo", model="D230S1", rec="yes", power=["battery"], ha=1,
 price=84.99, price_note="Tapo UK (RRP £94.99)", price_src="tapo_d230",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=2.99, sub_name="Tapo Care",
 best="An easy battery doorbell that keeps footage indoors on its chime/hub",
 catch="The microSD card is extra, and Home Assistant needs an unofficial add-on.",
 storage="microSD (up to 512 GB) in the indoor H200 hub", live="Yes", alerts="Yes",
 ai="Free: person detection", history="Yes, on the hub's card",
 paywalled="30-day cloud history, snapshot notifications, Smart Sort",
 sub_text="Optional Tapo Care from £2.99/month or £29.49/year",
 ha_text="Official integration doesn't show video. The community 'Tapo: Cameras Control' add-on reportedly works locally.",
 wifi="Not checked",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["tapo_d230","tapo_care","ha_tapo","er_tapo"],
 unverified="Home Assistant support (from forum posts only)."),
dict(id="tapo-td21", brand="TP-Link Tapo", model="TD21", rec="yes", power=["battery"], ha=0,
 price=44.99, price_note="Tapo UK sale price (RRP £56.00)", price_src="tapo_td21",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=2.99, sub_name="Tapo Care",
 best="The tightest budget",
 catch="Basic, and it isn't clear whether the card sits in the doorbell (stealable) or the chime.",
 storage="microSD up to 512 GB", live="Yes", alerts="Yes", ai="Free: person detection",
 history="Yes, on card", paywalled="30-day cloud history, snapshot notifications, Smart Sort",
 sub_text="Optional Tapo Care from £2.99/month", ha_text="Unknown", wifi="Not checked",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["tapo_td21","tapo_care"],
 unverified="Where the card goes; Home Assistant support."),
dict(id="arlo", brand="Arlo", model="Essential Video Doorbell 2K (2nd gen)", rec="kit", power=["battery","wired"], ha=0,
 price=169.99, price_note="Argos, doorbell + chime bundle", price_src="argos_arlo",
 extra=109.74, extra_note="+ Arlo SmartHub £99.74 + USB stick", free_records=True,
 sub=7.99, sub_name="Arlo Secure (1 camera)",
 best="People who already own Arlo cameras",
 catch="Recording needs a £7.99/month plan or a separate hub costing about £100.",
 storage="Only through an Arlo SmartHub (VMB4540, USB) or a Base Station", live="Yes", alerts="Yes",
 ai="Paid", history="None without a hub",
 paywalled="Cloud recording (7, 14 or 30 days depending on plan), object detection, activity zones, theft replacement",
 sub_text="Arlo Secure £7.99/month (1 camera, 7 days), Multi-Cam £11.99, Secure Plus £19.99, Secure Pro £24.99",
 ha_text="No official integration; only a community add-on that goes through Arlo's cloud.",
 wifi="Not checked",
 score=dict(rec=1,live=1,alerts=1,ai=0,storage=0,ha=0),
 src=["argos_arlo","arlo_blog","arlo_faq","arlo_hubcompat","amz_arlohub","tr_arlo","ambient_arlo"],
 unverified="Argos price; whether the doorbell can be hardwired. Arlo's own UK pages don't show plan prices; the £7.99 is from two 2026 reviews."),
dict(id="aqara-g4", brand="Aqara", model="Video Doorbell G4", rec="yes", power=["battery","wired"], ha=1,
 price=84.99, price_note="Amazon UK", price_src="amz_aqara",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=None, sub_name="No plan needed (iCloud+ only for HomeKit Secure Video)",
 best="Apple Home users",
 catch="Runs on AA batteries unless wired, and setting it up in Home Assistant is fiddly.",
 storage="microSD (up to 512 GB) in the indoor chime", live="Yes", alerts="Yes",
 ai="Free: face recognition on the device", history="Yes, on the chime's card (24/7 only when wired)",
 paywalled="Nothing essential. HomeKit Secure Video needs Apple's paid iCloud+",
 sub_text="None needed", ha_text="Reported to work locally through HA's HomeKit Device integration.",
 wifi="Not checked",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["amz_aqara","aqara_eu","ha_homekit"],
 unverified="Amazon price and card limit (from search summaries); Home Assistant support (from user forum posts)."),
dict(id="blink", brand="Blink", model="Battery Doorbell 2K+", rec="kit", power=["battery"], ha=0,
 price=69.99, price_note="Amazon UK RRP (deals as low as £29.99)", price_src="amz_blink",
 extra=49.99, extra_note="+ Sync Module 2 £39.99 + USB stick", free_records=True,
 sub=2.50, sub_name="Blink Basic",
 best="The cheapest way into Amazon's ecosystem, if you catch a deal",
 catch="Saves nothing without a £40 Sync Module 2 and a USB stick, and live view cuts off after 5 minutes.",
 storage="Only through a Sync Module 2 + USB stick (1–256 GB); clips aren't encrypted", live="Capped at 5 minutes",
 alerts="Yes", ai="Paid (person and vehicle detection)", history="None without a Sync Module 2",
 paywalled="Cloud clips, person/vehicle detection, 90-minute live view, AI descriptions",
 sub_text="Blink Basic £2.50/month (£24.99/year); Plus £8/month; Basic AI £5.49/month",
 ha_text="Official integration, but it goes through Blink's cloud.", wifi="2.4 GHz (Blink requirement)",
 score=dict(rec=1,live=0,alerts=1,ai=0,storage=0,ha=0),
 src=["amz_blink","camel_sm2","blink_plans","blink_sm2","ha_blink"],
 unverified="Amazon listing showed long dispatch times when checked."),
dict(id="ezviz-ep3x", brand="EZVIZ", model="EP3x Pro", rec="yes", power=["battery"], ha=0,
 price=79.99, price_note="Amazon UK (list price £89.99)", price_src="amz_ep3x",
 extra=0, extra_note="32 GB storage built in", free_records=True,
 sub=4.99, sub_name="EZVIZ CloudPlay 7-day",
 best="Two cameras on a budget, with storage built in",
 catch="Expert Reviews found its motion detection unreliable and the app confusing.",
 storage="32 GB built in, no card needed", live="Yes", alerts="Yes",
 ai="Free: human and package detection", history="Yes, on built-in storage",
 paywalled="Nothing essential. CloudPlay is optional",
 sub_text="Optional CloudPlay: €4.99/month (7 days) on EZVIZ's EU page; UK price only shown in the app",
 ha_text="Official integration, but it goes through EZVIZ's cloud. Support for battery doorbells unknown.",
 wifi="2.4 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=0),
 src=["amz_ep3x","ezviz_blog","er_tapo","ezviz_cloud","ha_ezviz"],
 unverified="CloudPlay UK price (£4.99 assumed); Amazon price."),
dict(id="ezviz-db2", brand="EZVIZ", model="DB2 Pro Kit", rec="yes", power=["battery"], ha=0,
 price=114.99, price_note="ER Tech, UK retailer", price_src="ertech_db2",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=4.99, sub_name="EZVIZ CloudPlay 7-day",
 best="Flats and rentals: no wiring, and footage stays indoors in the chime",
 catch="2.4 GHz Wi-Fi only, and the card is sold separately.",
 storage="microSD (up to 256 GB) in the included indoor chime", live="Yes", alerts="Yes",
 ai="Free: PIR plus human-shape detection", history="Yes, on the chime's card", paywalled="Nothing essential",
 sub_text="Optional CloudPlay: €4.99/month (7 days) on EZVIZ's EU page; UK price only shown in the app", ha_text="Official integration, but it goes through EZVIZ's cloud.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["ertech_db2","ezviz_blog","ezviz_cloud","ha_ezviz"],
 unverified="CloudPlay UK price; Home Assistant support for this model."),
dict(id="hik", brand="Hikvision", model="DS-KB6003-WIP", rec="yes", power=["wired"], ha=1,
 price=295.00, price_note="Only UK listing found; includes installation", price_src="eagle_hik",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=None, sub_name="No plan",
 best="Only worth it if an installer is fitting a Hikvision system anyway",
 catch="Discontinued trade product; the price includes fitting.",
 storage="microSD up to 128 GB; RTSP to an NVR", live="Yes (Hik-Connect app)", alerts="Yes (motion)",
 ai="None", history="Yes, on card or NVR", paywalled="Nothing", sub_text="None",
 ha_text="Works as a generic RTSP camera.", wifi="Not checked",
 score=dict(rec=2,live=1,alerts=1,ai=0,storage=0,ha=1),
 src=["eagle_hik","hik_ds"],
 unverified="ONVIF support; availability."),
]

# ---------- derived figures ----------
def money(x): return f"£{x:,.2f}"
for r in ROWS:
    r["score_total"] = sum(r["score"].values())
    r["nosub3"] = round(r["price"] + r["extra"], 2)
    r["sub3"] = round(r["price"] + MONTHS * r["sub"], 2) if r["sub"] is not None else None
    # cheapest way to keep recordings for 3 years
    opts = []
    if r["free_records"]: opts.append(r["nosub3"])
    if r["sub3"] is not None: opts.append(r["sub3"])
    r["keep3"] = min(opts)
    m_free = f"{money(r['price'])}" + (f" + {money(r['extra'])} ({r['extra_note'].lstrip('+ ')})" if r["extra"] else "") + f" = {money(r['nosub3'])}"
    if not r["free_records"]: m_free += " (but no recordings)" if r["rec"]=="no" else " (3 hours of history only)"
    m_sub = (f"{money(r['price'])} + {MONTHS} × {money(r['sub'])} ({r['sub_name']}) = {money(r['sub3'])}" if r["sub3"] is not None else "No subscription offered or needed")
    r["maths_free"], r["maths_sub"] = m_free, m_sub

REC_LABEL = {"yes":"Yes", "kit":"Only with extra kit", "no":"No"}
REC_RANK = {"yes":2, "kit":1, "no":0}
POWER_LABEL = {"battery":"Battery", "wired":"Wired", "poe":"PoE"}
HA_LABEL = {2:"Official, local", 1:"Local, unofficial", 0:"Cloud only"}
SCORE_PARTS = [("rec","Records free",2),("live","Live view free",1),("alerts","Motion alerts free",1),("ai","Smart detection free",1),("storage","Storage in the box",1),("ha","Local / Home Assistant",2)]

# footnote numbering
order=[]
for r in ROWS:
    for k in r["src"]:
        if k not in order: order.append(k)
FN = {k:i+1 for i,k in enumerate(order)}

# ---------- CSV ----------
with open(os.path.join(ROOT,"data","doorbells.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f)
    w.writerow(["Brand","Model","Records free without subscription","Power","UK price (£)","Price note","Price source",
        "Best for","Main catch","Free-feature score (/8)","3-yr cost without subscription (£)","3-yr cost with cheapest plan, monthly (£)",
        "Cheapest 3-yr cost to keep recordings (£)","Maths: without","Maths: with","Local storage","Live view free?","Motion alerts free?",
        "Smart detection","Recorded history without subscription","What's paywalled","Subscription & UK price","Home Assistant / local-only",
        "Wi-Fi","Sources","Unverified / re-check","Last checked"])
    for r in ROWS:
        w.writerow([r["brand"],r["model"],REC_LABEL[r["rec"]],"/".join(POWER_LABEL[p] for p in r["power"]),f"{r['price']:.2f}",r["price_note"],S[r["price_src"]][1],
            r["best"],r["catch"],r["score_total"],f"{r['nosub3']:.2f}","" if r["sub3"] is None else f"{r['sub3']:.2f}",f"{r['keep3']:.2f}",r["maths_free"],r["maths_sub"],
            r["storage"],r["live"],r["alerts"],r["ai"],r["history"],r["paywalled"],r["sub_text"],r["ha_text"],r["wifi"],
            " ; ".join(S[k][1] for k in r["src"]),r["unverified"],CHECKED])

# ---------- Markdown ----------
md=[f"# UK video doorbells without a subscription\n", f"Last checked {CHECKED}. {len(ROWS)} doorbells. No affiliate links.\n",
    "| Doorbell | Records free? | Price | Score /8 | 3 yrs, no plan | 3 yrs, with plan | Best for | Main catch |","|---|---|---|---|---|---|---|---|"]
for r in sorted(ROWS,key=lambda r:r["keep3"]):
    md.append(f"| {r['brand']} {r['model']} | {REC_LABEL[r['rec']]} | [{money(r['price'])}]({S[r['price_src']][1]}) | {r['score_total']} | {money(r['nosub3'])} | {money(r['sub3']) if r['sub3'] else '—'} | {r['best']} | {r['catch']} |")
md.append("\n## Detail\n")
for r in ROWS:
    md += [f"### {r['brand']} {r['model']}", f"- **Best for:** {r['best']}", f"- **Main catch:** {r['catch']}",
      f"- **Price:** {money(r['price'])} ({r['price_note']})", f"- **3-year cost, no plan:** {r['maths_free']}", f"- **3-year cost, with plan:** {r['maths_sub']}",
      f"- **Storage:** {r['storage']}", f"- **Free:** live view {r['live'].lower()}; alerts {r['alerts'].lower()}; smart detection: {r['ai']}",
      f"- **History without plan:** {r['history']}", f"- **Paywalled:** {r['paywalled']}", f"- **Plans:** {r['sub_text']}",
      f"- **Home Assistant:** {r['ha_text']}", f"- **Unverified:** {r['unverified']}",
      "- **Sources:** " + " · ".join(f"[{S[k][0]}]({S[k][1]})" for k in r["src"]), ""]
md += ["## How the 3-year costs are worked out",
 f"- Without a plan: hardware price + anything extra you need to record for free (a microSD card or USB stick is assumed at {money(CARD)}; that figure isn't from a cited source).",
 f"- With a plan: hardware price + {MONTHS} × the cheapest UK monthly plan that adds recording for one device. Paying yearly is usually cheaper.",
 "- Batteries, electricity, installation (except Hikvision, where it's included) and price rises are left out."]
open(os.path.join(ROOT,"data","doorbells.md"),"w",encoding="utf-8").write("\n".join(md))

# ---------- HTML ----------
e=html.escape
def fn(keys): return ", ".join(f'<a class="fn" href="#fn{FN[k]}" title="{e(S[k][0])}">{FN[k]}</a>' for k in keys)
def gbp(x): return "—" if x is None else f"£{x:,.0f}" if float(x).is_integer() else f"£{x:,.2f}"

# Product photos: manufacturers' own images, processed by make_images.py into img/*.webp; sources in images.json
IMG = json.load(open(os.path.join(HERE,"images.json"), encoding="utf-8"))
def photo(r, size):
    name = f"{r['brand']} {r['model']}"
    w, h = (45, 60) if size == "sm" else (180, 240)
    m = IMG.get(r["id"], {})
    if m.get("placeholder") or not m:
        return f'<span class="ph ph-{size}" role="img" aria-label="No photo available for {e(name)}" style="width:{w}px;height:{h}px"><span>No photo</span></span>'
    return f'<img class="ph ph-{size}" src="img/{r["id"]}-{size}.webp" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{e(name)}">'

# Short-answer verdicts, colour-coded and repeated on the matching rows
VERDICT = {"reo-wifi":"best","reo-poe":"best","reo-batt":"best","tapo-d230":"batt","ring":"avoid","blink":"avoid","arlo":"avoid"}
V_LABEL = {"best":"Best overall","batt":"Battery pick","avoid":"Avoid without a plan"}
def vlink(ids, text): return f'<a class="jump" href="#m-{ids[0]}" data-ids="{" ".join(ids)}">{text}</a>'

rows_html=[]
for i,r in enumerate(ROWS):
    pw=" ".join(r["power"])
    sc=r["score_total"]
    v=VERDICT.get(r["id"])
    vattr=f' data-v="{v}"' if v else ""
    vtag=f'<span class="vtag v-{v}"> {V_LABEL[v]}</span>' if v else ""
    rows_html.append(f'''<tbody class="item" id="m-{r['id']}" data-id="{r['id']}"{vattr} data-rec="{r['rec']}" data-recv="{REC_RANK[r['rec']]}" data-ha="{r['ha']}" data-power="{pw}" data-price="{r['price']}" data-keep3="{r['keep3']}" data-nosub3="{r['nosub3']}" data-sub3="{r['sub3'] if r['sub3'] is not None else 999999}" data-score="{sc}" data-model="{e((r['brand']+' '+r['model']).lower())}" data-idx="{i}">
<tr class="main">
<td class="c-cmp"><input type="checkbox" class="cmp" value="{r['id']}" aria-label="Compare {e(r['brand'])} {e(r['model'])}"></td>
<th scope="row" class="c-model"><div class="mcell">{photo(r,"sm")}<div><span class="brand">{e(r['brand'])}</span> <span class="mname">{e(r['model'])}</span>{vtag}<span class="best">Best for: {e(r['best'])}</span></div></div></th>
<td class="c-rec" data-label="Records free?"><span class="rec rec-{r['rec']}"> {REC_LABEL[r['rec']]}</span></td>
<td class="c-price num" data-label="Price">{gbp(r['price'])}{fn([r['price_src']])}</td>
<td class="c-score" data-label="Free features"><span class="score"><b>{sc}</b>/8</span><span class="bar" aria-hidden="true"><i style="width:{sc/8*100:.0f}%"></i></span></td>
<td class="c-nosub num" data-label="3 yrs, no plan">{gbp(r['nosub3'])}{'' if r['free_records'] else '<span class="note">no recordings</span>' if r['rec']=='no' else '<span class="note">3 hrs history</span>'}</td>
<td class="c-sub num" data-label="3 yrs, with plan">{gbp(r['sub3'])}</td>
<td class="c-catch" data-label="Main catch">{e(r['catch'])}<div class="more-w"><button type="button" class="more" aria-expanded="false" aria-controls="d-{r['id']}">Details</button></div></td>
</tr>
<tr class="detail" id="d-{r['id']}" hidden><td colspan="8"><div class="dgrid">
<figure class="dimg">{photo(r,"lg")}</figure>
<dl>
<dt>Power</dt><dd>{" / ".join(POWER_LABEL[p] for p in r['power'])}; Wi-Fi: {e(r['wifi'])}</dd>
<dt>Storage</dt><dd>{e(r['storage'])}</dd>
<dt>Live view</dt><dd>{e(r['live'])}</dd>
<dt>Motion alerts</dt><dd>{e(r['alerts'])}</dd>
<dt>Smart detection</dt><dd>{e(r['ai'])}</dd>
<dt>History without a plan</dt><dd>{e(r['history'])}</dd>
</dl><dl>
<dt>Behind the paywall</dt><dd>{e(r['paywalled'])}</dd>
<dt>Plans</dt><dd>{e(r['sub_text'])}</dd>
<dt>Home Assistant</dt><dd>{e(r['ha_text'])}</dd>
<dt>3 years, no plan</dt><dd class="maths">{e(r['maths_free'])}</dd>
<dt>3 years, with plan</dt><dd class="maths">{e(r['maths_sub'])}</dd>
<dt>Score breakdown</dt><dd>{"; ".join(f"{lbl} {r['score'][k]}/{mx}" for k,lbl,mx in SCORE_PARTS)}</dd>
</dl></div>
<p class="unverified"><b>Not yet verified:</b> {e(r['unverified'])}</p>
<p class="srcs">Sources {fn(r['src'])}</p></td></tr>
</tbody>''')

data_js = json.dumps({r["id"]:{
 "name":f"{r['brand']} {r['model']}","rec":REC_LABEL[r["rec"]],"price":gbp(r["price"]),"score":f"{r['score_total']}/8",
 "nosub3":gbp(r["nosub3"]),"sub3":gbp(r["sub3"]),"best":r["best"],"catch":r["catch"],"power":" / ".join(POWER_LABEL[p] for p in r["power"]),
 "storage":r["storage"],"live":r["live"],"alerts":r["alerts"],"ai":r["ai"],"history":r["history"],"paywalled":r["paywalled"],
 "plan":r["sub_text"],"ha":r["ha_text"],"wifi":r["wifi"],
 "img":"" if IMG.get(r["id"],{}).get("placeholder") else f'img/{r["id"]}-sm.webp'} for r in ROWS}, ensure_ascii=False)

fn_list="".join(f'<li id="fn{FN[k]}"><a href="{e(S[k][1])}" rel="nofollow noopener noreferrer">{e(S[k][0])}</a></li>' for k in order)
maxp=int(max(r["price"] for r in ROWS)+5)
byid={r["id"]:r for r in ROWS}
photo_credits=", ".join(f'<a href="{e(IMG[r["id"]]["page"])}" rel="nofollow noopener noreferrer">{e(r["brand"])} {e(r["model"])}</a>' for r in ROWS if not IMG.get(r["id"],{}).get("placeholder"))
no_photo=", ".join(f'{e(r["brand"])} {e(r["model"])}' for r in ROWS if IMG.get(r["id"],{}).get("placeholder"))

page=f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta name="color-scheme" content="light dark">
<title>Video doorbells that work without a subscription (UK) | SubFree UK</title>
<meta name="description" content="{len(ROWS)} UK video doorbells compared: what is free, what is paywalled, and what each costs over three years.">
<script>try{{var t=localStorage.getItem("theme");if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script>
<style>
:root{{--ink:#1a1a1a;--ink2:#555;--ink3:#767676;--rule:#d9d6cf;--rule2:#ece9e2;--paper:#fff;--tint:#f6f4ef;--acc:#0f5c4d;
--v-best:#17694a;--v-batt:#1f5d96;--v-avoid:#a33b26;--hl:#fff1b8;--tray:#1a1a1a;--tray-ink:#fff;--imgbg:#fff;--imgf:none;
--serif:Charter,"Bitstream Charter","Iowan Old Style","Sitka Text",Cambria,Georgia,serif;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color-scheme:light}}
:root[data-theme=dark]{{--ink:#e9e7e2;--ink2:#b3b0a9;--ink3:#8f8c86;--rule:#3b3a37;--rule2:#2b2a28;--paper:#151514;--tint:#1e1e1c;--acc:#62c2a8;
--v-best:#5fc896;--v-batt:#80b4ea;--v-avoid:#f08a74;--hl:#4a4320;--tray:#2b2a28;--tray-ink:#e9e7e2;--imgbg:#fff;--imgf:brightness(.86);color-scheme:dark}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--ink:#e9e7e2;--ink2:#b3b0a9;--ink3:#8f8c86;--rule:#3b3a37;--rule2:#2b2a28;--paper:#151514;--tint:#1e1e1c;--acc:#62c2a8;
--v-best:#5fc896;--v-batt:#80b4ea;--v-avoid:#f08a74;--hl:#4a4320;--tray:#2b2a28;--tray-ink:#e9e7e2;--imgbg:#fff;--imgf:brightness(.86);color-scheme:dark}}}}
*{{box-sizing:border-box}}
[hidden]{{display:none!important}}
html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.45 var(--sans)}}
a{{color:var(--acc)}}
p{{max-width:65ch}}
.wrap{{max-width:1440px;margin:0 auto;padding:0 1rem}}
.mast{{display:flex;justify-content:space-between;align-items:center;gap:1rem;border-bottom:1px solid var(--ink);padding:1rem 0;font:600 12px/1 var(--sans);letter-spacing:.08em;text-transform:uppercase}}
.mast span{{color:var(--ink3);font-weight:500;margin-left:1rem;letter-spacing:.04em}}
#theme{{font:500 12px/1 var(--sans);letter-spacing:.02em;text-transform:none;background:none;color:var(--ink);border:1px solid var(--rule);padding:0 1rem;cursor:pointer;display:inline-flex;align-items:center;gap:1rem;white-space:nowrap;min-height:24px}}
#theme:hover{{border-color:var(--ink)}}
#theme i{{display:inline-block;width:10px;height:10px;border-radius:50%;border:1.5px solid currentColor;background:linear-gradient(90deg,currentColor 50%,transparent 50%)}}
header.intro{{padding:2rem 0;display:grid;grid-template-columns:minmax(0,1.618fr) 1fr;gap:2rem;border-bottom:1px solid var(--rule)}}
h1{{font:700 34px/1.12 var(--serif);margin:0 0 1rem;letter-spacing:-.01em;max-width:22ch}}
.dek{{font:18px/1.45 var(--serif);color:var(--ink2);margin:0 0 1rem}}
.meta{{font-size:13px;color:var(--ink2);margin:0}}
.meta b{{color:var(--ink)}}
.verdict{{border-left:1px solid var(--rule);padding:0 0 0 2rem;font-size:14px}}
.verdict h2{{font:700 13px/1.2 var(--sans);text-transform:uppercase;letter-spacing:.06em;margin:0 0 1rem}}
.verdict p{{margin:0 0 1rem;padding-left:1rem;border-left:3px solid var(--vc)}}
.verdict p b{{color:var(--vc)}}
.v-best{{--vc:var(--v-best)}} .v-batt{{--vc:var(--v-batt)}} .v-avoid{{--vc:var(--v-avoid)}}
a.jump{{color:inherit;font-weight:600;text-decoration:underline;text-decoration-color:var(--vc);text-decoration-thickness:2px;text-underline-offset:2px}}
a.jump:hover{{color:var(--vc)}}
.vtag{{display:block;margin-top:0;padding:1rem 0 0;font:700 10px/1.2 var(--sans);text-transform:uppercase;letter-spacing:.07em;color:var(--vc)}}
.vtag::before{{content:"";display:inline-block;width:7px;height:7px;background:var(--vc);margin-right:0;vertical-align:0}}
tbody.item[data-v=best]{{--vc:var(--v-best)}} tbody.item[data-v=batt]{{--vc:var(--v-batt)}} tbody.item[data-v=avoid]{{--vc:var(--v-avoid)}}
tbody.item[data-v] tr.main>td.c-cmp{{box-shadow:inset 3px 0 0 var(--vc)}}
.controls{{display:flex;flex-wrap:wrap;gap:1rem 2rem;align-items:flex-start;padding:1rem 0;border-bottom:1px solid var(--rule)}}
fieldset{{border:0;margin:0;padding:0;min-width:0}}
legend,.lab{{font:600 11px/1 var(--sans);text-transform:uppercase;letter-spacing:.07em;color:var(--ink2);padding:0;margin-bottom:1rem;display:block}}
.opts{{display:flex;flex-wrap:wrap;gap:1rem}}
.opts label{{display:inline-flex;align-items:center;gap:1rem;min-height:24px;font-size:14px;cursor:pointer;white-space:nowrap}}
input[type=checkbox]{{accent-color:var(--acc);width:15px;height:15px;margin:0}}
input[type=range]{{accent-color:var(--acc);width:180px;min-height:24px;vertical-align:middle;margin:0}}
.range output{{font:600 14px var(--sans);font-variant-numeric:tabular-nums;margin-left:1rem}}
.sortby{{margin-left:auto}}
select{{font:14px var(--sans);padding:0 1rem;min-height:24px;border:1px solid var(--rule);background:var(--paper);color:var(--ink);border-radius:0}}
.count{{flex:1 0 100%;margin:0;font-size:13px;color:var(--ink2)}}
button.link{{background:none;border:0;padding:0;min-height:24px;font:inherit;color:var(--acc);text-decoration:underline;cursor:pointer}}
table.cmp-t,table.main-t{{border-collapse:collapse;width:100%}}
.main-t thead th{{position:sticky;top:0;z-index:2;background:var(--paper);font:600 11px/1.25 var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--ink2);text-align:left;padding:1rem;border-bottom:2px solid var(--ink);vertical-align:bottom;white-space:normal}}
.main-t thead th.num{{text-align:right}}
.main-t thead th button{{font:inherit;letter-spacing:inherit;text-transform:inherit;color:inherit;background:none;border:0;padding:0;margin:0;min-height:24px;cursor:pointer;text-align:inherit}}
.main-t thead th button:hover{{color:var(--ink);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}}
.main-t thead th[aria-sort=ascending] button::after{{content:"\\00a0\\2191"}}
.main-t thead th[aria-sort=descending] button::after{{content:"\\00a0\\2193"}}
.main-t thead sup{{text-transform:none;font-size:9px}}
.main-t td,.main-t tbody th{{padding:1rem;border-bottom:1px solid var(--rule2);vertical-align:top;text-align:left;font-weight:400}}
.main-t tbody.item:hover tr.main{{background:var(--tint)}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.main-t td.num,.main-t th.num{{text-align:right}}
td.num{{white-space:nowrap}}
.c-cmp{{width:2rem;padding-left:0!important;padding-right:0!important}}
.c-rec{{width:120px}}
.c-model{{width:27%}}
.mcell{{display:flex;gap:1rem;align-items:flex-start}}
.mcell>div{{min-width:0}}
.ph{{display:block;flex:none;background:var(--imgbg);border:1px solid var(--rule2);object-fit:contain}}
img.ph{{filter:var(--imgf)}}
span.ph{{display:flex;align-items:center;justify-content:center;background:var(--tint);color:var(--ink3);font:600 9px/1.2 var(--sans);text-transform:uppercase;letter-spacing:.06em;text-align:center}}
span.ph-lg{{font-size:11px}}
.brand{{font-weight:700}} .mname{{font-weight:400}}
.best{{display:block;font-size:13px;color:var(--ink2);margin-top:0;line-height:1.35}}
.c-catch{{font-size:14px;width:28%}}
.more-w{{margin-top:1rem}}
.rec{{font-size:14px;display:inline-block;padding-left:1rem;text-indent:-1rem}}
.rec::before{{content:"";display:inline-block;width:8px;height:8px;margin-right:0;vertical-align:1px;border:1.5px solid var(--acc);text-indent:0}}
.rec-yes::before{{background:var(--acc)}}
.rec-kit::before{{background:linear-gradient(90deg,var(--acc) 50%,transparent 50%)}}
.rec-no{{color:var(--ink2)}} .rec-no::before{{border-color:var(--ink3)}}
.score b{{font-size:15px}} .score{{color:var(--ink2);font-size:13px;white-space:nowrap}}
.bar{{display:block;height:3px;background:var(--rule2);margin:1rem 0 0;width:52px}}
.bar i{{display:block;height:100%;background:var(--acc)}}
.note{{display:block;font-size:12px;color:var(--ink3);white-space:normal}}
.fn{{font-size:10px;vertical-align:super;line-height:0;margin-left:0;text-decoration:none;color:var(--ink3)}}
.fn:hover{{color:var(--acc);text-decoration:underline}}
.c-price .fn{{display:inline-block;min-width:1rem;text-align:left;white-space:nowrap}}
button.more{{background:none;border:1px solid var(--rule);font:12px var(--sans);padding:0 1rem;min-height:24px;cursor:pointer;color:var(--ink);white-space:nowrap}}
button.more:hover,button.more[aria-expanded=true]{{border-color:var(--ink)}}
tr.detail td{{background:var(--tint);padding:1rem 1rem 1rem 3rem;border-bottom:1px solid var(--rule)}}
.dgrid{{display:grid;grid-template-columns:180px minmax(0,1fr) minmax(0,1fr);gap:0 2rem}}
.dimg{{margin:0}}
.dgrid dl{{margin:0;display:grid;grid-template-columns:140px minmax(0,1fr);gap:1rem;font-size:14px;align-content:start}}
.dgrid dt{{color:var(--ink2)}} .dgrid dd{{margin:0}}
.maths{{font-variant-numeric:tabular-nums}}
.unverified{{font-size:13px;margin:1rem 0 0;color:var(--ink2)}}
.srcs{{font-size:12px;color:var(--ink3);margin:1rem 0 0}}
.srcs .fn{{font-size:12px;vertical-align:baseline;margin-left:0;color:var(--acc)}}
.empty{{padding:2rem 0;margin:0 auto;color:var(--ink2);text-align:center}}
/* jump-to-row highlight */
@keyframes flash{{0%,35%{{background-color:var(--hl)}}100%{{background-color:transparent}}}}
tbody.item.flash tr.main>*{{animation:flash 1.8s ease-out}}
@media (prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}} tbody.item.flash tr.main>*{{animation:none;background:var(--hl)}}}}
/* compare */
#compare{{border:1px solid var(--ink);margin:1rem 0 0;padding:0 0 1rem}}
.cmp-head{{display:flex;justify-content:space-between;align-items:baseline;padding:1rem;border-bottom:1px solid var(--rule)}}
.cmp-head h2{{font:700 20px/1.2 var(--serif);margin:0}}
.cmp-scroll{{overflow-x:auto}}
.cmp-t th,.cmp-t td{{padding:1rem;border-bottom:1px solid var(--rule2);text-align:left;vertical-align:top;font-size:14px}}
.cmp-t tbody tr:hover th,.cmp-t tbody tr:hover td{{background:var(--tint)}}
.cmp-t thead th{{font:700 15px/1.25 var(--sans);border-bottom:2px solid var(--ink);min-width:200px}}
.cmp-name{{display:block}}
.cmp-photo{{display:block;margin-top:1rem}}
.cmp-photo img{{display:block;width:45px;height:60px;object-fit:contain;background:var(--imgbg);border:1px solid var(--rule2);filter:var(--imgf)}}
.cmp-t tbody th{{font:600 11px/1.3 var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--ink2);width:150px;min-width:120px}}
.vh{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}}
.tray{{position:sticky;bottom:0;background:var(--tray);color:var(--tray-ink);border-top:1px solid var(--rule);padding:1rem;display:flex;gap:1rem;align-items:center;justify-content:center;font-size:14px;z-index:5}}
.tray button{{font:600 14px var(--sans);background:var(--tray-ink);color:var(--tray);border:0;padding:0 1rem;min-height:24px;cursor:pointer}}
.tray button:disabled{{opacity:.5;cursor:default}}
.tray button.ghost{{background:none;color:var(--tray-ink);text-decoration:underline;padding:0 1rem}}
/* footer */
section.method{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;border-top:1px solid var(--ink);margin-top:2rem;padding:1rem 0 3rem;font-size:13px;color:var(--ink2)}}
section.method h2{{font:700 13px/1.2 var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--ink);margin:0 0 1rem}}
section.method p{{margin:0 0 1rem;max-width:none}}
section.method p a{{color:var(--ink2)}}
ol.fns{{margin:0;padding-left:2rem;columns:2;column-gap:2rem}}
ol.fns li{{margin:0;break-inside:avoid}}
ol.fns a{{color:var(--ink2)}}
@media (min-width:821px) and (max-width:1100px){{
 .count{{flex:1 1 auto;order:1;align-self:flex-end}} .sortby{{order:2}}
}}
/* 821-1100px: the full table must fit without sideways scrolling */
@media (max-width:1100px){{
 .main-t td,.main-t tbody th{{padding:1rem}}
 .main-t thead th{{padding:1rem;letter-spacing:.04em}}
 .c-model{{width:30%}} .c-rec{{width:auto}} .c-catch{{width:24%;font-size:13px}}
 .mcell{{gap:1rem}} .ph-sm{{width:36px!important;height:48px!important}}
 .best{{font-size:12.5px}}
 .rec{{font-size:13px}}
 tr.detail td{{padding-left:1rem}}
 .dgrid{{grid-template-columns:140px minmax(0,1fr) minmax(0,1fr);gap:0 2rem}}
 .ph-lg{{width:140px!important;height:187px!important}}
 .dgrid dl{{grid-template-columns:1fr;gap:0}} .dgrid dt{{margin-top:1rem;font-weight:600;font-size:12px}} .dgrid dt:first-child{{margin-top:0}}
}}
@media (max-width:900px){{
 h1{{font-size:30px}}
 .main-t td,.main-t tbody th{{padding:1rem}}
 .main-t thead th{{padding:1rem;font-size:10px}}
 .c-catch{{width:22%}}
}}
@media (max-width:820px){{
 body{{font-size:15px}}
 .wrap{{padding:0 1rem}}
 header.intro{{grid-template-columns:1fr;gap:1rem;padding:2rem 0}}
 .verdict{{border-left:0;border-top:1px solid var(--rule);padding:1rem 0 0}}
 h1{{font-size:27px}} .dek{{font-size:16px}}
 .controls{{gap:1rem}}
 .sortby{{margin-left:0}}
 input[type=range]{{width:150px}}
 .main-t thead{{display:none}}
 .main-t,.main-t tbody,.main-t tr,.main-t td,.main-t tbody th{{display:block}}
 .main-t tbody.item{{border-bottom:1px solid var(--rule);padding:1rem}}
 tbody.item[data-v]{{box-shadow:inset 3px 0 0 var(--vc)}}
 tbody.item[data-v] tr.main>td.c-cmp{{box-shadow:none}}
 .main-t tr.main{{display:grid;grid-template-columns:2rem repeat(3,minmax(0,1fr));gap:1rem;position:relative}}
 .main-t tbody.item:hover tr.main{{background:none}}
 .main-t tr.main>*{{padding:0;border:0;width:auto;min-width:0;max-width:none}}
 .c-cmp{{grid-row:1;grid-column:1;padding-top:0!important}}
 .c-model{{grid-column:2 / 5}}
 .ph-sm{{width:45px!important;height:60px!important}}
 .c-rec{{grid-column:2}} .c-price{{grid-column:3}} .c-score{{grid-column:4}}
 .c-nosub{{grid-column:2}} .c-sub{{grid-column:3 / 5}}
 .c-catch{{grid-column:2 / 5;font-size:14px}}
 .main-t td[data-label]::before{{content:attr(data-label);display:block;font:600 10px/1.3 var(--sans);text-transform:uppercase;letter-spacing:.07em;color:var(--ink3);margin-bottom:0}}
 .main-t td.num,.main-t th.num{{text-align:left}} .bar{{margin-left:0}}
 tr.detail td{{padding:1rem;margin-top:0}}
 .dgrid{{grid-template-columns:1fr}} .dgrid dl+dl{{margin-top:1rem}}
 .ph-lg{{width:120px!important;height:160px!important;margin-bottom:1rem}}
 section.method{{grid-template-columns:1fr}} ol.fns{{columns:1}}
 .cmp-t th,.cmp-t td{{padding:1rem;font-size:13px}}
 .cmp-t thead th{{min-width:140px;font-size:14px}}
 .cmp-t tbody th{{width:84px;min-width:84px;font-size:10px;position:sticky;left:0;background:var(--paper)}}
 .cmp-t thead th:first-child{{position:sticky;left:0;background:var(--paper);min-width:84px}}
}}
@media (max-width:520px){{.mast>div>span{{display:none}}}}
@media print{{.controls,.tray,.c-cmp,.more-w,#theme{{display:none}} tr.detail{{display:table-row!important}}}}
</style></head><body>
<div class="wrap">
<div class="mast"><div>SubFree UK <span>Gadgets that work without a subscription</span></div><button type="button" id="theme" aria-pressed="false"><i aria-hidden="true"></i><span>Dark mode</span></button></div>
<header class="intro">
<div>
<h1>Video doorbells that work without a subscription</h1>
<p class="dek">{len(ROWS)} doorbells sold in the UK, checked against manufacturer pages and independent reviews: what you get for free, what's behind a paywall, and what each one costs over three years.</p>
<p class="meta"><b>Last checked {CHECKED}.</b> No affiliate links, no tracking, no cookies. Prices change often, so each one links to its source.</p>
</div>
<aside class="verdict">
<h2>The short answer</h2>
<p class="v-best"><b>Best overall without fees:</b> {vlink(["reo-poe","reo-wifi","reo-batt"],"Reolink")}. It records to a card or NVR, nothing is paywalled, and it's the only one here with an official local Home Assistant integration.</p>
<p class="v-batt"><b>Easiest battery pick:</b> {vlink(["tapo-d230"],"Tapo D230S1")}, which keeps footage on a hub inside the house.</p>
<p class="v-avoid"><b>Avoid if you won't pay monthly:</b> {vlink(["ring"],"Ring")} records nothing without a plan, and {vlink(["blink"],"Blink")} and {vlink(["arlo"],"Arlo")} need extra hardware.</p>
</aside>
</header>

<form class="controls" id="controls" onsubmit="return false">
<fieldset><legend>Show only</legend><div class="opts">
<label><input type="checkbox" id="f-rec"> Records free, no extra kit</label>
<label><input type="checkbox" id="f-ha"> Local / Home Assistant</label>
</div></fieldset>
<fieldset><legend>Power</legend><div class="opts">
<label><input type="checkbox" class="f-pw" value="battery"> Battery</label>
<label><input type="checkbox" class="f-pw" value="wired"> Wired</label>
<label><input type="checkbox" class="f-pw" value="poe"> PoE</label>
</div></fieldset>
<div class="range"><label class="lab" for="f-max">Max price</label><input type="range" id="f-max" min="40" max="{maxp}" step="5" value="{maxp}"><output id="f-max-out" for="f-max">£{maxp}</output></div>
<div class="sortby"><label class="lab" for="sort">Sort by</label><select id="sort">
<option value="keep3">3-year cost to keep recordings</option>
<option value="price">Price, low to high</option>
<option value="score">Free-feature score, high to low</option>
<option value="recv">Records free first</option>
<option value="nosub3">3-year cost, no plan</option>
<option value="sub3">3-year cost, with plan</option>
<option value="model">Model, A to Z</option>
</select></div>
<p class="count">Tick up to 3 rows to compare. <span id="count">{len(ROWS)}</span> of {len(ROWS)} shown · <button type="button" class="link" id="reset">Reset</button></p>
</form>

<section id="compare" hidden aria-live="polite">
<div class="cmp-head"><h2>Side by side</h2><button type="button" class="link" id="cmp-close">Close</button></div>
<div class="cmp-scroll"><table class="cmp-t" id="cmp-table"></table></div>
</section>

<table class="main-t" id="tbl">
<thead><tr>
<th class="c-cmp"><span class="vh">Compare</span></th>
<th data-sort="model" aria-sort="none"><button type="button">Model</button></th><th data-sort="recv" aria-sort="none"><button type="button">Records free?</button></th><th class="num" data-sort="price" aria-sort="none"><button type="button">Price</button></th><th data-sort="score" aria-sort="none"><button type="button">Free features</button></th>
<th class="num" data-sort="nosub3" aria-sort="none"><button type="button">3 yrs, no plan<sup>a</sup></button></th><th class="num" data-sort="sub3" aria-sort="none"><button type="button">3 yrs, with plan<sup>b</sup></button></th><th>Main catch</th>
</tr></thead>
{''.join(rows_html)}
</table>
<p class="empty" id="empty" hidden>Nothing matches those filters. <button type="button" class="link" onclick="document.getElementById('reset').click()">Reset filters</button></p>

<section class="method" id="method">
<div>
<h2>How we worked it out</h2>
<p><sup>a</sup> <b>3 years, no plan</b> = price + anything you must add to record for free (Blink's Sync Module 2 at £39.99, Arlo's SmartHub at £99.74, and a microSD card or USB stick, assumed at {money(CARD)}; that last figure isn't from a cited source). Ring and Nest can't keep recordings this way, which is shown next to the figure.</p>
<p><sup>b</sup> <b>3 years, with plan</b> = price + 36 × the cheapest UK monthly plan that adds cloud recording for one device. Paying yearly is usually cheaper. The Reolink (£3.49) and EZVIZ (£4.99) plan prices aren't confirmed for the UK. Every model's sums are under <i>Details</i>.</p>
<p><b>Free-feature score (out of 8):</b> records for free (2 = out of the box, 1 = with extra kit or only briefly), free live view (1), free motion alerts (1), free smart detection (1), storage included in the box (1), local Home Assistant support (2 = official and local, 1 = unofficial or generic).</p>
<p>Batteries, electricity, installation (except Hikvision, where the price includes fitting) and future price rises are left out. Anything we haven't fully confirmed is listed under <i>Not yet verified</i> in each model's details. Spotted something wrong, or a paywall change? Tell us and we'll fix it.</p>
<p><b>Product photos</b> are the manufacturers' own, cropped and resized, from their product pages: {photo_credits}.{f" No reliable official photo for: {no_photo}." if no_photo else ""}</p>
</div>
<div><h2>Sources</h2><ol class="fns">{fn_list}</ol></div>
</section>
</div>
<div class="tray" id="tray" hidden><span id="tray-txt"></span><button type="button" id="tray-go">Compare</button><button type="button" class="ghost" id="tray-clear">Clear</button></div>
<script>
(function(){{
var D={data_js};
var $=function(s,c){{return (c||document).querySelector(s)}},$$=function(s,c){{return Array.prototype.slice.call((c||document).querySelectorAll(s))}};
var root=document.documentElement,mq=window.matchMedia('(prefers-color-scheme: dark)'),tb=$('#theme');
function isDark(){{var t=root.getAttribute('data-theme');return t?t==='dark':mq.matches}}
function syncTheme(){{var d=isDark();tb.setAttribute('aria-pressed',d);tb.lastChild.textContent=d?'Light mode':'Dark mode';tb.title=d?'Switch to light mode':'Switch to dark mode'}}
tb.onclick=function(){{var n=isDark()?'light':'dark';root.setAttribute('data-theme',n);try{{localStorage.setItem('theme',n)}}catch(e){{}}syncTheme()}};
if(mq.addEventListener)mq.addEventListener('change',syncTheme);
syncTheme();
var tbl=$('#tbl'),items=$$('tbody.item',tbl),maxEl=$('#f-max'),out=$('#f-max-out');
var skey='keep3',sdir=1,SDEF={{keep3:1,price:1,score:-1,recv:-1,nosub3:1,sub3:1,model:1}};
function apply(){{
 var rec=$('#f-rec').checked,ha=$('#f-ha').checked,pw=$$('.f-pw:checked').map(function(x){{return x.value}}),mx=+maxEl.value,n=0;
 out.textContent='£'+mx;
 items.forEach(function(t){{
  var ok=(!rec||t.dataset.rec==='yes')&&(!ha||+t.dataset.ha>0)&&(+t.dataset.price<=mx)&&
   (!pw.length||pw.some(function(p){{return t.dataset.power.split(' ').indexOf(p)>-1}}));
  t.hidden=!ok; if(ok)n++;
 }});
 $('#count').textContent=n; $('#empty').hidden=n>0;
 var s=items.slice().sort(function(a,b){{
  var x=skey==='model'?a.dataset.model:+a.dataset[skey],y=skey==='model'?b.dataset.model:+b.dataset[skey];
  if(x<y)return -sdir;if(x>y)return sdir;return +a.dataset.keep3-+b.dataset.keep3;
 }});
 s.forEach(function(t){{tbl.appendChild(t)}});
 $$('#tbl thead th[data-sort]').forEach(function(th){{th.setAttribute('aria-sort',th.dataset.sort===skey?(sdir>0?'ascending':'descending'):'none')}});
 $('#sort').value=skey;
}}
$$('#controls input').forEach(function(el){{el.addEventListener('input',apply);el.addEventListener('change',apply)}});
$('#sort').onchange=function(){{skey=this.value;sdir=SDEF[skey];apply()}};
$$('#tbl thead th[data-sort] button').forEach(function(b){{b.onclick=function(){{
 var k=b.parentNode.dataset.sort;
 if(k===skey)sdir=-sdir;else{{skey=k;sdir=SDEF[k]}}
 apply();
}}}});
$('#reset').onclick=function(){{$$('#controls input[type=checkbox]').forEach(function(c){{c.checked=false}});maxEl.value=maxEl.max;skey='keep3';sdir=1;apply()}};
$$('button.more').forEach(function(b){{b.onclick=function(){{var d=document.getElementById(b.getAttribute('aria-controls')),o=b.getAttribute('aria-expanded')==='true';b.setAttribute('aria-expanded',!o);b.textContent=o?'Details':'Hide';d.hidden=o}}}});
var reduce=window.matchMedia('(prefers-reduced-motion: reduce)');
$$('a.jump').forEach(function(a){{a.addEventListener('click',function(ev){{
 var rows=a.dataset.ids.split(' ').map(function(id){{return document.getElementById('m-'+id)}});
 if(rows.some(function(r){{return r.hidden}}))$('#reset').click();
 rows.sort(function(x,y){{return x.compareDocumentPosition(y)&4?-1:1}});
 ev.preventDefault();
 rows[0].scrollIntoView({{behavior:reduce.matches?'auto':'smooth',block:'center'}});
 if(history.replaceState)history.replaceState(null,'','#'+rows[0].id);
 rows.forEach(function(r){{r.classList.remove('flash');void r.offsetWidth;r.classList.add('flash');clearTimeout(r._ft);r._ft=setTimeout(function(){{r.classList.remove('flash')}},1900)}});
 var cb=rows[0].querySelector('input.cmp'); if(cb)cb.focus({{preventScroll:true}});
}})}});
var ROWS=[['Records free?','rec'],['Price','price'],['Free features','score'],['3 yrs, no plan','nosub3'],['3 yrs, with plan','sub3'],['Best for','best'],['Main catch','catch'],['Power','power'],['Storage','storage'],['Live view','live'],['Motion alerts','alerts'],['Smart detection','ai'],['History, no plan','history'],['Behind the paywall','paywalled'],['Plans','plan'],['Home Assistant','ha'],['Wi-Fi','wifi']];
function esc(s){{var d=document.createElement('div');d.textContent=s;return d.innerHTML}}
function sel(){{return $$('input.cmp:checked').map(function(c){{return c.value}})}}
function tray(){{
 var s=sel(); $$('input.cmp').forEach(function(c){{c.disabled=!c.checked&&s.length>=3}});
 $('#tray').hidden=s.length===0;
 $('#tray-txt').textContent=s.length===1?'1 selected (tick 1 or 2 more)':s.length+' selected';
 $('#tray-go').disabled=s.length<2;
 if(!$('#compare').hidden){{s.length>=2?render():($('#compare').hidden=true)}}
}}
function render(){{
 var s=sel(),h='<thead><tr><th><span class="vh">Spec</span></th>'+s.map(function(id){{
  var d=D[id];
  return '<th scope="col"><span class="cmp-name">'+esc(d.name)+'</span>'+(d.img?'<span class="cmp-photo"><img src="'+esc(d.img)+'" width="45" height="60" alt="" loading="lazy" decoding="async"></span>':'')+'</th>';
 }}).join('')+'</tr></thead><tbody>';
 ROWS.forEach(function(r){{h+='<tr><th scope="row">'+r[0]+'</th>'+s.map(function(id){{return '<td>'+esc(D[id][r[1]])+'</td>'}}).join('')+'</tr>'}});
 $('#cmp-table').innerHTML=h+'</tbody>'; $('#compare').hidden=false;
}}
$$('input.cmp').forEach(function(c){{c.addEventListener('change',tray)}});
$('#tray-go').onclick=function(){{render();$('#compare').scrollIntoView({{behavior:reduce.matches?'auto':'smooth',block:'start'}})}};
$('#tray-clear').onclick=function(){{$$('input.cmp').forEach(function(c){{c.checked=false}});$('#compare').hidden=true;tray()}};
$('#cmp-close').onclick=function(){{$('#compare').hidden=true}};
apply();
}})();
</script>
</body></html>'''
for _f in ("index.html","doorbells.html"): open(os.path.join(ROOT,_f),"w",encoding="utf-8").write(page)
print(len(ROWS),"rows written")
for r in sorted(ROWS,key=lambda r:r["keep3"]): print(f"{r['brand']:14} {r['model']:38} score {r['score_total']}  nosub {r['nosub3']:8.2f}  sub {r['sub3'] if r['sub3'] else '-':>8}  keep {r['keep3']:.2f}")
