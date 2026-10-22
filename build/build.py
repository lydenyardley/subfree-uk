"""Single source of truth for the SubFree UK doorbell table.
Generates data/doorbells.csv, data/doorbells.md and the site (index.html at the
repo root, with doorbells.html as a redirect) from ROWS below. The page's CSS
and JavaScript are build/page.css and build/page.js, inlined here at build time.
Run from anywhere: python3 build/build.py
"""
import csv, hashlib, html, json
import os
from datetime import date
from urllib.parse import urlparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
HERE = os.path.dirname(os.path.abspath(__file__))

# The one hand-typed fact: the day the prices and plans were checked. ISO, so
# the age can be counted; build/check.py warns after 30 days and fails at 60.
CHECKED_ISO = "2026-10-19"
_CHECKED_DATE = date.fromisoformat(CHECKED_ISO)
CHECKED = f"{_CHECKED_DATE.day} {_CHECKED_DATE:%B %Y}"
GITHUB = "https://github.com/lydenyardley/subfree-uk"
SITE = "/subfree-uk/"   # where the site is published; the 404 page needs root-relative links
EMAIL = "lydenyardley+subfreeuk@posteo.net"
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
 "ha_eufy": ("Home Assistant: eufy (ha-eufy-sdk)", "https://github.com/mega-yfue/ha-eufy-sdk"),
 "ha_arlo": ("Home Assistant: Aarlo (community)", "https://github.com/twrecked/hass-aarlo"),
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
 rec_src="ring_plans", history_src="ring_plans", ha_src="ha_ring", unverified=""),
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
 rec_src="nest_plans", history_src="nest_plans", ha_src="ha_nest", unverified=""),
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
 ha_text="Community integration only (ha-eufy-sdk), which still logs in through your eufy account.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=1),
 src=["eufy_prod","eufy_cloud","verge_eufy","sha_nosub","ha_eufy"],
 rec_src="eufy_prod", history_src="eufy_prod", ha_src="ha_eufy", unverified=""),
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
 rec_src="reo_store", history_src="reo_store", ha_src="ha_reo", unverified=""),
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
 rec_src="reo_faq", history_src="reo_faq", ha_src="ha_reo", unverified=""),
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
 rec_src="reo_batt", history_src="reo_batt", ha_src="ha_reo", unverified=""),
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
 rec_src="tapo_d230", history_src="tapo_d230", ha_src="ha_tplink", unverified=""),
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
 rec_src="tapo_td21", history_src="tapo_td21", ha_src="ha_tplink", unverified=""),
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
 src=["argos_arlo","arlo_blog","arlo_plans","arlo_faq","arlo_doorbell","arlo_hubcompat","amz_arlohub","tr_arlo","ambient_arlo","ha_arlo"],
 rec_src="arlo_blog", history_src="arlo_doorbell", ha_src="ha_arlo", unverified=""),
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
 rec_src="aqara_specs", history_src="aqara_specs", ha_src="ha_homekit", unverified=""),
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
 rec_src="blink_sm2", history_src="blink_sm2", ha_src="ha_blink", unverified=""),
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
 rec_src="amz_ep3x", history_src="ezviz_blog", ha_src="ha_ezviz", plan_price_region="EU", unverified="CloudPlay's UK price is app-only, so the £4.99 in the plan column is the published EU price, not a UK quote."),
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
 rec_src="ertech_db2", history_src="ertech_db2", ha_src="ha_ezviz", plan_price_region="EU", unverified="CloudPlay's UK price is app-only, so the £4.99 in the plan column is the published EU price, not a UK quote."),
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
 rec_src="hik_ds", history_src="hik_ds", ha_src="hik_ds", unverified=""),
]

# ---------- row shape ----------
# A row with a missing key fails here, before anything is generated. The
# unknown-key test is what catches a misspelling, which would otherwise read as
# a valid optional field and quietly skip a sentence or print nothing.
REQUIRED_ROW_KEYS = (
    "id", "brand", "model", "rec", "power", "ha", "price", "price_note",
    "price_src", "extra", "extra_note", "free_records", "sub", "sub_name",
    "best", "catch", "storage", "live", "alerts", "ai", "history",
    "paywalled", "sub_text", "ha_text", "wifi", "score", "src", "unverified",
    "rec_src", "history_src", "ha_src",
)
OPTIONAL_ROW_KEYS = ("power_note", "cards", "plan_price_region")
DERIVED_ROW_KEYS = (
    "score_total", "nosub3", "sub3", "keep3", "maths_free", "maths_sub",
    "plan_region", "keep_basis", "keep_note",
)

