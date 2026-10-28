"""The doorbell dataset, its sources and the figures derived from them.

No writes and no exits: reading this module is free, so a tool that wants the
data, or the day it was checked, does not rewrite the page. `build.py` imports
it and writes the files; `check.py` imports it and recomputes them.

A row is a dict with the REQUIRED_ROW_KEYS, optionally a power_note, cards or
plan_price_region, and the DERIVED_ROW_KEYS added below. `row_problems()` is
the guard: `build.write()` runs it before writing anything and `check.py` runs
it over the shipped files, so an unknown key or a source that does not resolve
fails by name instead of printing nothing.
"""

from datetime import date
from math import ceil
from urllib.parse import urlparse

from catalog import DOORBELLS as CAT

# The one hand-typed fact: the day the prices and plans were checked. ISO, so
# the age can be counted; build/check.py warns after 30 days and fails at 60.
CHECKED_ISO = "2026-10-19"
_CHECKED_DATE = date.fromisoformat(CHECKED_ISO)
CHECKED = f"{_CHECKED_DATE.day} {_CHECKED_DATE:%B %Y}"

# The two sundries the 3-year sums need, read on 26 October 2026 as the best
# UK price a buyer can pay for the leading brand's right product: the High
# Endurance card is the one SanDisk makes for home monitoring, and the Ultra
# Curve is the plain 64 GB stick the SmartHub and the Sync Module 2 take. Both
# figures are a UK retailer's own page, in S as sandisk_card and sandisk_stick;
# Amazon was the cheapest delivered of the UK shops that publish a price for
# them (SanDisk £25.99 and Argos £26.99 for the card, 7DayShop £27.99, Currys
# £43.99, and a cheaper card at Senetic whose £15.31 delivery made it dearer).
# A row that buys one names it in extra_src, so its card lists the price.
CARD = 25.37   # SanDisk High Endurance 64 GB microSDXC (SDSQQNR-064G-GN6IA)
STICK = 11.99  # SanDisk Ultra Curve 64 GB USB 3.2 flash drive (SDCZ550)
MONTHS = CAT["months"]

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
 "sandisk_card": ("Amazon UK: SanDisk High Endurance 64 GB", "https://www.amazon.co.uk/SanDisk-Endurance-Monitoring-Dashcams-MicroSDXC/dp/B07P3D6Y5B"),
 "sandisk_stick": ("Amazon UK: SanDisk Ultra Curve 64 GB", "https://www.amazon.co.uk/SANDISK-Computers-Desktops-RescuePRO-Recovery/dp/B0B42FNF15"),
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
 rec_src="ring_plans", history_src="ring_plans", ha_src="ha_ring", plan_src="ring_plans", unverified=""),
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
 rec_src="nest_plans", history_src="nest_plans", ha_src="ha_nest", plan_src="nest_prem", unverified=""),
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
 rec_src="eufy_prod", history_src="eufy_prod", ha_src="ha_eufy", plan_src="eufy_cloud", unverified=""),
dict(id="reo-wifi", brand="Reolink", model="Video Doorbell WiFi", rec="yes", power=["wired"], ha=2,
 price=93.49, price_note="Reolink UK sale price (RRP £109.99)", price_src="reo_store",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
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
 src=["reo_store","ha_reo","reo_cloud","sha_nosub","sandisk_card"],
 rec_src="reo_store", history_src="reo_store", ha_src="ha_reo", plan_src="reo_cloud", unverified=""),
dict(id="reo-poe", brand="Reolink", model="Video Doorbell PoE", rec="yes", power=["poe"], ha=2,
 price=69.99, price_note="Reolink UK sale price (RRP £99.99)", price_src="reo_store",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No Reolink Cloud plan",
 best="The most reliable, fully local setup, if you can run an Ethernet cable",
 catch="Needs an Ethernet cable to the door and a PoE switch or injector.",
 storage="microSD and/or NVR; RTSP/ONVIF", live="Yes", alerts="Yes", ai="Free: person detection",
 history="Yes, motion-triggered or 24/7 recording", paywalled="Nothing",
 sub_text="None. Reolink's doorbell FAQ says the PoE model cannot use Reolink Cloud; it records to microSD or an NVR",
 ha_text="Official, fully local integration (Local Push, Platinum).", wifi="Wired Ethernet",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=2),
 src=["reo_store","ha_reo","reo_faq","sandisk_card"],
 rec_src="reo_faq", history_src="reo_faq", ha_src="ha_reo", plan_src="reo_faq", unverified=""),
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
 rec_src="reo_batt", history_src="reo_batt", ha_src="ha_reo", plan_src="reo_cloud", unverified=""),
