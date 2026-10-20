"""Single source of truth for the SubFree UK doorbell table.
Generates data/doorbells.csv, data/doorbells.md and the site (index.html + doorbells.html at the repo root) from ROWS below.
Run from anywhere: python3 build/build.py
"""
import csv, html, json
import os
from urllib.parse import urlparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
HERE = os.path.dirname(os.path.abspath(__file__))

CHECKED = "19 October 2026"
GITHUB = "https://github.com/lydenyardley/subfree-uk"
CARD = 10.00   # ASSUMPTION (not cited): typical price of a 64 GB microSD card / USB stick
MINP = 40      # lower end of the price slider; the cheapest doorbell here is £44.99
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
 "nest_plans": ("Google Home Premium: what you get", "https://support.google.com/googlehome/answer/9233159?hl=en-GB"),
 "eufy_prod": ("eufy UK: E340", "https://www.eufy.com/uk/products/T8214311"),
 "eufy_cloud": ("eufy UK cloud plans", "https://www.eufy.com/uk/cloud-storage"),
 "verge_eufy": ("The Verge, Nov 2022", "https://www.theverge.com/2022/11/30/23486753/anker-eufy-security-camera-cloud-private-encryption-authentication-storage"),
 "sha_nosub": ("smarthomeassistant.co.uk guide", "https://smarthomeassistant.co.uk/articles/smart-security/best-video-doorbell-no-subscription-uk"),
 "reo_store": ("Reolink UK store", "https://store.reolink.com/gb/video-doorbells/"),
 "reo_batt": ("Reolink UK battery doorbells", "https://store.reolink.com/gb/wireless-doorbell-camera/"),
 "screwfix_reo": ("Screwfix: Reolink Battery", "https://www.screwfix.com/p/reolink-d340b-wired-or-wireless-battery-video-doorbell-black/471ak"),
 "reo_cloud": ("Reolink Cloud UK plans", "https://cloud.reolink.com/cloud-plan"),
 "reo_faq": ("Reolink doorbell FAQ", "https://support.reolink.com/articles/29213749981209-Reolink-Video-Doorbell-Cameras-FAQ/"),
 "reo_hub": ("Reolink UK Home Hub", "https://store.reolink.com/gb/home-hub-series/"),
 "ha_reo": ("Home Assistant: Reolink", "https://www.home-assistant.io/integrations/reolink/"),
 "tapo_d230": ("Tapo UK: D230S1", "https://uk.store.tapo.com/products/tapo-d230s1-smart-battery-video-doorbell"),
 "tapo_td21": ("Tapo UK: TD21", "https://uk.store.tapo.com/products/battery-video-doorbell-2k-3mp-colour-night-vision-tapo-td21"),
 "tapo_care": ("Tapo Care UK", "https://uk.store.tapo.com/pages/tapo-care"),
 "ha_tplink": ("Home Assistant: TP-Link Smart Home", "https://www.home-assistant.io/integrations/tplink/"),
 "tapo_td21_manual": ("Tapo TD21 setup guide", "https://www.tapo.com/en/manuals/1094/"),
 "er_tapo": ("Expert Reviews: EZVIZ EP3x Pro review", "https://www.expertreviews.co.uk/technology/home-security/ezviz-ep3x-pro-video-doorbell-review"),
 "argos_arlo": ("Argos: Arlo doorbell", "https://www.argos.co.uk/product/4379311"),
 "arlo_plans": ("Arlo UK plan prices", "https://www.arlo.com/en_gb/serviceplans"),
 "arlo_doorbell": ("Arlo 2nd-gen doorbell FAQ", "https://www.arlo.com/en_gb/support/faq/device-features/arlo-video-doorbell-2nd-generation-faq"),
 "arlo_faq": ("Arlo UK plans FAQ", "https://www.arlo.com/en_gb/support/faq/subscriptions-and-payments/what-arlo-subscription-plans-and-cloud-recording-options-are-available"),
 "arlo_blog": ("Arlo UK blog", "https://www.arlo.com/en_gb/blog/smart-security/should-you-have-a-video-doorbell-without-a-subscription"),
 "arlo_hubcompat": ("Arlo SmartHub compatibility", "https://www.arlo.com/en_gb/support/faq/connectivity-and-integrations/arlo-smarthub-and-base-station-compatibility"),
 "amz_arlohub": ("Amazon UK: Arlo SmartHub", "https://www.amazon.co.uk/Arlo-Certified-Accessory-Designed-Floodlight/dp/B08516SJZ9"),
 "tr_arlo": ("Trusted Reviews, 2026", "https://www.trustedreviews.com/reviews/arlo-essential-3-2k-security-camera"),
 "ambient_arlo": ("The Ambient", "https://www.the-ambient.com/reviews/arlo-pro-6-2k-review/"),
 "amz_aqara": ("Amazon UK: Aqara G4", "https://www.amazon.co.uk/Aqara-Doorbell-Included-Recognition-Automations/dp/B0BPHTL7MG"),
 "aqara_eu": ("Aqara EU store", "https://eu.aqara.com/products/aqara-video-doorbell-g4"),
 "aqara_specs": ("Aqara G4 specifications", "https://www.aqara.com/us/product/smart-video-doorbell-g4/specs/"),
 "ha_homekit": ("Home Assistant: HomeKit Device", "https://www.home-assistant.io/integrations/homekit_controller"),
 "amz_blink": ("Amazon UK: Blink 2K+", "https://www.amazon.co.uk/blink-battery-doorbell-2k-/dp/B0G62K1Y6C"),
 "camel_sm2": ("camelcamelcamel (Sync Module 2)", "https://uk.camelcamelcamel.com/product/B08BJ9ZCZC"),
 "blink_plans": ("Blink UK plans", "https://blinkforhome.com/plans-uk"),
 "blink_sm2": ("Blink Sync Module 2 FAQ", "https://support.blinkforhome.com/en_GB/faq-sm2/faq-sync-module-2"),
 "ha_blink": ("Home Assistant: Blink", "https://www.home-assistant.io/integrations/blink/"),
 "amz_ep3x": ("Amazon UK: EZVIZ EP3x Pro", "https://www.amazon.co.uk/EZVIZ-Dual-Lens-Doorbell-Detection-EP3X/dp/B0F2DXSGFD"),
 "ezviz_blog": ("EZVIZ UK: no-subscription guide", "https://www.ezviz.com/uk/blog/detail/best-video-doorbells-without-monthly-subscription-fees/2609214160772537"),
 "ezviz_cloud": ("EZVIZ CloudPlay (EU prices)", "https://www.ezviz.com/page/cloudplay"),
 "ezviz_terms": ("EZVIZ CloudPlay UK terms", "https://www.ezviz.com/uk/legal/cloudplay-paid-subscription-terms"),
 "ha_ezviz": ("Home Assistant: EZVIZ", "https://www.home-assistant.io/integrations/ezviz/"),
 "ertech_db2": ("ER Tech (UK retailer)", "https://www.ertech.co.uk/product/db2-pro/"),
 "eagle_hik": ("Eagle Security Solutions", "https://eaglesecuritysolutions.co.uk/p/door-entry-systems/wireless-intercoms/hikvision-ds-kb6003-wip-video-doorbell-fully-installed/"),
 "hik_ds": ("Hikvision datasheet", "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000083/S000000126/S000000127/OFR000160/M000001570/Data_Sheet/UD04258B_Spec-of-DS-KB6003-WIP-Wi-Fi-Doorbell_V1.4.6_20170519.pdf"),
 "hik_4gon": ("4Gon: Hikvision doorbell (discontinued)", "https://www.4gon.co.uk/hikvision-24v-dc-wifi-video-doorbell-dskb6003wip-p-8309.html"),
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
 unverified=""),
dict(id="nest", brand="Google Nest", model="Doorbell (battery)", rec="brief", power=["battery","wired"], ha=0,
 price=179.99, price_note="Google Store UK", price_src="nest_prod",
 extra=0, extra_note="", free_records=False,
 sub=8.00, sub_name="Google Home Premium Standard",
 best="Google Home households who want polished smart alerts",
 catch="Only 3 hours of free history. Anything longer is £8 a month.",
 storage="None", live="Yes", alerts="Yes",
 ai="Free: person, parcel, animal and vehicle alerts; Google sells 'smarter' AI notifications as Premium",
 history="3 hours of event clips", paywalled="30 or 60 days of history, AI notifications, familiar faces, Gemini search. No 24/7 recording on this model at any price",
 sub_text="Google Home Premium Standard £8/month (£80/year); Advanced £16/month (£160/year)",
 ha_text="Official integration, but it goes through Google's cloud (Cloud Push) and needs a one-off US$5 Google developer fee.",
 wifi="2.4 GHz only (5 GHz is US-only)",
 score=dict(rec=1,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["nest_prod","nest_prem","nest_plans","ha_nest"],
 unverified=""),
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
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=1),
 src=["eufy_prod","eufy_cloud","verge_eufy","sha_nosub"],
 unverified=""),
dict(id="reo-wifi", brand="Reolink", model="Video Doorbell WiFi", rec="yes", power=["wired"], ha=2,
 price=93.49, price_note="Reolink UK sale price (RRP £109.99)", price_src="reo_store",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=4.58, sub_name="Reolink Cloud Upgraded single-device",
 best="Homes with existing doorbell wiring, plus Home Assistant or NVR users",
 catch="Needs doorbell transformer wiring, and the microSD card is sold separately.",
 storage="microSD (up to 256 GB) and/or a Reolink NVR; RTSP/ONVIF", live="Yes", alerts="Yes",
 ai="Free: person detection", history="Yes, motion-triggered or 24/7 recording to card or NVR",
 paywalled="Nothing. Reolink Cloud is optional",
 sub_text="Optional Reolink Cloud. UK £4.58/month, or £2.71/month billed yearly (£32.52/year) for 1 camera",
 ha_text="Official, fully local integration (Local Push, top 'Platinum' quality rating); works with no internet connection.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=2),
 src=["reo_store","ha_reo","reo_cloud","sha_nosub"],
 unverified=""),
dict(id="reo-poe", brand="Reolink", model="Video Doorbell PoE", rec="yes", power=["poe"], ha=2,
 price=69.99, price_note="Reolink UK sale price (RRP £99.99)", price_src="reo_store",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=None, sub_name="No Reolink Cloud plan",
 best="The most reliable, fully local setup, if you can run an Ethernet cable",
 catch="Needs an Ethernet cable to the door and a PoE switch or injector.",
 storage="microSD and/or NVR; RTSP/ONVIF", live="Yes", alerts="Yes", ai="Free: person detection",
 history="Yes, motion-triggered or 24/7 recording", paywalled="Nothing",
 sub_text="None. Reolink's doorbell FAQ says the PoE model cannot use Reolink Cloud; it records to microSD or an NVR",
 ha_text="Official, fully local integration (Local Push, Platinum).", wifi="Wired Ethernet",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=2),
 src=["reo_store","ha_reo","reo_faq"],
 unverified=""),