def row_problems():
    problems = []
    for r in ROWS:
        rid = r.get("id", "(no id)")
        missing = [k for k in REQUIRED_ROW_KEYS if k not in r]
        allowed = REQUIRED_ROW_KEYS + OPTIONAL_ROW_KEYS + DERIVED_ROW_KEYS
        unknown = [k for k in r if k not in allowed]
        if missing: problems.append(f"{rid}: missing {', '.join(missing)}")
        if unknown: problems.append(f"{rid}: unknown {', '.join(unknown)}")
        for key in ("price_src", "rec_src", "history_src", "ha_src"):
            if key in r and r[key] not in S:
                problems.append(f"{rid}: {key} {r[key]!r} is not in S")
            if key in r and r[key] not in r.get("src", []):
                problems.append(f"{rid}: {key} {r[key]!r} is not in the row's src list")
        if r.get("cards", 1) < 1:
            problems.append(f"{rid}: cards must be at least 1")
        if r.get("plan_price_region", "UK") not in ("UK", "EU"):
            problems.append(f"{rid}: plan_price_region must be UK or EU")
    return problems

_ROW_PROBLEMS = row_problems()
if _ROW_PROBLEMS:
    raise SystemExit("Row problems:\n  " + "\n  ".join(_ROW_PROBLEMS))

# ---------- derived figures ----------
def money(x, decimals=2):
    """£ figure. decimals=None keeps whole pounds whole and shows pence otherwise."""
    if x is None: return "—"
    if decimals is None: decimals = 0 if float(x).is_integer() else 2
    return f"£{x:,.{decimals}f}"