dict(id="tapo-d230", brand="TP-Link Tapo", model="D230S1", rec="yes", power=["battery"], ha=1,
 price=84.99, price_note="Tapo UK (RRP £94.99)", price_src="tapo_d230",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
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
 src=["tapo_d230","tapo_care","ha_tplink","er_tapo","sandisk_card"],
 rec_src="tapo_d230", history_src="tapo_d230", ha_src="ha_tplink", plan_src="tapo_care", unverified=""),
dict(id="tapo-td21", brand="TP-Link Tapo", model="TD21", rec="yes", power=["battery"], ha=0,
 price=44.99, price_note="Tapo UK sale price (RRP £56.00)", price_src="tapo_td21",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=2.99, sub_name="Tapo Care",
 best="The tightest budget",
 catch="Basic, and the microSD card sits in the doorbell, so a thief takes the footage with it.",
 storage="microSD up to 512 GB, in the doorbell itself", live="Yes", alerts="Yes", ai="Free: person detection",
 history="Yes, on card", paywalled="30-day cloud history, snapshot notifications, Smart Sort",
 sub_text="Optional Tapo Care from £2.99/month",
 ha_text="Not listed as supported by Home Assistant's official TP-Link integration, and no local route is documented.", wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["tapo_td21","tapo_care","tapo_td21_manual","ha_tplink","sandisk_card"],
 rec_src="tapo_td21", history_src="tapo_td21", ha_src="ha_tplink", plan_src="tapo_care", unverified=""),
dict(id="arlo", brand="Arlo", model="Essential Video Doorbell 2K (2nd gen)", rec="kit", power=["battery"], ha=0,
 power_note="Can be wired to an existing chime for trickle charging, but still runs on its battery.",
 price=84.99, price_note="Argos half price, doorbell + chime bundle (was £169.99)", price_src="argos_arlo",
 extra=round(105.07 + STICK, 2), extra_note="+ Arlo SmartHub £105.07 + SanDisk 64 GB USB stick",
 extra_src="sandisk_stick", kit_src="amz_arlohub", kit_label="SmartHub", kit_price=105.07, free_records=True,
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
 src=["argos_arlo","arlo_blog","arlo_plans","arlo_faq","arlo_doorbell","arlo_hubcompat","amz_arlohub","tr_arlo","ambient_arlo","ha_arlo","sandisk_stick"],
 rec_src="arlo_blog", history_src="arlo_doorbell", ha_src="ha_arlo", plan_src="arlo_plans", unverified=""),
dict(id="aqara-g4", brand="Aqara", model="Video Doorbell G4", rec="yes", power=["battery","wired"], ha=1,
 price=84.99, price_note="Amazon UK", price_src="amz_aqara",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
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
 src=["amz_aqara","aqara_eu","aqara_specs","ha_homekit","sandisk_card"],
 rec_src="aqara_specs", history_src="aqara_specs", ha_src="ha_homekit", plan_src="aqara_specs", unverified=""),
dict(id="blink", brand="Blink", model="Battery Doorbell 2K+", rec="kit", power=["battery"], ha=0,
 price=69.99, price_note="Amazon UK RRP (deals as low as £29.99)", price_src="amz_blink",
 extra=round(39.99 + STICK, 2), extra_note="+ Sync Module 2 £39.99 + SanDisk 64 GB USB stick",
 extra_src="sandisk_stick", kit_src="camel_sm2", kit_label="Sync Module 2", kit_price=39.99, free_records=True,
 sub=2.50, sub_name="Blink Basic",
 best="The cheapest way into Amazon's ecosystem, if you catch a deal",
 catch="Saves nothing without a £40 Sync Module 2 and a USB stick, and live view cuts off after 5 minutes.",
 storage="Only through a Sync Module 2 + USB stick (1–256 GB); clips aren't encrypted", live="Capped at 5 minutes",
 alerts="Yes", ai="Paid (person and vehicle detection)", history="None without a Sync Module 2",
 paywalled="Cloud clips, person/vehicle detection, 90-minute live view, AI descriptions",
 sub_text="Blink Basic £2.50/month (£24.99/year); Plus £8/month; Basic AI £5.49/month",
 ha_text="Official integration, but it goes through Blink's cloud.", wifi="2.4 GHz (Blink requirement)",
 score=dict(rec=1,live=0,alerts=1,ai=0,storage=0,ha=0),
 src=["amz_blink","camel_sm2","blink_plans","blink_sm2","ha_blink","sandisk_stick"],
 rec_src="blink_sm2", history_src="blink_sm2", ha_src="ha_blink", plan_src="blink_plans", unverified=""),
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
 rec_src="amz_ep3x", history_src="ezviz_blog", ha_src="ha_ezviz", plan_src="ezviz_cloud", plan_price_region="EU", unverified="CloudPlay's UK price is app-only, so the £4.99 in the plan column is the published EU price, not a UK quote."),