dict(id="reo-batt", brand="Reolink", model="Video Doorbell (Battery)", rec="yes", power=["battery","wired"], ha=1,
 price=99.99, price_note="Screwfix, includes 64 GB card (Reolink UK also £99.99)", price_src="screwfix_reo",
 extra=0, extra_note="64 GB card included (Screwfix)", free_records=True,
 sub=4.17, sub_name="Reolink Cloud Standard (up to 5 cameras)",
 best="Battery install with 5 GHz Wi-Fi and no fees",
 catch="Footage sits on a card in the doorbell itself unless you add a £109.99 Home Hub (bundle £180.49).",
 storage="microSD in the doorbell, or a Home Hub indoors (up to 1 TB)", live="Yes", alerts="Yes",
 ai="Free: person, vehicle and package detection", history="Yes, on card or hub", paywalled="Nothing",
 sub_text="Optional Reolink Cloud. UK £4.17/month, or £2.87/month billed yearly (£34.44/year) for up to 5 cameras",
 ha_text="Official integration through a Reolink Home Hub or NVR, which streams the battery doorbell locally.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=1),
 src=["screwfix_reo","reo_batt","reo_hub","reo_cloud","ha_reo"],
 unverified=""),
dict(id="tapo-d230", brand="TP-Link Tapo", model="D230S1", rec="yes", power=["battery"], ha=1,
 price=84.99, price_note="Tapo UK (RRP £94.99)", price_src="tapo_d230",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=2.99, sub_name="Tapo Care",
 best="An easy battery doorbell that keeps footage indoors on its chime/hub",
 catch="The microSD card is extra, and Home Assistant gets settings and alerts but not the live video.",
 storage="microSD (up to 512 GB) in the indoor H200 hub", live="Yes", alerts="Yes",
 ai="Free: person detection", history="Yes, on the hub's card",
 paywalled="30-day cloud history, snapshot notifications, Smart Sort",
 sub_text="Optional Tapo Care from £2.99/month or £29.49/year",
 ha_text="Official TP-Link Smart Home integration, polled locally for settings and motion alerts. Hub-attached cameras still have no live view in Home Assistant.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["tapo_d230","tapo_care","ha_tplink","er_tapo"],
 unverified=""),
dict(id="tapo-td21", brand="TP-Link Tapo", model="TD21", rec="yes", power=["battery"], ha=0,
 price=44.99, price_note="Tapo UK sale price (RRP £56.00)", price_src="tapo_td21",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=2.99, sub_name="Tapo Care",
 best="The tightest budget",
 catch="Basic, and the microSD card sits in the doorbell, so a thief takes the footage with it.",
 storage="microSD up to 512 GB, in the doorbell itself", live="Yes", alerts="Yes", ai="Free: person detection",
 history="Yes, on card", paywalled="30-day cloud history, snapshot notifications, Smart Sort",
 sub_text="Optional Tapo Care from £2.99/month",
 ha_text="Not listed as supported by Home Assistant's official TP-Link integration, and no local route is documented.", wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["tapo_td21","tapo_care","tapo_td21_manual","ha_tplink"],
 unverified=""),
dict(id="arlo", brand="Arlo", model="Essential Video Doorbell 2K (2nd gen)", rec="kit", power=["battery"], ha=0,
 power_note="Can be wired to an existing chime for trickle charging, but still runs on its battery.",
 price=84.99, price_note="Argos half price, doorbell + chime bundle (was £169.99)", price_src="argos_arlo",
 extra=115.07, extra_note="+ Arlo SmartHub £105.07 + USB stick", free_records=True,
 sub=7.99, sub_name="Arlo Secure (1 camera)",
 best="People who already own Arlo cameras",
 catch="Recording needs a £7.99/month plan or a separate hub costing about £105.",
 storage="Only through an Arlo SmartHub (VMB4540, USB) or a Base Station", live="Yes", alerts="Yes",
 ai="Paid", history="None without a hub",
 paywalled="Cloud recording (7, 14 or 30 days depending on plan), object detection, activity zones, theft replacement",
 sub_text="Arlo Secure £7.99/month (1 camera, 7 days), Multi-Camera £12.99, Secure Plus £19.99 (14 days), Secure Pro £24.99",
 ha_text="No official integration; only a community add-on that goes through Arlo's cloud.",
 wifi="2.4 GHz only",
 score=dict(rec=1,live=1,alerts=1,ai=0,storage=0,ha=0),
 src=["argos_arlo","arlo_blog","arlo_plans","arlo_faq","arlo_doorbell","arlo_hubcompat","amz_arlohub","tr_arlo","ambient_arlo"],
 unverified=""),
dict(id="aqara-g4", brand="Aqara", model="Video Doorbell G4", rec="yes", power=["battery","wired"], ha=1,
 price=84.99, price_note="Amazon UK", price_src="amz_aqara",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=None, sub_name="No plan needed (iCloud+ only for HomeKit Secure Video)",
 best="Apple Home users",
 catch="Runs on AA batteries unless wired, and setting it up in Home Assistant is fiddly.",
 storage="microSD (up to 512 GB) in the indoor chime", live="Yes", alerts="Yes",
 ai="Free: face recognition on the device", history="Yes, on the chime's card (24/7 only when wired)",
 paywalled="Nothing essential. HomeKit Secure Video needs Apple's paid iCloud+",
 sub_text="None needed",
 ha_text="Reported to work locally through Home Assistant's HomeKit Device integration; two-way audio isn't available there.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["amz_aqara","aqara_eu","aqara_specs","ha_homekit"],
 unverified=""),
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
 unverified=""),
dict(id="ezviz-ep3x", brand="EZVIZ", model="EP3x Pro", rec="yes", power=["battery"], ha=0,
 price=79.99, price_note="Amazon UK (list price £89.99)", price_src="amz_ep3x",
 extra=0, extra_note="32 GB storage built in", free_records=True,
 sub=4.99, sub_name="EZVIZ CloudPlay 7-day",
 best="Two cameras on a budget, with storage built in",
 catch="Expert Reviews found its motion detection unreliable and the app confusing.",
 storage="32 GB built in, no card needed", live="Yes", alerts="Yes",
 ai="Free: human and package detection", history="Yes, on built-in storage",
 paywalled="Nothing essential. CloudPlay is optional",
 sub_text="Optional CloudPlay. UK price is app-only; EU €4.99/month (7 days), so treat the plan column as an estimate",
 ha_text="Official integration, but it goes through EZVIZ's cloud; this battery model isn't named in its supported list.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=0),
 src=["amz_ep3x","ezviz_blog","er_tapo","ezviz_cloud","ezviz_terms","ha_ezviz"],
 unverified="CloudPlay's UK price is app-only, so the £4.99 in the plan column is the published EU price, not a UK quote."),
dict(id="ezviz-db2", brand="EZVIZ", model="DB2 Pro Kit", rec="yes", power=["battery"], ha=0,
 price=114.99, price_note="ER Tech, UK retailer", price_src="ertech_db2",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=4.99, sub_name="EZVIZ CloudPlay 7-day",
 best="Flats and rentals: no wiring, and footage stays indoors in the chime",
 catch="2.4 GHz Wi-Fi only, and the card is sold separately.",
 storage="microSD (up to 256 GB) in the included indoor chime", live="Yes", alerts="Yes",
 ai="Free: PIR plus human-shape detection", history="Yes, on the chime's card", paywalled="Nothing essential",
 sub_text="Optional CloudPlay. UK price is app-only; EU €4.99/month (7 days), so treat the plan column as an estimate",
 ha_text="Official integration, but it goes through EZVIZ's cloud; this battery model isn't named in its supported list.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["ertech_db2","ezviz_blog","ezviz_cloud","ezviz_terms","ha_ezviz"],
 unverified="CloudPlay's UK price is app-only, so the £4.99 in the plan column is the published EU price, not a UK quote."),
dict(id="hik", brand="Hikvision", model="DS-KB6003-WIP", rec="yes", power=["wired"], ha=1,
 price=295.00, price_note="Only UK listing found (fitted install); the model is discontinued", price_src="eagle_hik",
 extra=CARD, extra_note="+ microSD card", free_records=True,
 sub=None, sub_name="No plan",
 best="Only worth it if an installer is fitting a Hikvision system anyway",
 catch="Discontinued by Hikvision, and the only UK listing we found is a fitted install at £295.",
 storage="microSD up to 128 GB; RTSP to an NVR", live="Yes (Hik-Connect app)", alerts="Yes (motion)",
 ai="None", history="Yes, on card or NVR", paywalled="Nothing", sub_text="None",
 ha_text="Works as a generic RTSP camera.", wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=0,storage=0,ha=1),
 src=["eagle_hik","hik_ds","hik_4gon"],
 unverified=""),
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

# 'brief' is a time limit, not missing hardware: Nest keeps 3 hours with no kit.
REC_LABEL = {"yes":"Yes", "kit":"Only with extra kit", "brief":"Only briefly (3 hrs)", "no":"No"}
REC_RANK = {"yes":2, "kit":1, "brief":1, "no":0}
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
      f"- **Home Assistant:** {r['ha_text']}", *([f"- **Unverified:** {r['unverified']}"] if r["unverified"] else []),
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
    # The thumbnail sits beside the model name, so it is decorative and must not
    # repeat that name. The large photo is the only name in the details panel.
    if m.get("placeholder") or not m:
        attrs = 'aria-hidden="true"' if size == "sm" else f'role="img" aria-label="No photo available for {e(name)}"'
        return f'<span class="ph ph-{size}" {attrs} style="width:{w}px;height:{h}px"><span>No photo</span></span>'
    alt = "" if size == "sm" else e(name)
    return f'<img class="ph ph-{size}" src="img/{r["id"]}-{size}.webp" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{alt}">'

def zoom(r, size):
    # Both sizes are 2x files, so the lightbox shows the large one at its own
    # width. Placeholders stay plain: there is nothing bigger to open.
    m = IMG.get(r["id"], {})
    if m.get("placeholder") or not m:
        return photo(r, size)
    name = e(f"{r['brand']} {r['model']}")
    return (f'<button type="button" class="zoom" data-full="img/{r["id"]}-lg.webp" data-name="{name}" '
            f'aria-label="View {name} photo full size">{photo(r, size)}<span class="zi" aria-hidden="true"></span></button>')