for r in ROWS:
    r["cards"] = r.get("cards", 1)
    r["plan_region"] = r.get("plan_price_region", "UK")
    # A second card is a second purchase: the base extra has one already.
    if r["cards"] > 1: r["extra"] = round(r["extra"] + CARD * (r["cards"] - 1), 2)
    r["score_total"] = sum(r["score"].values())
    r["nosub3"] = round(r["price"] + r["extra"], 2)
    r["sub3"] = round(r["price"] + MONTHS * r["sub"], 2) if r["sub"] is not None else None
    # cheapest way to keep recordings for 3 years
    opts = []
    if r["free_records"]: opts.append(r["nosub3"])
    if r["sub3"] is not None: opts.append(r["sub3"])
    r["keep3"] = min(opts)
    # Which of the two 3-year figures the sort uses, and what to call it. The
    # page says so in words and bolds that cell, so the order never looks broken.
    if r["free_records"] and (r["sub3"] is None or r["nosub3"] <= r["sub3"]):
        r["keep_basis"], r["keep_note"] = "nosub", "records free, no plan"
    else:
        r["keep_basis"], r["keep_note"] = "sub", f"with the {r['sub_name']} plan"
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
        "Smart detection","Recorded history without subscription","What's paywalled","Subscription & UK price","Plan price region","Home Assistant / local-only",
        "Wi-Fi","Sources","Unverified / re-check","Last checked"])
    for r in ROWS:
        w.writerow([r["brand"],r["model"],REC_LABEL[r["rec"]],"/".join(POWER_LABEL[p] for p in r["power"]),f"{r['price']:.2f}",r["price_note"],S[r["price_src"]][1],
            r["best"],r["catch"],r["score_total"],f"{r['nosub3']:.2f}","" if r["sub3"] is None else f"{r['sub3']:.2f}",f"{r['keep3']:.2f}",r["maths_free"],r["maths_sub"],
            r["storage"],r["live"],r["alerts"],r["ai"],r["history"],r["paywalled"],r["sub_text"],r["plan_region"],r["ha_text"],r["wifi"],
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
def fnames(keys):
    """The same footnotes, named. A row says which shop or page, not just a number."""
    return ", ".join(f'<a class="fn" href="#fn{FN[k]}" title="{e(S[k][0])}">{e(S[k][0])}</a>' for k in keys)


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

# The details panel in plain sentences. The table and the comparison keep the
# terse values, which are for someone who already knows the words; this is the
# version for someone who has never fitted a doorbell. No new facts: each
# sentence says the same thing as the row it stands in for.
PLAIN = {
 "ring": ("Runs on the battery, or you can wire it to your existing chime.",
          "None. The doorbell has no storage of its own and no hub to hold the footage."),
 "nest": ("Runs on the battery, or you can wire it to your existing chime.",
          "None. The doorbell has no storage of its own and no hub to hold the footage."),
 "eufy-e340": ("Runs on the battery, or you can wire it to your existing chime.",
          "8 GB is built into the doorbell, so it records on its own. The optional HomeBase S380 (16 GB, expandable) holds more."),
 "reo-wifi": ("Wired to your existing doorbell chime.",
          "A microSD card in the doorbell (up to 256 GB), or a Reolink NVR. It also streams over RTSP and ONVIF, so other apps can pull the video."),
 "reo-poe": ("Powered by an Ethernet cable (PoE): one cable carries both the power and the video, so there is no separate power supply to run.",
          "A microSD card in the doorbell, or a Reolink NVR. It also streams over RTSP and ONVIF, so other apps can pull the video."),
 "reo-batt": ("Runs on the battery, or you can wire it to your existing chime.",
          "A microSD card in the doorbell, or a Reolink Home Hub indoors (up to 1 TB)."),
 "tapo-d230": ("Battery only.",
          "A microSD card (up to 512 GB) in the indoor H200 hub, so the footage stays in the house."),
 "tapo-td21": ("Battery only.",
          "A microSD card (up to 512 GB) in the doorbell itself, so the card comes out with the doorbell if it is stolen."),
 "arlo": ("Battery only, though you can wire it to an existing chime for trickle charging.",
          "Recording needs an Arlo SmartHub (VMB4540, with a USB stick) or a Base Station."),
 "aqara-g4": ("Runs on AA batteries, or you can wire it to your existing chime.",
          "A microSD card (up to 512 GB) in the indoor chime."),
 "blink": ("Battery only.",
          "Recording needs a Sync Module 2 and a USB stick (1–256 GB). The clips are not encrypted."),
 "ezviz-ep3x": ("Battery only.",
          "32 GB is built in, so no card is needed."),
 "ezviz-db2": ("Battery only.",
          "A microSD card (up to 256 GB) in the indoor chime that comes with it."),
 "hik": ("Wired to your existing doorbell chime.",
          "A microSD card (up to 128 GB), and it can stream to an NVR over RTSP."),
}
_missing=[r["id"] for r in ROWS if r["id"] not in PLAIN]
if _missing: raise SystemExit(f"PLAIN has no entry for: {_missing}")
_stale=[k for k in PLAIN if k not in {r["id"] for r in ROWS}]
if _stale: raise SystemExit(f"PLAIN has an entry for a row that does not exist: {_stale}")

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
    # The price is the link to the page the price came from, so the promise in
    # the intro ("each one links to its source") is kept in the row itself.
    pm=money(r["price"], None);psrc=S[r["price_src"]]
    price=f'<a class="buy" href="{e(psrc[1])}" rel="nofollow noopener noreferrer" title="Check the price at {e(psrc[0])}" aria-label="{pm} at {e(psrc[0])}">{pm}</a>'
    ncls=" keep" if r["keep_basis"]=="nosub" else ""
    scls=" keep" if r["keep_basis"]=="sub" else ""
    # The bold figure follows the sort. The default sort is the 3-year cost to
    # keep recordings, so the cell that figure comes from starts bold, and the
    # sort note says so. Where the plan is the cheapest way to record, the
    # cell says so too, or the bold number reads as the wrong figure.
    knote='<span class="note">cheapest: with a plan</span>' if r["keep_basis"]=="sub" else ""
    rows_html.append(f'''<tbody class="item" id="m-{r['id']}" data-id="{r['id']}" data-keep="{r['keep_basis']}"{vattr} data-rec="{r['rec']}" data-recv="{REC_RANK[r['rec']]}" data-ha="{r['ha']}" data-power="{pw}" data-price="{r['price']}" data-keep3="{r['keep3']}" data-nosub3="{r['nosub3']}" data-sub3="{r['sub3'] if r['sub3'] is not None else 0}" data-score="{sc}" data-model="{e((r['brand']+' '+r['model']).lower())}" data-idx="{i}">
<tr class="main">
<td class="c-cmp"><label class="cmp-w"><input type="checkbox" class="cmp" value="{r['id']}" aria-label="Compare {e(r['brand'])} {e(r['model'])}"><span class="cmp-cap" aria-hidden="true">Compare</span></label></td>
<th scope="row" class="c-model"><div class="mcell">{zoom(r,"sm")}<div><span class="brand">{e(r['brand'])}</span> <span class="mname">{e(r['model'])}</span>{vtag}<span class="best">Best for: {e(r['best'])}</span></div></div></th>
<td class="c-rec" data-label="Records free?"><span class="rec rec-{r['rec']}">{REC_LABEL[r['rec']]}</span>{fn([r['rec_src']])}</td>
<td class="c-price num" data-label="Price">{price}</td>
<td class="c-score" data-label="Free features"><span class="score"><b>{sc}</b>/8</span><span class="bar" aria-hidden="true"><i style="transform:scaleX({sc/8:.3f})"></i></span></td>
<td class="c-nosub num{ncls}" data-label="3 years, no plan">{money(r['nosub3'], None)}{'' if r['free_records'] else '<span class="note">no recordings</span>' if r['rec']=='no' else '<span class="note">3 hrs history</span>'}</td>
<td class="c-sub num{scls}" data-label="3 years, with plan" data-region="{r['plan_region']}">{money(r['sub3'], None) if r['sub3'] is not None else '<span class="noplan">No plan</span>'}{knote}{'<span class="vh">EU price, not a UK quote</span>' if r['plan_region'] == 'EU' else ''}</td>
<td class="c-catch" data-label="Main catch">{e(r['catch'])}<div class="more-w"><button type="button" class="more" aria-expanded="false" aria-controls="d-{r['id']}">Details</button></div></td>
</tr>
<tr class="detail" id="d-{r['id']}" hidden><td colspan="8"><div class="dgrid">
<figure class="dimg">{zoom(r,"lg")}</figure>
<dl class="dspec">
<div class="pair"><dt>Power</dt><dd>{e(PLAIN[r['id']][0])}{pnote}</dd></div>
<div class="pair"><dt>Wi-Fi</dt><dd>{e(r['wifi'])}</dd></div>
<div class="pair"><dt>Storage</dt><dd>{e(PLAIN[r['id']][1])}</dd></div>
<div class="pair"><dt>Live view</dt><dd>{e(r['live'])}</dd></div>
<div class="pair"><dt>Motion alerts</dt><dd>{e(r['alerts'])}</dd></div>
<div class="pair"><dt>Smart detection</dt><dd>{e(r['ai'])}</dd></div>
<div class="pair"><dt>History without a plan</dt><dd>{e(r['history'])} {fn([r['history_src']])}</dd></div>
<div class="pair"><dt>Behind the paywall</dt><dd>{e(r['paywalled'])}</dd></div>
<div class="pair"><dt>Plans</dt><dd>{e(r['sub_text'])}</dd></div>
<div class="pair"><dt>Home Assistant</dt><dd>{e(r['ha_text'])} {fn([r['ha_src']])}</dd></div>
<div class="pair"><dt>3 years, no plan</dt><dd class="maths">{e(r['maths_free'])}</dd></div>
<div class="pair"><dt>3 years, with plan</dt><dd class="maths">{e(r['maths_sub'])}</dd></div>
<div class="pair"><dt>Score breakdown</dt><dd>{"; ".join(f"{lbl} {r['score'][k]}/{mx}" for k,lbl,mx in SCORE_PARTS)}</dd></div>
</dl></div>
{unv}
<p class="srcs">Sources: {fnames(r['src'])}</p></td></tr>
</tbody>''')

data_js = json.dumps({r["id"]:{
 "name":f"{r['brand']} {r['model']}","rec":REC_LABEL[r["rec"]],"recCls":r["rec"],"price":money(r["price"], None),"score":f"{r['score_total']}/8",
 "nosub3":money(r["nosub3"], None),"sub3":money(r["sub3"], None) if r["sub3"] is not None else "No plan","keep3":r["keep3"],"keepNote":r["keep_note"],"region":r["plan_region"],"best":r["best"],"catch":r["catch"],"power":" / ".join(POWER_LABEL[p] for p in r["power"]),
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

# The page's static parts live in their own files so an editor, a linter and
# `node --check` can see them. They ship as separate asset files, not inline:
# with gzip on, that is 26.2KB on a first visit against 29.0KB inlined, and
# 13.5KB on a repeat visit. The version in the URL is a content hash, so a
# change busts the cache, while the path stays stable: GitHub Pages caches HTML
# for ten minutes, and a hashed filename that a deploy deletes would leave that
# cached copy asking for a file that no longer exists.
PAGE_CSS = open(os.path.join(HERE, "page.css"), encoding="utf-8").read()
PAGE_JS = (open(os.path.join(HERE, "page.js"), encoding="utf-8").read()
           .replace("/*@@DATA@@*/{}", data_js).replace("@@CHECKED@@", CHECKED))

def content_version(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:10]


CSS_FILE, JS_FILE = "assets/page.css", "assets/page.js"
CSS_URL = f"{CSS_FILE}?v={content_version(PAGE_CSS)}"
JS_URL = f"{JS_FILE}?v={content_version(PAGE_JS)}"

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
<link rel="stylesheet" href="{CSS_URL}">
</head><body>
<a class="skip" href="#tbl">Skip to the comparison table</a>
<div class="wrap">
<div class="mast" id="top"><div>SubFree UK <span>Gadgets that work without a subscription</span></div><button type="button" id="theme"><i aria-hidden="true"></i><span>Dark mode</span></button></div>
<header class="intro">
<div>
<h1>Video doorbells that work without a subscription</h1>
<p class="dek">{len(ROWS)} UK doorbells, checked against manufacturer pages and independent reviews: free features, paywalls and 3-year costs.</p>
<p class="meta"><b>Last checked {CHECKED}.</b> No affiliate links, no tracking, no cookies. Spotted a mistake? <a href="{GITHUB}/issues/new">Open an issue</a>.</p>
<p class="vshort"><b class="vlab">Short answer</b>
<span class="v-best">{vlink(["reo-poe"],"Reolink PoE")} is the best overall without fees.</span>
<span class="v-batt">{vlink(["tapo-d230"],"Tapo D230S1")} is the easiest battery one.</span>
<span class="v-avoid">{vlink(["ring"],"Ring")} needs a plan. {vlink(["blink"],"Blink")} and {vlink(["arlo"],"Arlo")} need extra kit.</span>
</p>
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
<p class="range-txt" id="f-range">£{MINP} to £{maxp}</p>
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
</select><p class="sortnote" id="sortnote">Order: 3-year cost to keep recordings (the bold figure).</p></div>
<p class="count">Tick up to 3 rows to compare. <span id="count">{len(ROWS)}</span> of {len(ROWS)} shown · <button type="button" class="link" id="reset">Reset</button><span id="cmp-sep" hidden> · </span><button type="button" class="link" id="cmp-inline" hidden>Compare</button><span id="cmp-cap" class="cap" hidden></span></p>
</form>
<noscript><p class="nojs">Filters, sorting, compare and the per-model details need JavaScript. All {len(ROWS)} doorbells are listed below.</p></noscript>
<script>if(window.matchMedia('(max-width:520px)').matches)document.getElementById('filters').open=false;</script>

<section id="compare" hidden>
<div class="cmp-head"><h2 id="cmp-h" tabindex="-1">Side by side</h2><div class="cmp-actions"><label class="cmpo" id="cmp-diff-w" hidden><input type="checkbox" id="cmp-diff"> Differences only <span id="cmp-dupes"></span></label><span class="cmp-links"><button type="button" class="link" id="cmp-copy">Copy shortlist</button><button type="button" class="link" id="cmp-clear">Clear</button><button type="button" class="link" id="cmp-close">Close</button></span></div></div>
<p class="cmp-note" id="cmp-note" role="status" hidden></p>
<p class="cmp-cue" id="cmp-cue" hidden></p>
<div class="cmp-wrap"><div class="cmp-scroll" tabindex="0" role="region" aria-label="Comparison table, scrolls sideways"><table class="cmp-t" id="cmp-table"></table></div></div>
</section>

<p class="vkey" id="vkey"><span class="v-best"><b>Green</b>: a best pick that records without paying</span><span class="v-batt"><b>Blue</b>: the best battery pick</span><span class="v-avoid"><b>Red</b>: avoid if you will not pay a monthly plan</span></p>
<div id="totop-s" aria-hidden="true"></div>
<div class="tbl-w"><div class="prog" aria-hidden="true"><i></i></div>
<table class="main-t" id="tbl" tabindex="-1">
<thead><tr>
<th scope="col" class="c-cmp"><span class="cmp-h">Compare</span></th>
<th scope="col" data-sort="model" aria-sort="none"><button type="button">Model</button></th><th scope="col" data-sort="recv" aria-sort="none"><button type="button">Records free?</button></th><th scope="col" class="num" data-sort="price" aria-sort="none"><button type="button">Price</button></th><th scope="col" data-sort="score" aria-sort="none"><button type="button">Free features</button></th>
<th scope="col" class="num" data-sort="nosub3" aria-sort="none"><button type="button" aria-label="3-year cost, no plan, footnote a">3-year cost, no plan</button><a class="mk" href="#m-a" aria-label="How the 3-year cost without a plan is worked out">a</a></th><th scope="col" class="num" data-sort="sub3" aria-sort="none"><button type="button" aria-label="3-year cost, with plan, footnote b">3-year cost, with plan</button><a class="mk" href="#m-b" aria-label="How the 3-year cost with a plan is worked out">b</a></th><th scope="col">Main catch</th>
</tr></thead>
{''.join(rows_html)}
</table></div>
<p class="empty" id="empty" hidden><span id="empty-txt">Nothing matches those filters.</span> <button type="button" class="link" id="near" hidden></button> <button type="button" class="link" id="empty-reset">Reset filters</button></p>

<section class="method" id="method">
<div>
<h2>How we worked it out</h2>
<p id="m-a"><sup>a</sup> <b>3 years, no plan</b> = price + anything you must add to record for free (Blink's Sync Module 2 at £39.99, Arlo's SmartHub at £105.07, and a microSD card or USB stick, assumed at {money(CARD)}; that last figure isn't from a cited source). Ring and Nest can't keep recordings this way, which is shown next to the figure.</p>
<p id="m-b"><sup>b</sup> <b>3 years, with plan</b> = price + 36 × the cheapest UK monthly plan that adds cloud recording for one device. Paying yearly is usually cheaper. The EZVIZ plan figure is the EU price because EZVIZ shows UK pricing only inside its app. Every model's sums are under <i>Details</i>.</p>
<p><b>Free-feature score (out of 8):</b> records for free (2 = out of the box, 1 = with extra kit or only briefly), free live view (1), free motion alerts (1), free smart detection (1), storage included in the box (1), local Home Assistant support (2 = official and local, 1 = unofficial or generic).</p>
<p><b>Plain terms.</b> <i>PoE</i> (Power over Ethernet) sends power and video down one network cable. An <i>NVR</i> is a recorder box that stores footage from several cameras. A <i>microSD</i> card is the small memory card that sits inside many doorbells or their indoor chime. <i>2.4 GHz only</i> means the doorbell cannot join a 5 GHz network, so it will not show up on a phone that is on 5 GHz. <i>Home Assistant</i> is free software that keeps your smart home on your own network instead of a manufacturer's cloud.</p>
<p>Batteries, electricity, installation (except Hikvision, where the price includes fitting) and future price rises are left out. Anything not yet confirmed is listed under <i>Not yet verified</i> in each model's details.</p>
<p>Photos are the manufacturers' own, from their product pages: {photo_credits}.{f" No reliable official photo for: {no_photo}." if no_photo else ""}</p>
</div>
<details class="srcs" id="sources" open><summary><h2 class="srcs-t">Sources <span class="srcs-n">{len(order)} links</span></h2></summary><div class="fns-wrap">{fn_list}</div></details>
</section>
<footer class="foot">
<p>Last checked {CHECKED}. {len(ROWS)} UK doorbells, no affiliate links, no tracking. <a href="{GITHUB}/issues/new">Open an issue</a> · <a href="#tbl">Back to the table</a> · <a href="#top">Back to top</a>.</p>
<p>SubFree UK is a personal comparison of UK video doorbells, put together by <a href="{GITHUB}">lydenyardley</a> to show which ones record without a subscription. Every price links to the page it came from, so you can check it yourself. Spotted a mistake? <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
</footer>
</main>
</div>
<div class="tray" id="tray" hidden><span id="tray-txt"></span><button type="button" id="tray-go">Compare</button><button type="button" class="ghost" id="tray-clear">Clear</button></div>
<button type="button" class="totop" id="totop" hidden aria-label="Back to top"><span aria-hidden="true">↑</span></button>
<dialog id="lightbox" aria-labelledby="lb-name">
<button type="button" class="lb-x" id="lb-x" aria-label="Close photo">✕</button>
<div id="lb-img"></div>
<div class="lb-bar"><span id="lb-name"></span><button type="button" class="link" id="lb-close">Close</button></div>
</dialog>
<script src="{JS_URL}"></script>
</body></html>'''
# One page, one name. The second filename used to be a byte-identical copy;
# it is now a redirect so an old link still lands on the canonical URL.
ALIAS = '''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<title>Moved: the doorbell comparison</title>
<link rel="canonical" href="https://lydenyardley.github.io/subfree-uk/">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=./">
</head><body><p>This page has moved to the <a href="./">UK doorbell comparison</a>.</p></body></html>'''

# A mistyped link should land on the site's own page, not on a hosting
# company's. GitHub Pages serves this file for any path it cannot find, so
# the links in it are root-relative and work at any depth.
NOT_FOUND = f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<title>Page not found | SubFree UK</title>
<meta name="description" content="That page does not exist. The UK video doorbell comparison is on the home page.">
<link rel="stylesheet" href="{SITE}{CSS_FILE}?v={content_version(PAGE_CSS)}">
</head><body>
<div class="wrap">
<div class="mast"><div>SubFree UK <span>Gadgets that work without a subscription</span></div></div>
<main class="nf">
<h1>Page not found</h1>
<p>That link does not lead anywhere. The comparison of UK video doorbells that record without a subscription is on the home page, and it is one page.</p>
<a class="nf-btn" href="{SITE}">See the doorbell comparison</a>
</main>
</div>
</body></html>'''


def write():
    if _CHECKED_DATE > date.today():
        raise SystemExit(
            f"CHECKED_ISO is {CHECKED_ISO}, which is in the future; fix the date before building"
        )
    open(os.path.join(ROOT,"index.html"),"w",encoding="utf-8").write(page)
    open(os.path.join(ROOT,"doorbells.html"),"w",encoding="utf-8").write(ALIAS)
    open(os.path.join(ROOT,"404.html"),"w",encoding="utf-8").write(NOT_FOUND)
    assets = os.path.join(ROOT, "assets")
    os.makedirs(assets, exist_ok=True)
    for name, text in ((CSS_FILE, PAGE_CSS), (JS_FILE, PAGE_JS)):
        open(os.path.join(ROOT, name), "w", encoding="utf-8").write(text)
    # The one-off content-hashed names from the first version of this change.
    for name in os.listdir(assets):
        if name.startswith("page-") and name.endswith((".css", ".js")):
            os.remove(os.path.join(assets, name))
    print(len(ROWS),"rows written")
    for r in sorted(ROWS,key=lambda r:r["keep3"]): print(f"{r['brand']:14} {r['model']:38} score {r['score_total']}  nosub {r['nosub3']:8.2f}  sub {r['sub3'] if r['sub3'] else '-':>8}  keep {r['keep3']:.2f}")
    open_rows=[r for r in ROWS if r["unverified"]]
    print(f"\nUnverified ({len(open_rows)} of {len(ROWS)} rows):" + (" none" if not open_rows else ""))
    for r in open_rows: print(f"  {r['brand']} {r['model']}: {r['unverified'].replace('£','GBP ')}")

if __name__ == "__main__":
    write()