dict(id="ezviz-db2", brand="EZVIZ", model="DB2 Pro Kit", rec="yes", power=["battery"], ha=0,
 price=114.99, price_note="ER Tech, UK retailer", price_src="ertech_db2",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=4.99, sub_name="EZVIZ CloudPlay 7-day",
 best="Flats and rentals: no wiring, and footage stays indoors in the chime",
 catch="2.4 GHz Wi-Fi only, and the card is sold separately.",
 storage="microSD (up to 256 GB) in the included indoor chime", live="Yes", alerts="Yes",
 ai="Free: PIR plus human-shape detection", history="Yes, on the chime's card", paywalled="Nothing essential",
 sub_text="Optional CloudPlay. UK price is app-only; EU €4.99/month (7 days), so treat the plan column as an estimate",
 ha_text="Official integration, but it goes through EZVIZ's cloud; this battery model isn't named in its supported list.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["ertech_db2","ezviz_blog","ezviz_cloud","ezviz_terms","ha_ezviz","sandisk_card"],
 rec_src="ertech_db2", history_src="ertech_db2", ha_src="ha_ezviz", plan_src="ezviz_cloud", plan_price_region="EU", unverified="CloudPlay's UK price is app-only, so the £4.99 in the plan column is the published EU price, not a UK quote."),
dict(id="hik", brand="Hikvision", model="DS-KB6003-WIP", rec="yes", power=["wired"], ha=1,
 price=295.00, price_note="Only UK listing found (fitted install); the model is discontinued", price_src="eagle_hik",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan",
 best="Only worth it if an installer is fitting a Hikvision system anyway",
 catch="Discontinued by Hikvision, and the only UK listing we found is a fitted install at £295.",
 storage="microSD up to 128 GB; RTSP to an NVR", live="Yes (Hik-Connect app)", alerts="Yes (motion)",
 ai="None", history="Yes, on card or NVR", paywalled="Nothing", sub_text="None",
 ha_text="Works as a generic RTSP camera.", wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=0,storage=0,ha=1),
 src=["eagle_hik","hik_ds","hik_4gon","sandisk_card"],
 rec_src="hik_ds", history_src="hik_ds", ha_src="hik_ds", plan_src="hik_ds", unverified=""),
]

# ---------- each row's verdict and its plain words ----------
# Authored beside the rows and attached to them below, so a row carries its own
# verdict and sentences by the time anything reads it.
VERDICT = {
    "reo-poe": "best", "reo-wifi": "wired", "reo-batt": "batt",
    "tapo-d230": "easy", "ring": "avoid", "blink": "avoid", "arlo": "avoid",
}
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

# ---------- row shape ----------
# The unknown-key test is what catches a misspelling, which would otherwise read
# as a valid optional field and quietly skip a sentence or print nothing. The
# build runs this before it writes anything, and the audit runs it over the
# files that shipped.
REQUIRED_ROW_KEYS = (
    "id", "brand", "model", "rec", "power", "ha", "price", "price_note",
    "price_src", "extra", "extra_note", "free_records", "sub", "sub_name",
    "best", "catch", "storage", "live", "alerts", "ai", "history",
    "paywalled", "sub_text", "ha_text", "wifi", "score", "src", "unverified",
    "rec_src", "history_src", "ha_src", "plan_src",
) + CAT["required_keys"]
OPTIONAL_ROW_KEYS = (
    "power_note", "cards", "plan_price_region", "extra_src", "kit_src", "kit_label",
    "kit_price",
)
DERIVED_ROW_KEYS = (
    "score_total", "nosub3", "sub3", "keep3", "maths_free", "maths_sub",
    "plan_region", "keep_basis", "keep_note", "verdict", "plain",
)