# Short-answer verdicts, colour-coded and repeated on the matching rows.
# One row owns "Best overall"; the other variants name the case they win.
VERDICT = {"reo-poe":"best","reo-wifi":"wired","reo-batt":"batt","tapo-d230":"easy","ring":"avoid","blink":"avoid","arlo":"avoid"}
V_LABEL = {"best":"Best overall","wired":"Best with doorbell wiring","batt":"Best battery, no fees","easy":"Easiest battery setup","avoid":"Avoid without a plan"}
V_TONE = {"best":"best","wired":"best","batt":"batt","easy":"batt","avoid":"avoid"}
def vlink(ids, text): return f'<a class="jump" href="#m-{ids[0]}" data-ids="{" ".join(ids)}">{text}</a>'

rows_html=[]
for i,r in enumerate(ROWS):
    pw=" ".join(r["power"])
    sc=r["score_total"]
    v=VERDICT.get(r["id"])
    tone=V_TONE[v] if v else ""
    vattr=f' data-v="{tone}"' if tone else ""
    vtag=f'<span class="vtag v-{tone}">{V_LABEL[v]}</span>' if v else ""
    unv=f'<p class="unverified"><b>Not yet verified:</b> {e(r["unverified"])}</p>' if r["unverified"] else ""
    pnote='. ' + e(r["power_note"]) if r.get("power_note") else ""
    rows_html.append(f'''<tbody class="item" id="m-{r['id']}" data-id="{r['id']}"{vattr} data-rec="{r['rec']}" data-recv="{REC_RANK[r['rec']]}" data-ha="{r['ha']}" data-power="{pw}" data-price="{r['price']}" data-keep3="{r['keep3']}" data-nosub3="{r['nosub3']}" data-sub3="{r['sub3'] if r['sub3'] is not None else 0}" data-score="{sc}" data-model="{e((r['brand']+' '+r['model']).lower())}" data-idx="{i}">
<tr class="main">
<td class="c-cmp"><input type="checkbox" class="cmp" value="{r['id']}" aria-label="Compare {e(r['brand'])} {e(r['model'])}"></td>
<th scope="row" class="c-model"><div class="mcell">{zoom(r,"sm")}<div><span class="brand">{e(r['brand'])}</span> <span class="mname">{e(r['model'])}</span>{vtag}<span class="best">Best for: {e(r['best'])}</span></div></div></th>
<td class="c-rec" data-label="Records free?"><span class="rec rec-{r['rec']}">{REC_LABEL[r['rec']]}</span></td>
<td class="c-price num">{gbp(r['price'])}</td>
<td class="c-score" data-label="Free features"><span class="score"><b>{sc}</b>/8</span><span class="bar" aria-hidden="true"><i data-w="{sc/8*100:.0f}" style="transform:scaleX({sc/8:.3f})"></i></span></td>
<td class="c-nosub num" data-label="3 yrs, no plan">{gbp(r['nosub3'])}{'' if r['free_records'] else '<span class="note">no recordings</span>' if r['rec']=='no' else '<span class="note">3 hrs history</span>'}</td>
<td class="c-sub num" data-label="3 yrs, with plan">{gbp(r['sub3']) if r['sub3'] is not None else '<span class="noplan">No plan</span>'}</td>
<td class="c-catch" data-label="Main catch">{e(r['catch'])}<div class="more-w"><button type="button" class="more" aria-expanded="false" aria-controls="d-{r['id']}">Details</button></div></td>
</tr>
<tr class="detail" id="d-{r['id']}" hidden><td colspan="8"><div class="dgrid">
<figure class="dimg">{zoom(r,"lg")}</figure>
<dl>
<dt>Power</dt><dd>{" / ".join(POWER_LABEL[p] for p in r['power'])}; Wi-Fi: {e(r['wifi'])}{pnote}</dd>
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
{unv}
<p class="srcs">Sources {fn(r['src'])}</p></td></tr>
</tbody>''')

data_js = json.dumps({r["id"]:{
 "name":f"{r['brand']} {r['model']}","rec":REC_LABEL[r["rec"]],"price":gbp(r["price"]),"score":f"{r['score_total']}/8",
 "nosub3":gbp(r["nosub3"]),"sub3":gbp(r["sub3"]) if r["sub3"] is not None else "No plan","keep3":r["keep3"],"best":r["best"],"catch":r["catch"],"power":" / ".join(POWER_LABEL[p] for p in r["power"]),
 "storage":r["storage"],"live":r["live"],"alerts":r["alerts"],"ai":r["ai"],"history":r["history"],"paywalled":r["paywalled"],
 "plan":r["sub_text"],"ha":r["ha_text"],"wifi":r["wifi"],
 "img":"" if IMG.get(r["id"],{}).get("placeholder") else f'img/{r["id"]}-sm.webp',
 "imgLg":"" if IMG.get(r["id"],{}).get("placeholder") else f'img/{r["id"]}-lg.webp'} for r in ROWS}, ensure_ascii=False)

# 52 numbered lines are hard to scan, so the list is grouped by the host the
# link points at. Real <li value> keeps every footnote number stable.
HOST_PREFIX = {"www", "en", "en-uk", "uk", "eu", "us", "store", "cloud", "support", "blog"}
def src_host(url):
    parts = urlparse(url).netloc.lower().split(".")
    while len(parts) > 2 and parts[0] in HOST_PREFIX: parts = parts[1:]
    return ".".join(parts)
groups={}
for k in order: groups.setdefault(src_host(S[k][1]), []).append(k)
fn_list="".join(
    f'<section class="fns-g"><h3>{e(host)}</h3><ol class="fns">'
    + "".join(f'<li id="fn{FN[k]}" value="{FN[k]}"><a href="{e(S[k][1])}" rel="nofollow noopener noreferrer">{e(S[k][0])}</a></li>' for k in keys)
    + '</ol></section>'
    for host, keys in sorted(groups.items(), key=lambda kv: FN[kv[1][0]]))
maxp=int(max(r["price"] for r in ROWS)+5)
byid={r["id"]:r for r in ROWS}
photo_credits=", ".join(f'<a href="{e(IMG[r["id"]]["page"])}" rel="nofollow noopener noreferrer">{e(r["brand"])} {e(r["model"])}</a>' for r in ROWS if not IMG.get(r["id"],{}).get("placeholder"))
no_photo=", ".join(f'{e(r["brand"])} {e(r["model"])}' for r in ROWS if IMG.get(r["id"],{}).get("placeholder"))