def row_problems(cat=None):
    """Every row against the category's row shape, by name.

    `rows.py` runs this before `build.py` writes anything, and the audit runs it
    over the files that shipped. A missing key, an unknown key, a source that
    does not resolve, a source that is not https, a verdict outside the
    category's vocabulary and a row with no plain sentence are all named rather
    than printed blank.
    """
    cat = cat or CAT
    rows = cat.get("rows") or ROWS
    sources = cat.get("sources") or S
    problems = []
    for r in rows:
        rid = r.get("id", "(no id)")
        missing = [k for k in REQUIRED_ROW_KEYS if k not in r]
        allowed = REQUIRED_ROW_KEYS + OPTIONAL_ROW_KEYS + DERIVED_ROW_KEYS
        unknown = [k for k in r if k not in allowed]
        if missing: problems.append(f"{rid}: missing {', '.join(missing)}")
        if unknown: problems.append(f"{rid}: unknown {', '.join(unknown)}")
        for key in ("price_src", "rec_src", "history_src", "ha_src", "plan_src", "extra_src", "kit_src"):
            if key in r and r[key] not in sources:
                problems.append(f"{rid}: {key} {r[key]!r} is not in the category's sources")
            if key in r and r[key] not in r.get("src", []):
                problems.append(f"{rid}: {key} {r[key]!r} is not in the row's src list")
        if r.get("cards", 1) < 1:
            problems.append(f"{rid}: cards must be at least 1")
        if r.get("plan_price_region", "UK") not in ("UK", "EU"):
            problems.append(f"{rid}: plan_price_region must be UK or EU")
        # A row with no free route to a recording and no plan has nothing to
        # keep, so `keep3` has no figure to be. The build used to crash in
        # `min()` with no row named; it now fails here, in words.
        if not r.get("free_records") and r.get("sub") is None:
            problems.append(
                f"{rid}: no route keeps recordings (free_records is false and sub is None)"
            )
        # The fields a new row is most likely to get wrong, checked against the
        # vocabulary the page prints, so a typo names its row instead of raising
        # a KeyError inside the CSV writer or printing a blank cell.
        if r.get("rec") not in REC_LABEL:
            problems.append(
                f"{rid}: rec {r.get('rec')!r} is not one of {', '.join(REC_LABEL)}"
            )
        for value in r.get("power") or ():
            if value not in POWER_LABEL:
                problems.append(
                    f"{rid}: power {value!r} is not one of {', '.join(POWER_LABEL)}"
                )
        if not isinstance(r.get("ha"), int) or isinstance(r.get("ha"), bool) or not 0 <= r["ha"] <= 2:
            problems.append(f"{rid}: ha {r.get('ha')!r} is not a whole number from 0 to 2")
        parts = r.get("score") or {}
        for key, value in parts.items():
            if key not in PART_MAX:
                problems.append(
                    f"{rid}: score {key!r} is not one of {', '.join(PART_MAX)}"
                )
            elif not isinstance(value, int) or not 0 <= value <= PART_MAX[key]:
                problems.append(
                    f"{rid}: score {key} is {value!r}, outside 0 to {PART_MAX[key]}"
                )
        missing_parts = [key for key in PART_MAX if key not in parts]
        if missing_parts:
            problems.append(f"{rid}: score is missing {', '.join(missing_parts)}")
        verdict = r.get("verdict")
        if verdict is not None and verdict not in cat["verdicts"]:
            problems.append(
                f"{rid}: verdict {verdict!r} is not one of {', '.join(cat['verdicts'])}"
            )
        if r.get("plain") is None:
            problems.append(f"{rid}: has no plain-language sentence")
        if r.get("kit_src") and not r.get("kit_label"):
            problems.append(f"{rid}: buys kit but names no kit_label for the method note")
        # The kit's own price is authored, not recovered by subtracting a sundry
        # from the row's extra: the note prints it, and it has to be the price
        # the cited page published for that box.
        if r.get("kit_src"):
            kit = r.get("kit_price")
            if not isinstance(kit, (int, float)) or kit <= 0:
                problems.append(f"{rid}: buys kit but names no kit_price")
                continue
            card = CARD * (r.get("cards", 1) - 1)
            want = round(kit + (STICK if r.get("extra_src") else 0) + card, 2)
            if abs(want - r["extra"]) > 0.005:
                problems.append(
                    f"{rid}: extra is {r['extra']:.2f}, but kit_price, the sundry and "
                    f"the cards come to {want:.2f}"
                )
    # A source is a page a reader clicks, so it has to be an https page: the
    # escaping on the way out keeps the markup intact, not the scheme honest.
    for key, (_, url) in sources.items():
        if urlparse(url).scheme != "https":
            problems.append(f"{key}: {url!r} is not an https page")
    ids = {r["id"] for r in rows}
    if rows is ROWS:      # the doorbell module's own tables
        for rid in VERDICT:
            if rid not in ids:
                problems.append(f"VERDICT has an entry for a row that does not exist: {rid}")
        for rid in PLAIN:
            if rid not in ids:
                problems.append(f"PLAIN has an entry for a row that does not exist: {rid}")
    headlines = [r["id"] for r in rows if r.get("verdict") == cat["headline"]]
    if not headlines:
        problems.append(f"no row carries the headline verdict {cat['headline']!r}")
    return problems


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
    r["verdict"] = VERDICT.get(r["id"])
    r["plain"] = PLAIN.get(r["id"])
    r["nosub3"] = round(r["price"] + r["extra"], 2)
    r["sub3"] = round(r["price"] + MONTHS * r["sub"], 2) if r["sub"] is not None else None
    # cheapest way to keep recordings for 3 years
    opts = []
    if r["free_records"]: opts.append(r["nosub3"])
    if r["sub3"] is not None: opts.append(r["sub3"])
    # A row with neither route has no total to print. `row_problems()` rejects
    # it by name before anything is written; `None` here keeps the module
    # importable so that the guard can run at all.
    r["keep3"] = min(opts) if opts else None
    # Which of the two 3-year figures the sort uses, and what to call it. The
    # page says so in words and bolds that cell, so the order never looks broken.
    if r["keep3"] is None:
        r["keep_basis"], r["keep_note"] = "none", "no way to keep recordings"
    elif r["free_records"] and (r["sub3"] is None or r["nosub3"] <= r["sub3"]):
        r["keep_basis"], r["keep_note"] = "nosub", "records free, no plan"
    else:
        r["keep_basis"], r["keep_note"] = "sub", f"with the {r['sub_name']} plan"
    m_free = f"{money(r['price'])}" + (f" + {money(r['extra'])} ({r['extra_note'].lstrip('+ ')})" if r["extra"] else "") + f" = {money(r['nosub3'])}"
    if not r["free_records"]: m_free += " (but no recordings)" if r["rec"]=="no" else " (3 hours of history only)"
    m_sub = (f"{money(r['price'])} + {MONTHS} × {money(r['sub'])} ({r['sub_name']}) = {money(r['sub3'])}" if r["sub3"] is not None else "No subscription offered or needed")
    r["maths_free"], r["maths_sub"] = m_free, m_sub