page=f'''<!doctype html>
<html lang="en-GB" class="no-js"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta name="color-scheme" content="light dark">
<title>Video doorbells that work without a subscription (UK) | SubFree UK</title>
<meta name="description" content="{len(ROWS)} UK video doorbells compared: what is free, what is paywalled, and what each costs over three years.">
<link rel="canonical" href="https://lydenyardley.github.io/subfree-uk/">
<meta property="og:type" content="website">
<meta property="og:title" content="Video doorbells that work without a subscription (UK)">
<meta property="og:description" content="{len(ROWS)} UK video doorbells compared: what is free, what is paywalled, and what each costs over three years.">
<meta property="og:url" content="https://lydenyardley.github.io/subfree-uk/">
<meta property="og:image" content="https://lydenyardley.github.io/subfree-uk/img/reo-poe-lg.webp">
<meta property="og:image:alt" content="Reolink Video Doorbell PoE">
<meta name="twitter:card" content="summary">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<script>document.documentElement.className="js";try{{var t=localStorage.getItem("theme");if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script>
<style>
:root{{--ink:#1a1a1a;--ink2:#555;--ink3:#767676;--rule:#d9d6cf;--rule2:#ece9e2;--paper:#fff;--tint:#f6f4ef;--acc:#0f5c4d;
--v-best:#17694a;--v-batt:#1f5d96;--v-avoid:#a33b26;--hl:#fff1b8;--tray:#332f2a;--tray-ink:#f6f3ec;--imgbg:#fff;--imgf:none;
--serif:Charter,"Bitstream Charter","Iowan Old Style","Sitka Text",Cambria,Georgia,serif;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color-scheme:light}}
:root[data-theme=dark]{{--ink:#e9e7e2;--ink2:#b3b0a9;--ink3:#8f8c86;--rule:#3b3a37;--rule2:#2b2a28;--paper:#151514;--tint:#1e1e1c;--acc:#62c2a8;
--v-best:#5fc896;--v-batt:#80b4ea;--v-avoid:#f08a74;--hl:#4a4320;--tray:#2b2a28;--tray-ink:#e9e7e2;--imgbg:#e9e7e2;--imgf:brightness(.84);color-scheme:dark}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--ink:#e9e7e2;--ink2:#b3b0a9;--ink3:#8f8c86;--rule:#3b3a37;--rule2:#2b2a28;--paper:#151514;--tint:#1e1e1c;--acc:#62c2a8;
--v-best:#5fc896;--v-batt:#80b4ea;--v-avoid:#f08a74;--hl:#4a4320;--tray:#2b2a28;--tray-ink:#e9e7e2;--imgbg:#e9e7e2;--imgf:brightness(.84);color-scheme:dark}}}}
*{{box-sizing:border-box}}
[hidden]{{display:none!important}}
.skip{{position:absolute;top:0;left:0;z-index:20;transform:translateY(-120%);background:var(--paper);border:1px solid var(--ink);padding:0.5rem 1rem;font:600 14px/1.4 var(--sans);color:var(--ink)}}
.skip:focus{{transform:none}}
.no-js .controls{{display:none}}
.no-js #theme{{display:none}}
.no-js .more-w{{display:none}}
.nojs{{margin:1rem 0;padding:1rem;border:1px solid var(--rule);font-size:14px;color:var(--ink2)}}
html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.45 var(--sans);transition:background-color .18s,color .18s}}
a{{color:var(--acc)}}
p{{max-width:65ch}}
sup{{font-size:11px}}
.wrap{{max-width:1440px;margin:0 auto;padding:0 1rem}}
.mast{{display:flex;justify-content:space-between;align-items:center;gap:1rem;border-bottom:1px solid var(--ink);padding:1rem 0;font:600 12px/1 var(--sans);letter-spacing:.08em;text-transform:uppercase}}
.mast>div>span{{color:var(--ink3);font-weight:500;margin-left:1rem;letter-spacing:.04em}}
#theme{{position:relative;font:500 12px/1 var(--sans);letter-spacing:.02em;text-transform:none;background:none;color:var(--ink);border:1px solid var(--rule);padding:0 1rem;cursor:pointer;display:inline-flex;align-items:center;gap:0;white-space:nowrap;min-height:24px}}
#theme:hover{{border-color:var(--ink)}}
#theme i{{display:inline-block;width:10px;height:10px;margin-right:0.4rem;border-radius:50%;border:1.5px solid currentColor;background:linear-gradient(90deg,currentColor 50%,transparent 50%);transition:transform .18s ease}}
:root[data-theme=dark] #theme i{{transform:rotate(180deg)}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]) #theme i{{transform:rotate(180deg)}}}}
#theme::after{{content:"";position:absolute;inset:-10px -8px}}
header.intro{{padding:2rem 0;display:grid;grid-template-columns:minmax(0,1.618fr) 1fr;gap:2rem;border-bottom:1px solid var(--rule)}}
h1{{font-weight:700;font-size:clamp(27px,3.5vw,50px);line-height:1.12;font-family:var(--serif);margin:0 0 1rem;letter-spacing:-.01em;max-width:22ch}}
.dek{{font:18px/1.45 var(--serif);color:var(--ink2);margin:0 0 1rem}}
.meta{{font-size:13px;color:var(--ink2);margin:0}}
.meta b{{color:var(--ink)}}
.verdict{{border-left:1px solid var(--rule);padding:0 0 0 2rem;font-size:14px}}
.verdict h2{{font:700 13px/1.2 var(--sans);text-transform:uppercase;letter-spacing:.06em;margin:0 0 1rem}}
.verdict p{{margin:0 0 1rem;padding-left:1rem;border-left:3px solid var(--vc)}}
.verdict p b{{color:var(--vc)}}
.vshort{{display:none;margin:1rem 0 0;font-size:14px;line-height:1.45}}
.v-best{{--vc:var(--v-best)}} .v-batt{{--vc:var(--v-batt)}} .v-avoid{{--vc:var(--v-avoid)}}
a.jump{{color:inherit;font-weight:600;text-decoration:underline;text-decoration-color:var(--vc);text-decoration-thickness:2px;text-underline-offset:2px}}
a.jump:hover{{color:var(--vc)}}
.vtag{{display:block;margin-top:0;padding:0.5rem 0 0;font:600 12px/1.25 var(--sans);letter-spacing:.01em;color:var(--vc)}}
.vtag::before{{content:"";display:inline-block;width:7px;height:7px;background:var(--vc);margin-right:0.5rem;vertical-align:0}}
tbody.item[data-v=best]{{--vc:var(--v-best)}} tbody.item[data-v=batt]{{--vc:var(--v-batt)}} tbody.item[data-v=avoid]{{--vc:var(--v-avoid)}}
tbody.item[data-v] tr.main>td.c-cmp{{border-left:3px solid var(--vc)}}
.controls{{display:flex;flex-wrap:wrap;gap:1rem 2rem;align-items:flex-start;padding:1rem 0;border-bottom:1px solid var(--rule)}}
.filters>summary{{display:none}}
.fbody{{display:flex;flex-wrap:nowrap;gap:1rem 2rem;align-items:flex-start}}
fieldset{{border:0;margin:0;padding:0;min-width:0}}
legend,.lab{{font:600 11px/1 var(--sans);text-transform:uppercase;letter-spacing:.07em;color:var(--ink2);padding:0;margin-bottom:1rem;display:block}}
.opts{{display:flex;flex-wrap:wrap;gap:1rem}}
.opts label{{display:inline-flex;align-items:center;gap:0.5rem;min-height:24px;font-size:14px;cursor:pointer;white-space:nowrap}}
.hint{{margin:0.5rem 0 0;font-size:12px;line-height:1.35;color:var(--ink3);max-width:26ch}}
input[type=checkbox]{{accent-color:var(--acc);width:15px;height:15px;margin:0}}
/* One range input per handle, stacked, so each keeps its own keyboard value.
   Only the thumbs take pointer events, which is what lets them overlap. */
.range{{flex:1 1 180px;min-width:170px;max-width:320px}}
.dual{{position:relative;height:24px;width:100%;--thumb:18px}}
/* Firefox draws a smaller thumb, so the track inset has to match it too. */
@supports selector(::-moz-range-thumb){{.dual{{--thumb:14px}}}}
.dual input[type=range]{{position:absolute;left:0;top:0;width:100%;height:24px;margin:0;background:none;border:0;padding:0;-webkit-appearance:none;appearance:none;pointer-events:none}}
.dual input[type=range]:focus-visible{{outline:2px solid var(--acc);outline-offset:2px}}
.dual input[type=range]::-webkit-slider-runnable-track{{height:24px;background:none;border:0}}
.dual input[type=range]::-moz-range-track{{height:24px;background:none;border:0}}
.dual input[type=range]::-webkit-slider-thumb{{-webkit-appearance:none;appearance:none;pointer-events:auto;width:18px;height:18px;margin-top:3px;border-radius:50%;background:var(--paper);border:2px solid var(--acc);cursor:pointer}}
.dual input[type=range]::-moz-range-thumb{{pointer-events:auto;width:14px;height:14px;border-radius:50%;background:var(--paper);border:2px solid var(--acc);cursor:pointer}}
.dual-track{{position:absolute;left:calc(var(--thumb)/2);right:calc(var(--thumb)/2);top:11px;height:2px;background:var(--rule)}}
.dual-track i{{position:absolute;top:0;height:100%;background:var(--acc)}}
.dual-vals{{display:flex;justify-content:space-between;gap:1rem;margin-top:0.5rem;font:600 13px var(--sans);font-variant-numeric:tabular-nums;color:var(--ink2)}}
.sortby{{margin-left:auto}}
select{{font:14px var(--sans);padding:0 1rem;min-height:44px;border:1px solid var(--rule);background:var(--paper);color:var(--ink);border-radius:0}}
.count{{flex:1 0 100%;margin:0;font-size:13px;color:var(--ink2)}}
.count button.link{{position:relative;padding:10px 6px;margin:-10px -6px}}
button.link{{background:none;border:0;padding:0;min-height:24px;font:inherit;color:var(--acc);text-decoration:underline;cursor:pointer}}
table.cmp-t,table.main-t{{border-collapse:collapse;width:100%}}
.main-t thead th{{position:sticky;top:0;z-index:2;background:var(--paper);font:600 11px/1.25 var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--ink2);text-align:left;padding:1rem;border-bottom:2px solid var(--ink);vertical-align:middle;white-space:normal}}
.main-t thead th.num{{text-align:right}}
.main-t thead th button{{font:inherit;letter-spacing:inherit;text-transform:inherit;color:inherit;background:none;border:0;padding:0;margin:0;min-height:24px;cursor:pointer;text-align:inherit}}
.main-t thead th button:hover{{color:var(--ink);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}}
.main-t thead th[aria-sort=ascending] button::after{{content:"\\00a0\\2191"}}
.main-t thead th[aria-sort=descending] button::after{{content:"\\00a0\\2193"}}
.main-t thead sup{{text-transform:none}}
.main-t td,.main-t tbody th{{padding:1rem;border-bottom:1px solid var(--rule2);vertical-align:top;text-align:left;font-weight:400}}
.main-t tbody.item:hover tr.main{{background:var(--tint)}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.main-t td.num,.main-t th.num{{text-align:right}}
td.num{{white-space:nowrap}}
.c-cmp{{width:2rem;padding-left:0.5rem!important;padding-right:0.5rem!important}}
.c-rec{{width:120px}}
.c-model{{width:27%}}
.mcell{{display:flex;gap:1rem;align-items:flex-start}}
.mcell>div{{min-width:0}}
.ph{{display:block;flex:none;background:var(--imgbg);border:1px solid var(--rule2);object-fit:contain}}
img.ph{{filter:var(--imgf)}}
span.ph{{display:flex;align-items:center;justify-content:center;background:var(--tint);color:var(--ink2);font:600 11px/1.25 var(--sans);text-transform:uppercase;letter-spacing:.04em;text-align:center;padding:0.5rem 0.25rem}}
span.ph-lg{{font-size:12px}}
.brand{{font-weight:700}} .mname{{font-weight:400}}
.best{{display:block;font-size:13px;color:var(--ink2);margin-top:0.5rem;line-height:1.35}}
.c-catch{{font-size:14px;width:28%}}
.more-w{{margin-top:0.5rem}}
.rec{{font-size:14px;display:inline-block;padding-left:1rem;text-indent:-1rem}}
.rec::before{{content:"";display:inline-block;width:8px;height:8px;margin-right:0.5rem;vertical-align:1px;border:1.5px solid var(--acc);text-indent:0}}
.rec-yes::before{{background:var(--acc)}}
.rec-kit::before,.rec-brief::before{{background:linear-gradient(90deg,var(--acc) 50%,transparent 50%)}}
.rec-no{{color:var(--ink2)}} .rec-no::before{{border-color:var(--ink3)}}
.noplan{{color:var(--ink2)}}
.score b{{font-size:15px}} .score{{color:var(--ink2);font-size:13px;white-space:nowrap}}
.bar{{display:block;height:3px;background:var(--rule2);margin:0.5rem 0 0;width:52px}}
/* scaleX paints on the compositor; animating width forced a layout each frame */
.bar i{{display:block;height:100%;width:100%;background:var(--acc);transform-origin:left center;transition:transform .2s ease}}
.note{{display:block;font-size:12px;color:var(--ink3);white-space:normal}}
.fn{{font-size:11px;vertical-align:super;line-height:0;margin-left:0;text-decoration:underline;text-underline-offset:2px;color:var(--ink3)}}
.fn:hover{{color:var(--acc);text-decoration:underline}}
button.more{{position:relative;background:none;border:1px solid var(--rule);font:12px var(--sans);padding:0 1rem;min-height:24px;cursor:pointer;color:var(--ink);white-space:nowrap}}
button.more::after{{content:"";position:absolute;inset:-10px -8px}}
button.more:hover,button.more[aria-expanded=true]{{border-color:var(--ink)}}
tr.detail td{{background:var(--tint);padding:1rem 1rem 1rem 3rem;border-bottom:1px solid var(--rule)}}
.dgrid{{display:grid;grid-template-columns:180px minmax(0,1fr) minmax(0,1fr);gap:0 2rem}}
.dimg{{margin:0}}
.zoom{{position:relative;display:block;padding:0;border:0;background:none;line-height:0;cursor:zoom-in}}
.zoom:focus-visible{{outline:2px solid var(--acc);outline-offset:2px}}
.zi{{position:absolute;right:-0.25rem;bottom:-0.25rem;width:1.25rem;height:1.25rem;border-radius:50%;background:var(--paper);border:1px solid var(--ink);display:grid;place-items:center;opacity:0;pointer-events:none;transition:opacity .15s}}
.zi::before{{content:"";width:6px;height:6px;border:1.5px solid var(--ink);border-radius:50%;margin:-3px 0 0 -3px}}
.zi::after{{content:"";position:absolute;right:4px;bottom:4px;width:5px;height:1.5px;background:var(--ink);transform:rotate(45deg)}}
.zoom:hover .zi,.zoom:focus-visible .zi{{opacity:1}}
@media (hover:none){{.zi{{opacity:1}}}}
#lightbox{{border:1px solid var(--rule);background:var(--paper);color:var(--ink);padding:1rem;max-width:min(90vw,420px)}}
#lightbox img{{display:block;margin:0 auto;width:auto;height:auto;max-width:100%;max-height:70vh;background:var(--imgbg);border:1px solid var(--rule2);filter:var(--imgf)}}
#lightbox::backdrop{{background:rgb(0 0 0 / .65)}}
.lb-bar{{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin-top:1rem;font:600 13px/1.3 var(--sans)}}
.dgrid dl{{margin:0;display:grid;grid-template-columns:140px minmax(0,1fr);gap:1rem;font-size:14px;align-content:start}}
.dgrid dt{{color:var(--ink2)}} .dgrid dd{{margin:0}}
.maths{{font-variant-numeric:tabular-nums}}
.unverified{{font-size:13px;margin:1rem 0 0;color:var(--ink2)}}
.srcs{{font-size:12px;color:var(--ink2);margin:1rem 0 0}}
.srcs .fn{{font-size:12px;vertical-align:baseline;margin-left:0;color:var(--acc)}}
.empty{{padding:2rem 0;margin:0 auto;color:var(--ink2);text-align:center}}
/* jump-to-row highlight */
@keyframes flash{{0%,35%{{background-color:var(--hl)}}100%{{background-color:transparent}}}}
tbody.item.flash tr.main>*{{animation:flash 1.8s ease-out}}
@media (prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}} tbody.item.flash tr.main>*{{animation:none;background:var(--hl)}} #theme i,body,.bar i,.cmp-note{{transition:none}}}}
/* compare */
#compare{{border:1px solid var(--ink);margin:1rem 0 0;padding:0 0 1rem}}
.cmp-head{{display:flex;justify-content:space-between;align-items:baseline;padding:1rem;border-bottom:1px solid var(--rule)}}
.cmp-head h2{{font:700 20px/1.2 var(--serif);margin:0}}
.cmp-actions{{display:flex;gap:1rem;align-items:baseline;flex-wrap:wrap}}
.cmpo{{display:inline-flex;align-items:center;gap:0.4rem;font-size:13px;line-height:1.3;color:var(--ink2);cursor:pointer}}
#cmp-dupes{{color:var(--ink3);white-space:nowrap}}
.cmp-note{{margin:0;padding:0 1rem 1rem;font-size:13px;line-height:1.4;color:var(--ink2);transition:opacity .4s}}
.cmp-note.out{{opacity:0}}
.cmp-t tr.cmp-cost th,.cmp-t tr.cmp-cost td{{background:var(--tint);font-variant-numeric:tabular-nums}}
.cmp-scroll{{overflow-x:auto}}
.cmp-t th,.cmp-t td{{padding:0.5rem 1rem;border-bottom:1px solid var(--rule2);text-align:left;vertical-align:top;font-size:14px}}
.cmp-t tbody tr:hover th,.cmp-t tbody tr:hover td{{background:var(--tint)}}
.cmp-t thead th{{font:700 15px/1.25 var(--sans);border-bottom:2px solid var(--ink);min-width:200px}}
.cmp-name{{display:block}}
.cmp-photo{{display:block;margin-top:1rem}}
.cmp-photo img{{display:block;width:45px;height:60px;object-fit:contain;background:var(--imgbg);border:1px solid var(--rule2);filter:var(--imgf)}}
.cmp-t tbody th{{font:600 11px/1.2rem var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--ink2);width:150px;min-width:120px}}
.vh{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}}
.tray{{position:sticky;bottom:0;background:var(--tray);color:var(--tray-ink);border-top:1px solid var(--rule);padding:1rem;display:flex;gap:1rem;align-items:center;justify-content:center;font-size:14px;z-index:5}}
.tray button{{font:600 14px var(--sans);background:var(--tray-ink);color:var(--tray);border:0;padding:0 1rem;min-height:24px;cursor:pointer}}
.tray button:disabled{{opacity:.5;cursor:default}}
.tray button.ghost{{background:none;color:var(--tray-ink);text-decoration:underline;padding:0 1rem}}
 /* The tray becomes the compare header and comes back again. The two are never
    on screen together, so one name serves both and no other element is named. */
 #tray,.cmp-head{{view-transition-name:cmp-tray}}
 ::view-transition-group(cmp-tray){{animation-duration:240ms;animation-timing-function:cubic-bezier(.2,.7,.2,1)}}
 /* Hand over rather than dissolve: two bars of text cross-fading in one box
    reads as a smear, so the old bar goes first and the new one arrives after. */
 ::view-transition-old(cmp-tray){{animation:vt-out 100ms linear both}}
 ::view-transition-new(cmp-tray){{animation:vt-in 140ms 100ms linear both}}
 @keyframes vt-out{{to{{opacity:0}}}}
 @keyframes vt-in{{from{{opacity:0}}}}
 /* Only the pair moves. Without this the whole page cross-fades and the table
    ghosts behind the comparison. */
 ::view-transition-old(root),::view-transition-new(root){{animation:none}}
 @media (prefers-reduced-motion:reduce){{::view-transition-group(*),::view-transition-old(*),::view-transition-new(*),::view-transition-image-pair(*),::view-transition-group(root){{animation:none!important}}}}
/* footer */
section.method{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;border-top:1px solid var(--ink);margin-top:2rem;padding:1rem 0 3rem;font-size:13px;color:var(--ink2)}}
section.method h2{{font:700 13px/1.2 var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--ink);margin:0 0 1rem}}
section.method p{{margin:0 0 1rem;max-width:none}}
section.method p a{{color:var(--ink2)}}
.srcs>summary{{display:flex;align-items:center;gap:0.5rem;min-height:24px;margin:0 0 1rem;cursor:pointer;list-style:none}}
.srcs>summary::-webkit-details-marker{{display:none}}
.srcs>summary h2{{margin:0}}
.srcs>summary::before{{content:"";flex:none;width:7px;height:7px;border-right:1.5px solid var(--ink);border-bottom:1.5px solid var(--ink);transform:rotate(-45deg);margin-right:0.25rem}}
.srcs[open]>summary::before{{transform:rotate(45deg)}}
.srcs-n{{font:500 12px/1.2 var(--sans);letter-spacing:0;text-transform:none;color:var(--ink3)}}
.fns-wrap{{columns:2;column-gap:2rem}}
.fns-g{{margin:0 0 0.75rem;break-inside:avoid}}
.fns-g h3{{font:600 12px/1.3 var(--sans);text-transform:uppercase;letter-spacing:.05em;color:var(--ink3);margin:0}}
ol.fns{{margin:0;padding-left:1.5rem;columns:1}}
ol.fns li{{margin:0}}
ol.fns a{{display:inline-flex;align-items:center;min-height:24px;text-decoration:underline;color:var(--ink2)}}
.foot{{border-top:1px solid var(--rule);padding:1rem 0 2rem;font-size:13px;color:var(--ink2)}}
.foot p{{margin:0;max-width:none}}
.foot a{{color:var(--ink2)}}
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
 .main-t td,.main-t tbody th{{padding:1rem}}
 .main-t thead th{{padding:1rem;font-size:11px}}
 .c-catch{{width:22%}}
}}
@media (max-width:820px){{
 body{{font-size:15px}}
 .wrap{{padding:0 1rem}}
 header.intro{{grid-template-columns:1fr;gap:1rem;padding:2rem 0}}
 .verdict{{border-left:0;border-top:1px solid var(--rule);padding:1rem 0 0}}
 .dek{{font-size:16px}}
 .controls{{gap:1rem}}
 .sortby{{margin-left:0}}
 input[type=range]{{width:150px}}
 .main-t thead{{position:absolute;width:1px;height:1px;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}}
 .main-t thead th{{position:static;padding:0;border:0;background:none}}
 .main-t,.main-t tbody,.main-t tr,.main-t td,.main-t tbody th{{display:block}}
 .main-t tbody.item{{border-bottom:1px solid var(--rule);padding:1rem}}
 tbody.item[data-v]{{border-left:3px solid var(--vc)}}
 tbody.item[data-v] tr.main>td.c-cmp{{border-left:0}}
 .main-t tr.main{{display:grid;grid-template-columns:2rem minmax(0,1fr);gap:0 1rem;position:relative;align-items:baseline}}
 .main-t tbody.item:hover tr.main{{background:none}}
 .main-t tr.main>*{{padding:0;border:0;width:auto;min-width:0;max-width:none}}
 .c-cmp{{grid-row:1;grid-column:1;padding-top:0!important}}
 .c-model{{grid-column:2;grid-row:1}}
 .ph-sm{{width:45px!important;height:60px!important}}
 .c-rec{{grid-column:2;grid-row:2}} .c-price{{grid-column:2;grid-row:3}} .c-score{{grid-column:2;grid-row:4}}
 .c-nosub{{grid-column:2;grid-row:5}} .c-sub{{grid-column:2;grid-row:6}}
 .c-catch{{grid-column:2;grid-row:7;padding-top:0.75rem;font-size:14px}}
 /* One muted label column, value to its right, so five separate label
    lines become one aligned rhythm. The price needs no label. */
 .main-t td.c-rec,.main-t td.c-score,.main-t td.c-nosub,.main-t td.c-sub{{display:flex;gap:0.75rem;align-items:baseline;padding:0.45rem 0 0}}
 .main-t td.c-rec::before,.main-t td.c-score::before,.main-t td.c-nosub::before,.main-t td.c-sub::before{{flex:0 0 8.5rem;margin:0}}
 .main-t td.c-price{{padding:0.5rem 0 0.25rem;font:700 17px/1.2 var(--sans)}}
 .main-t td.c-score .bar{{margin:0;flex:0 0 52px;align-self:center}}
 .main-t td.c-nosub .note{{white-space:normal}}
 .main-t td[data-label]::before{{content:attr(data-label);display:block;font:600 12px/1.3 var(--sans);text-transform:uppercase;letter-spacing:.04em;color:var(--ink3);margin-bottom:0;white-space:normal}}
 .main-t td.num,.main-t th.num{{text-align:left}} .bar{{margin-left:0}}
 tr.detail td{{padding:1rem;margin-top:0}}
 .dgrid{{grid-template-columns:1fr}} .dgrid dl+dl{{margin-top:1rem}}
 .ph-lg{{width:120px!important;height:160px!important;margin-bottom:1rem}}
 section.method{{grid-template-columns:1fr}} .fns-wrap{{columns:1}}
 .cmp-t th,.cmp-t td{{padding:0.5rem 1rem;font-size:13px}}
 .cmp-t thead th{{min-width:140px;font-size:14px}}
 .cmp-t tbody th{{width:84px;min-width:84px;font-size:11px;position:sticky;left:0;background:var(--paper)}}
 .cmp-t thead th:first-child{{position:sticky;left:0;background:var(--paper);min-width:84px}}
}}
@media (max-width:520px){{
 .mast>div>span{{display:none}}
 header.intro{{padding:1rem 0}}
 .dek{{font-size:15px;line-height:1.4;margin-bottom:0.5rem}}
 .verdict{{display:none}}
 .vshort{{display:block}}
 .srcs>summary{{align-items:flex-start}}
 .controls{{padding:0.75rem 0;gap:0.75rem}}
 .sortby .lab{{margin-bottom:0.5rem}}
 /* The Compare action joins this line on the first tick; reserve its second
    line so the table does not jump 19px when the tray appears. */
 .count{{min-height:3em}}
 .filters{{display:block;flex:1 1 100%}}
 .filters>summary{{display:flex;align-items:center;gap:0.5rem;min-height:44px;padding:0 1rem;border:1px solid var(--rule);font:600 12px/1 var(--sans);text-transform:uppercase;letter-spacing:.07em;color:var(--ink2);cursor:pointer;list-style:none}}
 .filters>summary::-webkit-details-marker{{display:none}}
 .filters>summary::marker{{content:""}}
 .filters>summary::before{{content:"";width:7px;height:7px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(-45deg);margin-right:0.25rem}}
 .filters[open]>summary::before{{transform:rotate(45deg)}}
 .filters:not([open]) .fbody{{display:none}}
 .fbody{{flex-direction:column;align-items:stretch;gap:1rem;padding:1rem;border:1px solid var(--rule);border-top:0}}
 .fbody .opts{{gap:0.5rem 1rem}}
 .range{{flex:none;width:100%;max-width:none}}
}}
@media print{{.skip,.controls,.tray,.c-cmp,.more-w,#theme,.srcs>summary,.cmp-note{{display:none}} tr.detail{{display:table-row!important}}}}
</style></head><body>
<a class="skip" href="#tbl">Skip to the comparison table</a>
<div class="wrap">
<div class="mast"><div>SubFree UK <span>Gadgets that work without a subscription</span></div><button type="button" id="theme"><i aria-hidden="true"></i><span>Dark mode</span></button></div>
<header class="intro">
<div>
<h1>Video doorbells that work without a subscription</h1>
<p class="dek">{len(ROWS)} doorbells sold in the UK, checked against manufacturer pages and independent reviews: what you get for free, what's behind a paywall, and what each one costs over three years.</p>
<p class="meta"><b>Last checked {CHECKED}.</b> No affiliate links, no tracking, no cookies. Prices change often, so each one links to its source. Spotted a mistake? <a href="{GITHUB}/issues/new">Open an issue</a>.</p>
<p class="vshort"><b>Short answer:</b> <span class="v-best">{vlink(["reo-poe"],"Reolink PoE")}</span> or <span class="v-batt">{vlink(["tapo-d230"],"Tapo D230S1")}</span>. <span class="v-avoid">{vlink(["ring"],"Ring")}</span> needs a plan to record.</p>
</div>
<aside class="verdict">
<h2>The short answer</h2>
<p class="v-best"><b>Best overall without fees:</b> {vlink(["reo-poe"],"Reolink Video Doorbell PoE")}. It records to a card or NVR, nothing is paywalled, and Reolink is the only brand here with an official local Home Assistant integration. The WiFi and battery versions follow the same rules if you can't run an Ethernet cable.</p>
<p class="v-batt"><b>Easiest battery pick:</b> {vlink(["tapo-d230"],"Tapo D230S1")}, which keeps footage on a hub inside the house.</p>
<p class="v-avoid"><b>Avoid if you won't pay monthly:</b> {vlink(["ring"],"Ring")} records nothing without a plan, and {vlink(["blink"],"Blink")} and {vlink(["arlo"],"Arlo")} need extra hardware.</p>
</aside>
</header>

<main>
<p class="vh" id="live" role="status"></p>
<form class="controls" id="controls" onsubmit="return false">
<details class="filters" id="filters" open>
<summary>Filters</summary>
<div class="fbody">
<fieldset><legend>Show only</legend><div class="opts">
<label><input type="checkbox" id="f-rec"> Records free, no extra kit</label>
<label><input type="checkbox" id="f-ha"> Local / Home Assistant</label>
</div></fieldset>
<fieldset><legend>Power</legend><div class="opts">
<label><input type="checkbox" class="f-pw" value="battery"> Battery</label>
<label><input type="checkbox" class="f-pw" value="wired"> Wired</label>
<label><input type="checkbox" class="f-pw" value="poe"> PoE</label>
</div><p class="hint">PoE: one cable carries both power and data.</p></fieldset>
<div class="range">
<span class="lab">Price</span>
<div class="dual">
<div class="dual-track" aria-hidden="true"><i id="f-fill"></i></div>
<input type="range" id="f-min" min="{MINP}" max="{maxp}" step="5" value="{MINP}" aria-label="Lowest price">
<input type="range" id="f-max" min="{MINP}" max="{maxp}" step="5" value="{maxp}" aria-label="Highest price">
</div>
<div class="dual-vals"><output id="f-min-out" for="f-min">£{MINP}</output><output id="f-max-out" for="f-max">£{maxp}</output></div>
</div>
</div>
</details>
<div class="sortby"><label class="lab" for="sort">Sort by</label><select id="sort">
<option value="keep3">3-year cost to keep recordings</option>
<option value="price">Price, low to high</option>
<option value="score">Free-feature score, high to low</option>
<option value="recv">Records free first</option>
<option value="nosub3">3-year cost, no plan</option>
<option value="sub3">3-year cost, with plan</option>
<option value="model">Model, A to Z</option>
</select></div>
<p class="count">Tick up to 3 rows to compare. <span id="count">{len(ROWS)}</span> of {len(ROWS)} shown · <button type="button" class="link" id="reset">Reset</button><span id="cmp-sep" hidden> · </span><button type="button" class="link" id="cmp-inline" hidden>Compare</button></p>
</form>
<noscript><p class="nojs">Filters, sorting, compare and the per-model details need JavaScript. All {len(ROWS)} doorbells are listed below.</p></noscript>
<script>if(window.matchMedia('(max-width:520px)').matches)document.getElementById('filters').open=false;</script>

<section id="compare" hidden>
<div class="cmp-head"><h2 id="cmp-h" tabindex="-1">Side by side</h2><div class="cmp-actions"><label class="cmpo" id="cmp-diff-w" hidden><input type="checkbox" id="cmp-diff"> Differences only <span id="cmp-dupes"></span></label><button type="button" class="link" id="cmp-copy">Copy shortlist</button><button type="button" class="link" id="cmp-clear">Clear</button><button type="button" class="link" id="cmp-close">Close</button></div></div>
<p class="cmp-note" id="cmp-note" role="status" hidden></p>
<div class="cmp-scroll"><table class="cmp-t" id="cmp-table"></table></div>
</section>

<table class="main-t" id="tbl" tabindex="-1">
<thead><tr>
<th scope="col" class="c-cmp"><span class="vh">Compare</span></th>
<th scope="col" data-sort="model" aria-sort="none"><button type="button">Model</button></th><th scope="col" data-sort="recv" aria-sort="none"><button type="button">Records free?</button></th><th scope="col" class="num" data-sort="price" aria-sort="none"><button type="button">Price</button></th><th scope="col" data-sort="score" aria-sort="none"><button type="button">Free features</button></th>
<th scope="col" class="num" data-sort="nosub3" aria-sort="none"><button type="button" aria-label="3 yrs, no plan, footnote a">3 yrs, no plan<sup aria-hidden="true">a</sup></button></th><th scope="col" class="num" data-sort="sub3" aria-sort="none"><button type="button" aria-label="3 yrs, with plan, footnote b">3 yrs, with plan<sup aria-hidden="true">b</sup></button></th><th scope="col">Main catch</th>
</tr></thead>
{''.join(rows_html)}
</table>
<p class="empty" id="empty" hidden><span id="empty-txt">Nothing matches those filters.</span> <button type="button" class="link" id="near" hidden></button> <button type="button" class="link" id="empty-reset">Reset filters</button></p>

<section class="method" id="method">
<div>
<h2>How we worked it out</h2>
<p><sup>a</sup> <b>3 years, no plan</b> = price + anything you must add to record for free (Blink's Sync Module 2 at £39.99, Arlo's SmartHub at £105.07, and a microSD card or USB stick, assumed at {money(CARD)}; that last figure isn't from a cited source). Ring and Nest can't keep recordings this way, which is shown next to the figure.</p>
<p><sup>b</sup> <b>3 years, with plan</b> = price + 36 × the cheapest UK monthly plan that adds cloud recording for one device. Paying yearly is usually cheaper. The EZVIZ plan figure is the EU price because EZVIZ shows UK pricing only inside its app. Every model's sums are under <i>Details</i>.</p>
<p><b>Free-feature score (out of 8):</b> records for free (2 = out of the box, 1 = with extra kit or only briefly), free live view (1), free motion alerts (1), free smart detection (1), storage included in the box (1), local Home Assistant support (2 = official and local, 1 = unofficial or generic).</p>
<p><b>Plain terms.</b> <i>PoE</i> (Power over Ethernet) sends power and video down one network cable. An <i>NVR</i> is a recorder box that stores footage from several cameras. A <i>microSD</i> card is the small memory card that sits inside many doorbells or their indoor chime. <i>Home Assistant</i> is free software that keeps your smart home on your own network instead of a manufacturer's cloud.</p>
<p>Batteries, electricity, installation (except Hikvision, where the price includes fitting) and future price rises are left out. Anything not yet confirmed is listed under <i>Not yet verified</i> in each model's details.</p>
<p>Photos are the manufacturers' own, from their product pages: {photo_credits}.{f" No reliable official photo for: {no_photo}." if no_photo else ""}</p>
</div>
<details class="srcs" id="sources" open><summary><h2 class="srcs-t">Sources <span class="srcs-n">{len(order)} links</span></h2></summary><div class="fns-wrap">{fn_list}</div></details>
</section>
<footer class="foot"><p>Last checked {CHECKED}. {len(ROWS)} UK doorbells, no affiliate links, no tracking. <a href="{GITHUB}/issues/new">Open an issue</a> · <a href="#tbl">Back to the table</a>.</p></footer>
</main>
</div>
<div class="tray" id="tray" hidden><span id="tray-txt"></span><button type="button" id="tray-go">Compare</button><button type="button" class="ghost" id="tray-clear">Clear</button></div>
<dialog id="lightbox" aria-labelledby="lb-name">
<div id="lb-img"></div>
<div class="lb-bar"><span id="lb-name"></span><button type="button" class="link" id="lb-close">Close</button></div>
</dialog>
<script>
(function(){{
var D={data_js},CHECKED='{CHECKED}';
var $=function(s,c){{return (c||document).querySelector(s)}},$$=function(s,c){{return Array.prototype.slice.call((c||document).querySelectorAll(s))}};
var root=document.documentElement,mq=window.matchMedia('(prefers-color-scheme: dark)'),tb=$('#theme');
function isDark(){{var t=root.getAttribute('data-theme');return t?t==='dark':mq.matches}}
function syncTheme(){{var d=isDark();tb.lastChild.textContent=d?'Light mode':'Dark mode';tb.title=d?'Switch to light mode':'Switch to dark mode';tb.setAttribute('aria-label',tb.title)}}
tb.onclick=function(){{var n=isDark()?'light':'dark';root.setAttribute('data-theme',n);try{{localStorage.setItem('theme',n)}}catch(e){{}}syncTheme()}};
if(mq.addEventListener)mq.addEventListener('change',syncTheme);
syncTheme();
var narrow=window.matchMedia('(max-width:820px)'),small=window.matchMedia('(max-width:520px)'),filters=$('#filters'),srcs=$('#sources');
function fitFilters(){{filters.open=!small.matches}}
function fitSources(){{srcs.open=!narrow.matches}}
function fitSortKeys(){{$$('#tbl thead th button').forEach(function(b){{if(narrow.matches)b.setAttribute('tabindex','-1');else b.removeAttribute('tabindex')}})}}
if(small.addEventListener)small.addEventListener('change',fitFilters);
if(narrow.addEventListener)narrow.addEventListener('change',fitSortKeys);
if(narrow.addEventListener)narrow.addEventListener('change',fitSources);
addEventListener('beforeprint',function(){{srcs.open=true}});
fitFilters();fitSortKeys();fitSources();
var tbl=$('#tbl'),items=$$('tbody.item',tbl),minEl=$('#f-min'),maxEl=$('#f-max'),minOut=$('#f-min-out'),maxOut=$('#f-max-out'),fill=$('#f-fill');
var live=$('#live'),liveT,liveClearT,announce=false,lastN=0,nearPick=null;
function say(m){{clearTimeout(liveT);clearTimeout(liveClearT);liveT=setTimeout(function(){{live.textContent='';liveT=setTimeout(function(){{live.textContent=m;liveClearT=setTimeout(function(){{live.textContent=''}},4000)}},60)}},300)}}
var skey='keep3',sdir=1,SDEF={{keep3:1,price:1,score:-1,recv:-1,nosub3:1,sub3:1,model:1}};
function apply(){{
 var lo0=+minEl.min,hi0=+maxEl.max,lo=+minEl.value,hi=+maxEl.value;
 if(lo>hi){{lo=hi;minEl.value=hi}}
 minEl.style.zIndex=lo>=hi?2:1;
 minOut.textContent='£'+lo;maxOut.textContent='£'+hi;
 fill.style.left=((lo-lo0)/(hi0-lo0)*100)+'%';
 fill.style.width=((hi-lo)/(hi0-lo0)*100)+'%';
 var rec=$('#f-rec').checked,ha=$('#f-ha').checked,pw=$$('.f-pw:checked').map(function(x){{return x.value}}),n=0;
 function ok(t,plo,phi){{return (!rec||t.dataset.rec==='yes')&&(!ha||+t.dataset.ha>0)&&(+t.dataset.price>=plo&&+t.dataset.price<=phi)&&
  (!pw.length||pw.some(function(p){{return t.dataset.power.split(' ').indexOf(p)>-1}}))}}
 items.forEach(function(t){{var show=ok(t,lo,hi);t.hidden=!show;if(show)n++}});
 $('#count').textContent=n; $('#empty').hidden=n>0;
 var near=null;
 if(!n){{
  var bestD=Infinity;
  items.forEach(function(t){{
   if(!ok(t,lo0,hi0))return;
   var p=+t.dataset.price,d=p<lo?lo-p:p>hi?p-hi:0;
   if(d<bestD||(d===bestD&&p<+(near?near.dataset.price:Infinity))){{bestD=d;near=t}}
  }});
 }}
 nearPick=near;
 var nb=$('#near');
 nb.hidden=!near;
 if(near){{
  var nm=near.querySelector('.brand').textContent+' '+near.querySelector('.mname').textContent;
  var pr='£'+(+near.dataset.price).toFixed(2).replace(/\\.00$/,'');
  nb.textContent='Show '+nm+' at '+pr;
 }}
 if(announce&&n!==lastN)say(n?n+' of '+items.length+' doorbells shown':'No doorbells match those filters');
 lastN=n;
 var s=items.slice().sort(function(a,b){{
  var x=skey==='model'?a.dataset.model:+a.dataset[skey],y=skey==='model'?b.dataset.model:+b.dataset[skey];
  if(x<y)return -sdir;if(x>y)return sdir;return +a.dataset.keep3-+b.dataset.keep3;
 }});
 s.forEach(function(t){{tbl.appendChild(t)}});
 $$('#tbl thead th[data-sort]').forEach(function(th){{th.setAttribute('aria-sort',th.dataset.sort===skey?(sdir>0?'ascending':'descending'):'none')}});
 $('#sort').value=skey;
}}
$$('#controls input').forEach(function(el){{el.addEventListener('input',apply);el.addEventListener('change',apply)}});
// The track is decorative and its inputs ignore pointer events, so a click
// there is a shortcut for "move the handle nearest this spot".
$('.dual-track').addEventListener('click',function(ev){{
 var r=this.getBoundingClientRect();
 if(!r.width)return;
 var v=+minEl.min+Math.min(1,Math.max(0,(ev.clientX-r.left)/r.width))*(+maxEl.max-+minEl.min);
 var el=Math.abs(v-+minEl.value)<=Math.abs(v-+maxEl.value)?minEl:maxEl;
 el.value=v;apply();el.focus({{preventScroll:true}});
}});
$('#sort').onchange=function(){{skey=this.value;sdir=SDEF[skey];apply();drawBars()}};
$$('#tbl thead th[data-sort] button').forEach(function(b){{b.onclick=function(){{
 var k=b.parentNode.dataset.sort;
 if(k===skey)sdir=-sdir;else{{skey=k;sdir=SDEF[k]}}
 apply();drawBars();
}}}});
$('#reset').onclick=function(){{$$('#controls input[type=checkbox]').forEach(function(c){{c.checked=false}});minEl.value=minEl.min;maxEl.value=maxEl.max;skey='keep3';sdir=1;apply()}};
$$('button.more').forEach(function(b){{b.onclick=function(){{var d=document.getElementById(b.getAttribute('aria-controls')),o=b.getAttribute('aria-expanded')==='true';b.setAttribute('aria-expanded',!o);b.textContent=o?'Details':'Hide';d.hidden=o}}}});
var reduce=window.matchMedia('(prefers-reduced-motion: reduce)');
var barTimers=[];
function drawBars(){{
 var bars=$$('#tbl tbody.item:not([hidden]) .bar i');
 barTimers.forEach(clearTimeout);barTimers=[];
 if(reduce.matches){{bars.forEach(function(b){{b.style.transform='scaleX('+(b.dataset.w/100)+')'}});return}}
 bars.forEach(function(b){{b.style.transform='scaleX(0)'}});
 setTimeout(function(){{bars.forEach(function(b,i){{barTimers.push(setTimeout(function(){{b.style.transform='scaleX('+(b.dataset.w/100)+')'}},i*20))}})}},0);
}}
$$('a.jump').forEach(function(a){{a.addEventListener('click',function(ev){{
 var rows=a.dataset.ids.split(' ').map(function(id){{return document.getElementById('m-'+id)}});
 if(rows.some(function(r){{return r.hidden}}))$('#reset').click();
 rows.sort(function(x,y){{return x.compareDocumentPosition(y)&4?-1:1}});
 ev.preventDefault();
 rows[0].scrollIntoView({{behavior:reduce.matches?'auto':'smooth',block:'center'}});
 if(history.replaceState)history.replaceState(null,'',location.pathname+location.search+'#'+rows[0].id);
 rows.forEach(function(r){{r.classList.remove('flash');void r.offsetWidth;r.classList.add('flash');clearTimeout(r._ft);r._ft=setTimeout(function(){{r.classList.remove('flash')}},1900)}});
 var vis=$$('#tbl tbody.item:not([hidden])'),pos=vis.indexOf(rows[0]),vt=rows[0].querySelector('.vtag');
 say(D[rows[0].dataset.id].name+(vt?', '+vt.textContent.toLowerCase():'')+', row '+(pos+1)+' of '+vis.length);
 var cb=rows[0].querySelector('input.cmp'); if(cb)cb.focus({{preventScroll:true}});
}})}});
var PINNED=['Records free?','Price','3 yrs, no plan','3 yrs, with plan'],diffOnly=false;
var ROWS=[['Records free?','rec'],['Price','price'],['Free features','score'],['3 yrs, no plan','nosub3'],['3 yrs, with plan','sub3'],['Best for','best'],['Main catch','catch'],['Power','power'],['Storage','storage'],['Live view','live'],['Motion alerts','alerts'],['Smart detection','ai'],['History, no plan','history'],['Behind the paywall','paywalled'],['Plans','plan'],['Home Assistant','ha'],['Wi-Fi','wifi']];
function esc(s){{var d=document.createElement('div');d.textContent=s;return d.innerHTML}}
function sel(){{return $$('input.cmp:checked').map(function(c){{return c.value}})}}
function cmpIds(){{return sel().slice(0,3)}}
function shareUrl(){{var s=cmpIds();return location.origin+location.pathname+(s.length?'?cmp='+s.join(','):'')}}
function syncUrl(){{
 var s=cmpIds(),u=location.pathname+(s.length?'?cmp='+s.join(','):'')+location.hash;
 try{{if(history.replaceState)history.replaceState(null,'',u)}}catch(e){{}}
}}
function tray(){{
 var s=sel(); $$('input.cmp').forEach(function(c){{c.disabled=!c.checked&&s.length>=3}});
 $('#tray').hidden=s.length===0||!$('#compare').hidden;
 $('#tray-txt').textContent=s.length===1?'1 selected (tick 1 or 2 more)':s.length>=3?'3 selected (maximum, untick one to swap)':s.length?'2 selected':'';
 $('#tray-go').disabled=s.length<2;
 var ib=$('#cmp-inline');$('#cmp-sep').hidden=ib.hidden=s.length<2;ib.textContent='Compare '+s.length;
 // Unticking below two closes the panel without stealing focus from the box
 // the reader is on, so this path never touches focus.
 if(!$('#compare').hidden){{
  if(s.length>=2)render();
  else{{$('#compare').hidden=true;$('#tray').hidden=s.length===0}}
 }}
 say(s.length===0?'Comparison cleared':s.length===3?'3 selected. That is the maximum; untick one to swap.':s.length+' selected');
 syncUrl();
}}
function render(){{
 var s=sel(),h='<caption class="vh">Side-by-side comparison of '+s.length+' doorbells</caption><thead><tr><th scope="col"><span class="vh">Spec</span></th>'+s.map(function(id){{
  var d=D[id];
  return '<th scope="col"><span class="cmp-name">'+esc(d.name)+'</span>'+(d.img?'<span class="cmp-photo"><button type="button" class="zoom" data-full="'+esc(d.imgLg)+'" data-name="'+esc(d.name)+'" aria-label="View '+esc(d.name)+' photo full size"><img src="'+esc(d.img)+'" width="45" height="60" alt="" loading="lazy" decoding="async"><span class="zi" aria-hidden="true"></span></button></span>':'')+'</th>';
 }}).join('')+'</tr></thead><tbody>';
 var keep=s.map(function(id){{return D[id].keep3}}),valid=keep.filter(function(v){{return typeof v==='number'&&isFinite(v)}}),low=valid.length?Math.min.apply(null,valid):Infinity;
 h+='<tr class="cmp-cost" data-pin="1"><th scope="row">3 years, cheapest</th>'+s.map(function(id){{var v=D[id].keep3;
  if(typeof v!=='number'||!isFinite(v))return '<td>no plan</td>';
  return '<td>'+(Math.abs(v-low)<0.005?'£'+v.toFixed(2)+' · cheapest':'+£'+(v-low).toFixed(2))+'</td>';
 }}).join('')+'</tr>';
 var dupes=0;
 ROWS.forEach(function(r){{
  var vals=s.map(function(id){{return D[id][r[1]]}}),pin=PINNED.indexOf(r[0])>-1,same=vals.every(function(v){{return v===vals[0]}});
  if(same&&!pin)dupes++;
  h+='<tr'+(pin?' data-pin="1"':'')+(same&&!pin?' data-same="1"':'')+'><th scope="row">'+r[0]+'</th>'+s.map(function(id){{return '<td>'+esc(D[id][r[1]])+'</td>'}}).join('')+'</tr>';
 }});
 $('#cmp-table').innerHTML=h+'</tbody>'; $('#compare').hidden=false;
 if(!dupes)diffOnly=false;
 $('#cmp-diff-w').hidden=!dupes;
 $('#cmp-dupes').textContent=dupes?'('+dupes+' identical)':'';
 $('#cmp-diff').checked=diffOnly;
 applyDiff();
}}
// Identical rows are the one part of a comparison that carries no decision, so
// they can go. The four that do carry one stay even when they match.
function applyDiff(){{$$('#cmp-table tbody tr[data-same]').forEach(function(tr){{tr.hidden=diffOnly}})}}
$('#cmp-diff').onchange=function(){{diffOnly=this.checked;applyDiff()}};
$$('input.cmp').forEach(function(c){{c.addEventListener('change',tray)}});
function showCompare(){{
 // Already open: take the reader back to it rather than rebuilding it.
 if(!$('#compare').hidden){{$('#compare').scrollIntoView({{behavior:reduce.matches?'auto':'smooth',block:'start'}});$('#cmp-h').focus({{preventScroll:true}});return}}
 // The tray leaves and its place is taken by the compare header: the same box
 // stops being one control and starts being another. Scroll first, so both
 // snapshots are taken from the reader's final position.
 function go(smooth){{
  render();tray();
  $('#compare').scrollIntoView({{behavior:smooth?'smooth':'auto',block:'start'}});
  // The button that opened this is hidden now, so hand focus to the panel's
  // heading. Not the section: its name would be every cell in the table.
  $('#cmp-h').focus({{preventScroll:true}});
 }}
 if(document.startViewTransition&&!reduce.matches)document.startViewTransition(function(){{go(false)}});else go(!reduce.matches);
 say('Side-by-side comparison of '+sel().length+' doorbells');
}}
function closeCompare(){{
 if($('#compare').hidden)return;
 var go=function(){{
  $('#compare').hidden=true;tray();
  if(!$('#tray').hidden)$('#tray-go').focus({{preventScroll:true}});
 }};
 if(document.startViewTransition&&!reduce.matches)document.startViewTransition(go);else go();
}}
function clearAll(){{
 // Both Clear buttons are about to be hidden, so focus needs somewhere real.
 var inside=$('#compare').contains(document.activeElement)||$('#tray').contains(document.activeElement);
 $$('input.cmp').forEach(function(c){{c.checked=false}});$('#compare').hidden=true;tray();
 if(inside){{var f=document.querySelector('input.cmp');if(f)f.focus({{preventScroll:true}})}}
}}
$('#tray-go').onclick=showCompare;
$('#cmp-inline').onclick=showCompare;
$('#tray-clear').onclick=clearAll;
$('#cmp-clear').onclick=clearAll;
$('#cmp-close').onclick=closeCompare;
function m3(x){{return '£'+(+x).toFixed(2)}}
function shortlist(){{
 return 'SubFree UK shortlist, checked '+CHECKED+'\\n'+shareUrl()+'\\n\\n'+sel().map(function(id){{var d=D[id];
  return d.name+'\\n'+d.price+' · 3-year cost to keep recordings '+(typeof d.keep3==='number'&&isFinite(d.keep3)?m3(d.keep3):'no plan')+'\\nBest for: '+d.best+'\\nMain catch: '+d.catch;
 }}).join('\\n\\n');
}}
function legacyCopy(text){{
 var t=document.createElement('textarea');t.value=text;t.setAttribute('readonly','');t.style.position='fixed';t.style.top='-1000px';
 document.body.appendChild(t);t.select();var ok=false;try{{ok=document.execCommand('copy')}}catch(e){{}}
 document.body.removeChild(t);return ok;
}}
var copyBtn=$('#cmp-copy'),noteEl=$('#cmp-note'),noteT,noteT2;
function copyNote(m){{
 noteEl.textContent=m;noteEl.hidden=false;noteEl.classList.remove('out');
 clearTimeout(noteT);clearTimeout(noteT2);
 noteT=setTimeout(function(){{
  if(reduce.matches){{noteEl.hidden=true;return}}
  noteEl.classList.add('out');
  noteT2=setTimeout(function(){{noteEl.hidden=true;noteEl.classList.remove('out')}},400);
 }},6000);
}}
copyBtn.onclick=function(){{
 var text=shortlist(),n=sel().length;
 function ok(){{copyNote('Copied '+n+' model'+(n===1?'':'s')+' as Markdown, with prices and the date checked. Paste it into a message or a note.')}}
 function fail(){{copyNote('Copying is blocked in this browser. Select the table text and copy it by hand instead.')}}
 if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(text).then(ok,function(){{legacyCopy(text)?ok():fail()}});
 else legacyCopy(text)?ok():fail();
}};
$('#empty-reset').onclick=function(){{$('#reset').click()}};
$('#near').onclick=function(){{
 if(!nearPick)return;
 var p=+nearPick.dataset.price,st=+minEl.step||5,base=+minEl.min;
 if(p<+minEl.value)minEl.value=base+Math.floor((p-base)/st)*st;
 else if(p>+maxEl.value)maxEl.value=base+Math.ceil((p-base)/st)*st;
 apply();
}};
var lb=$('#lightbox'),lbBox=$('#lb-img'),lbName=$('#lb-name'),lbImg;
document.addEventListener('click',function(ev){{
 var b=ev.target.closest('.zoom');
 if(!b)return;
 if(!lbImg){{
  lbImg=document.createElement('img');
  lbImg.width=360;lbImg.height=480;lbImg.decoding='async';
  lbBox.appendChild(lbImg);
 }}
 lbImg.src=b.dataset.full;
 lbImg.alt=b.dataset.name;
 lbName.textContent=b.dataset.name;
 if(lb.showModal)lb.showModal();
}});
$('#lb-close').onclick=function(){{lb.close()}};
lb.addEventListener('click',function(ev){{
 if(ev.target!==lb)return;
 var r=lb.getBoundingClientRect();
 if(ev.clientX<r.left||ev.clientX>r.right||ev.clientY<r.top||ev.clientY>r.bottom)lb.close();
}});
apply();drawBars();announce=true;
var shared='';
try{{shared=decodeURIComponent((location.search.match(/[?&]cmp=([^&]*)/)||[])[1]||'')}}catch(e){{shared=''}}
if(shared){{
 var ids=[];
 shared.split(',').forEach(function(id){{if(D[id]&&ids.indexOf(id)<0&&ids.length<3)ids.push(id)}});
 if(ids.length){{
  $$('input.cmp').forEach(function(c){{c.checked=ids.indexOf(c.value)>-1}});
  if(ids.length>1)render();
  tray();
 }}
 syncUrl();
}}
}})();
</script>
</body></html>'''
for _f in ("index.html","doorbells.html"): open(os.path.join(ROOT,_f),"w",encoding="utf-8").write(page)
print(len(ROWS),"rows written")
for r in sorted(ROWS,key=lambda r:r["keep3"]): print(f"{r['brand']:14} {r['model']:38} score {r['score_total']}  nosub {r['nosub3']:8.2f}  sub {r['sub3'] if r['sub3'] else '-':>8}  keep {r['keep3']:.2f}")
open_rows=[r for r in ROWS if r["unverified"]]
print(f"\nUnverified ({len(open_rows)} of {len(ROWS)} rows):" + (" none" if not open_rows else ""))
for r in open_rows: print(f"  {r['brand']} {r['model']}: {r['unverified'].replace('£','GBP ')}")