# 'brief' is a time limit, not missing hardware: Nest keeps 3 hours with no kit.
# The vocabulary comes from the category record, so the page, the CSV, the
# comparison and the checks all print the same words.
REC_LABEL = {key: label for key, label, _ in CAT["rec"]}
REC_RANK = {key: rank for key, _, rank in CAT["rec"]}
POWER_LABEL = dict(CAT["powers"])
SCORE_PARTS = list(CAT["score_parts"])
SCORE_MAX = CAT["score_max"]
PART_MAX = {key: maximum for key, _, maximum in SCORE_PARTS}
# The slider's ends are the data's own: a row priced below a typed-in floor
# would disappear from the default view of the page it was added to, and a
# ceiling off the handle's 5-step grid would snap the dearest row out of range
# just as quietly.
MINP = int(min(r["price"] for r in ROWS) // 10 * 10)
MAXP = int(ceil(max(r["price"] for r in ROWS) / 5) * 5)


# The category record is where a category is described, so that a second one is
# a second record and its rows, not an edit to every page of the build. The rows
# attach themselves to their record; a record with no rows fails the audit.
CAT["rows"] = ROWS
CAT["sources"] = S

# footnote numbering
order=[]
for r in ROWS:
    for k in r["src"]:
        if k not in order: order.append(k)
FN = {k:i+1 for i,k in enumerate(order)}
