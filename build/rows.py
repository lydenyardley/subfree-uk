"""The doorbell and camera dataset, its sources and the figures derived from them.

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

from catalog import CATEGORIES, DOORBELLS as CAT, labels

# Each category carries the day its own prices and plans were checked, because
# a second category lands on a different day from the first. ISO, so the age
# can be counted; build/check.py warns after 30 days and fails at 60.
for _cat in CATEGORIES:
    _day = date.fromisoformat(_cat["checked_iso"])
    _cat["checked_date"] = _day
    _cat["checked"] = f"{_day.day} {_day:%B %Y}"

# The two sundries the 3-year sums need, read on 26 October 2026 as the best
# UK price a buyer can pay for the leading brand's right product: the High
# Endurance card is the one SanDisk makes for home monitoring, and the Ultra
# Curve is the plain 64 GB stick the SmartHub and the Sync Module 2 take. Both
# figures are a UK retailer's own page, in S as sandisk_card and sandisk_stick;
# Amazon was the cheapest delivered of the UK shops that publish a price for
# them (SanDisk £25.99 and Argos £26.99 for the card, 7DayShop £27.99, Currys
# £43.99, and a cheaper card at Senetic whose £15.31 delivery made it dearer).
# A row that buys one names it in extra_src, so its card lists the price.
CARD = 26.99   # SanDisk High Endurance 64 GB microSDXC (SDSQQNR-064G-GN6IA), Argos
STICK = 15.99  # SanDisk Cruzer Blade 64 GB USB flash drive (SDCZ50), Argos

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
 "eufy_c31": ("eufy UK: C31", "https://www.eufy.com/uk/products/t8223311"),
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
 "arlo_hub": ("Arlo UK store: SmartHub", "https://www.arlo.com/en_gb/accessories/arlo-pro-smarthub"),
 "tr_arlo": ("Trusted Reviews, 2026", "https://www.trustedreviews.com/reviews/arlo-essential-3-2k-security-camera"),
 "ambient_arlo": ("The Ambient", "https://www.the-ambient.com/reviews/arlo-pro-6-2k-review/"),
 "aqara_uk": ("EasyGates: Aqara G4", "https://www.easygates.co.uk/product/aqara-smart-video-doorbell-g4/"),
 "amz_aqara": ("Amazon UK: Aqara G4", "https://www.amazon.co.uk/dp/B0BPHTL7MG"),
 "aqara_eu": ("Aqara EU store", "https://eu.aqara.com/products/aqara-video-doorbell-g4"),
 "aqara_specs": ("Aqara G4 specifications", "https://www.aqara.com/us/product/smart-video-doorbell-g4/specs/"),
 "ha_homekit": ("Home Assistant: HomeKit Device", "https://www.home-assistant.io/integrations/homekit_controller"),
 "amz_blink": ("Amazon UK: Blink 2K+", "https://www.amazon.co.uk/dp/B0G62K1Y6C"),
 "camel_sm2": ("Sync Module 2 RRP £39.99 (camelcamelcamel history; no non-Amazon UK seller)", "https://uk.camelcamelcamel.com/product/B08BJ9ZCZC"),
 "blink_plans": ("Blink UK plans", "https://blinkforhome.com/plans-uk"),
 "blink_sm2": ("Blink Sync Module 2 FAQ", "https://support.blinkforhome.com/en_GB/faq-sm2/faq-sync-module-2"),
 "ha_blink": ("Home Assistant: Blink", "https://www.home-assistant.io/integrations/blink/"),
 "amz_ep3x": ("Amazon UK: EZVIZ EP3x Pro", "https://www.amazon.co.uk/dp/B0CXJ272BY"),
 "ezviz_blog": ("EZVIZ UK: no-subscription guide", "https://www.ezviz.com/uk/blog/detail/best-video-doorbells-without-monthly-subscription-fees/2609214160772537"),
 "ezviz_cloud": ("EZVIZ CloudPlay (EU prices)", "https://www.ezviz.com/page/cloudplay"),
 "ezviz_terms": ("EZVIZ CloudPlay UK terms", "https://www.ezviz.com/uk/legal/cloudplay-paid-subscription-terms"),
 "ha_ezviz": ("Home Assistant: EZVIZ", "https://www.home-assistant.io/integrations/ezviz/"),
 "ertech_db2": ("ER Tech (UK retailer)", "https://www.ertech.co.uk/product/db2-pro/"),
 "sandisk_card": ("Argos: SanDisk High Endurance 64 GB", "https://www.argos.co.uk/product/2656586"),
 "sandisk_stick": ("Argos: SanDisk Cruzer Blade 64 GB", "https://www.argos.co.uk/product/3395891"),
 "eagle_hik": ("Eagle Security Solutions", "https://eaglesecuritysolutions.co.uk/p/door-entry-systems/wireless-intercoms/hikvision-ds-kb6003-wip-video-doorbell-fully-installed/"),
 "hik_ds": ("Hikvision datasheet", "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000083/S000000126/S000000127/OFR000160/M000001570/Data_Sheet/UD04258B_Spec-of-DS-KB6003-WIP-Wi-Fi-Doorbell_V1.4.6_20170519.pdf"),
 "ha_eufy": ("Home Assistant: eufy (ha-eufy-sdk)", "https://github.com/mega-yfue/ha-eufy-sdk"),
 "ha_arlo": ("Home Assistant: Aarlo (community)", "https://github.com/twrecked/hass-aarlo"),
 "hik_4gon": ("4Gon: Hikvision doorbell (discontinued)", "https://www.4gon.co.uk/hikvision-24v-dc-wifi-video-doorbell-dskb6003wip-p-8309.html"),
 # Cameras: the UK store's own page carries the price the sums use, and the
 # vendor product page carries the recording, storage and detection facts.
 "reo_gb_home": ("Reolink UK store", "https://store.reolink.com/gb/"),
 "reo_argus": ("Reolink UK: Argus 4 Pro", "https://reolink.com/gb/product/argus-4-pro/"),
 "reo_rlc820a": ("Reolink UK: RLC-820A", "https://reolink.com/gb/product/rlc-820a/"),
 "reo_e1out": ("Reolink UK: E1 Outdoor Pro", "https://reolink.com/gb/product/e1-outdoor-pro/"),
 "tapo_c660": ("Tapo UK: C660 KIT", "https://uk.store.tapo.com/products/tapo-c660-kit-4k-clarity-solar-powered-pan-tilt-battery-security-camera-kit"),
 "eufy_s340": ("eufy UK: SoloCam S340", "https://www.anker.com/uk/products/t81703w1"),
 "eufy_e30": ("eufy UK: Indoor Cam E30", "https://www.anker.com/uk/products/t8417221"),
 "ha_eufy_cam": ("Home Assistant: eufy-security (community)", "https://github.com/fuatakgun/eufy_security"),
 "aqara_g3": ("Aqara UK: Camera Hub G3", "https://www.aqara-shop.co.uk/product/aqara-camera-hub-g3/"),
 "aqara_e1": ("Aqara UK: Camera E1", "https://www.aqara-shop.co.uk/product/aqara-camera-e1/"),
 "ring_outpro": ("Ring UK: Outdoor Camera Pro (plug-in)", "https://en-uk.ring.com/products/stick-up-cam-pro-plug-in"),
 "amz_blink_cam": ("Amazon UK: Blink Outdoor 4", "https://www.amazon.co.uk/blink-camera-outdoor-4/dp/B0DHLTMW3X"),
 "amz_sm2": ("Amazon UK: Blink Sync Module 2", "https://www.amazon.co.uk/dp/B08BJ9ZCZC"),
 "blink_storage": ("Blink: local storage options", "https://support.blinkforhome.com/en_GB/blink-storage-options"),
 "tr_blink": ("Trusted Reviews: Blink 2K+ UK prices", "https://www.trustedreviews.com/news/blinks-cheapest-new-doorbell-has-a-feature-most-budget-rivals-still-miss"),
 "chester_ep3x": ("Chester Digital Supplies: EP3x Pro", "https://www.chesterdigitalsupplies.co.uk/ezviz-ep3x-pro"),
 "ezviz_ep3x": ("EZVIZ UK: EP3x Pro", "https://www.ezviz.com/uk/product/ep3x+pro/55935"),
 "amz_ring": ("Amazon UK: Ring Battery Doorbell 2K", "https://www.amazon.co.uk/dp/B0FHJ91JY5"),
 "amz_nest": ("Amazon UK: Nest Doorbell (battery)", "https://www.amazon.co.uk/dp/B0D96LS7Z2"),
 "amz_e340": ("Amazon UK: eufy E340", "https://www.amazon.co.uk/dp/B0CF8RPX5M"),
 "amz_c31": ("Amazon UK: eufy C31", "https://www.amazon.co.uk/dp/B0GSFQL25B"),
 "amz_td21": ("Amazon UK: Tapo TD21", "https://www.amazon.co.uk/dp/B0DGLVB89G"),
 # Smart rings: Amazon UK listings carry the GBP price for one size, and the
 # vendor's own page carries what the ring measures. The membership page is
 # Oura's; the others publish that no plan is needed.
 "amz_oura4": ("Amazon UK: Oura Ring 4", "https://www.amazon.co.uk/dp/B0D9WWB3WX"),
 "oura_membership": ("Oura Membership UK", "https://ouraring.com/membership"),
 "oura_free": ("Oura support: what a membership adds", "https://support.ouraring.com/hc/en-us/articles/4409086524819-Oura-Membership"),
 "ha_oura": ("Home Assistant: Oura (community)", "https://github.com/louispires/Oura-Home-Assistant-Integration"),
 "amz_ultra": ("Amazon UK: Ultrahuman Ring AIR", "https://www.amazon.co.uk/dp/B0H3B3GL17"),
 "uh_ring": ("Ultrahuman Ring AIR", "https://www.ultrahuman.com/ring/"),
 "uh_nosub": ("Ultrahuman: Ring AIR vs Ring PRO (no subscription)", "https://www.ultrahuman.com/blog/ultrahuman-ring-pro-vs-ring-air/"),
 "ha_ultra": ("Home Assistant: Ultrahuman (community)", "https://github.com/anant-j/Ultrahuman"),
 "amz_rc2": ("Amazon UK: RingConn Gen 2", "https://www.amazon.co.uk/dp/B0DG2QKMFX"),
 "rc2_product": ("RingConn Gen 2", "https://ringconn.com/products/ringconn-gen-2"),
 "amz_rc2a": ("Amazon UK: RingConn Gen 2 Air", "https://www.amazon.co.uk/dp/B0DWK4QQ7H"),
 "rc2a_product": ("RingConn Gen 2 Air", "https://ringconn.com/products/ringconn-gen-2-air"),
 "amz_rc3": ("Amazon UK: RingConn Gen 3", "https://www.amazon.co.uk/dp/B0GVSGY854"),
 "rc3_product": ("RingConn Gen 3", "https://ringconn.com/products/ringconn-gen-3"),
 "rc_nosub": ("RingConn: what the rings cost to run", "https://ringconn.com/blogs/guides/ringconn-cost-guide"),
 "amz_samsung": ("Amazon UK: Samsung Galaxy Ring", "https://www.amazon.co.uk/dp/B0DNTFZLDZ"),
 "samsung_support": ("Samsung UK: how to use Galaxy Ring", "https://www.samsung.com/uk/support/mobile-devices/how-to-use-the-samsung-galaxy-ring/"),
 "amazfit_uk": ("Amazfit UK: Helio Ring", "https://uk.amazfit.com/products/amazfit-helio-ring"),
 "amazfit_aura": ("Amazfit UK: Zepp Aura", "https://uk.amazfit.com/pages/zepp-aura"),
 "ha_zepp": ("Home Assistant: Zepp2Hass (community)", "https://community.home-assistant.io/t/zepp2hass-connect-your-amazfit-zepp-watch-to-home-assistant/973979"),
 "ha_index": ("Home Assistant integrations", "https://www.home-assistant.io/integrations/"),
}

# Amazon Associates: a row whose price links to Amazon UK carries the tag, so
# a new Amazon row is tagged without anyone remembering to. Only price and
# buy links are tagged; an Amazon page cited for a sundry stays a plain citation.
AMAZON_TAG = "subfreeuk-21"


def amazon_tagged(url):
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
    u = urlsplit(url)
    if not u.netloc.endswith("amazon.co.uk"):
        return url
    q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True) if k != "tag"]
    q.append(("tag", AMAZON_TAG))
    return urlunsplit(u._replace(query=urlencode(q)))


# rec: 'yes' records free out of the box / 'kit' needs extra hardware or very limited / 'no'
# score parts: rec 0-2, live 0-1, alerts 0-1, ai 0-1, storage_in_box 0-1, ha 0-2  (max 8)
ROWS = [
dict(cat="doorbells", id="ring", brand="Ring", model="Battery Video Doorbell 2K", rec="no", power=["battery","wired"], ha=0,
 price=79.99, price_note="Ring UK, in stock", price_src="ring_prod", buy="amz_ring",
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
dict(cat="doorbells", id="nest", brand="Google Nest", model="Doorbell (battery)", rec="brief", power=["battery","wired"], ha=0,
 price=179.99, price_note="Google Store UK", price_src="nest_prod", buy="amz_nest",
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
dict(cat="doorbells", id="eufy-e340", brand="eufy", model="Video Doorbell E340", rec="yes", power=["battery","wired"], ha=1,
 price=169.99, price_note="eufy UK", price_src="eufy_prod", buy="amz_e340",
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
dict(cat="doorbells", id="eufy-c31", brand="eufy", model="Video Doorbell C31", rec="yes", power=["battery","wired"], ha=1,
 price=89.99, price_note="eufy UK", price_src="eufy_c31", buy="amz_c31",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=3.99, sub_name="eufy Cloud Backup Basic",
 best="A cheap eufy with 24/7 recording, if you can hardwire it",
 catch="24/7 recording and pre-roll only work hardwired (16-24V, 30VA) with your existing chime bypassed; the microSD card is sold separately.",
 storage="microSD up to 128 GB (not included); optional HomeBase S380", live="Yes", alerts="Yes",
 ai="Free: human and motion detection",
 history="Yes, event clips on the card; 24/7 continuous recording only when hardwired", paywalled="Nothing essential; cloud backup is optional",
 sub_text="Optional Cloud Backup £3.99/month or £39.99/year (1 device); £12.99/month for all devices",
 ha_text="Community integration only (ha-eufy-sdk), which still logs in through your eufy account.",
 wifi="Not stated on eufy's UK product page",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["eufy_c31","eufy_cloud","ha_eufy","sandisk_card"],
 rec_src="eufy_c31", history_src="eufy_c31", ha_src="ha_eufy", plan_src="eufy_cloud", unverified=""),
dict(cat="doorbells", id="reo-wifi", brand="Reolink", model="Video Doorbell WiFi", rec="yes", power=["wired"], ha=2,
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
dict(cat="doorbells", id="reo-poe", brand="Reolink", model="Video Doorbell PoE", rec="yes", power=["poe"], ha=2,
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
dict(cat="doorbells", id="reo-batt", brand="Reolink", model="Video Doorbell (Battery)", rec="yes", power=["battery","wired"], ha=1,
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
dict(cat="doorbells", id="tapo-d230", brand="TP-Link Tapo", model="D230S1", rec="yes", power=["battery"], ha=1,
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
dict(cat="doorbells", id="tapo-td21", brand="TP-Link Tapo", model="TD21", rec="yes", power=["battery"], ha=0,
 price=44.99, price_note="Tapo UK, currently sold out (RRP £56.00)", price_src="tapo_td21", buy="amz_td21",
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
dict(cat="doorbells", id="arlo", brand="Arlo", model="Essential Video Doorbell 2K (2nd gen)", rec="kit", power=["battery"], ha=0,
 power_note="Can be wired to an existing chime for trickle charging, but still runs on its battery.",
 price=84.99, price_note="Argos half price, doorbell + chime bundle (was £169.99)", price_src="argos_arlo",
 extra=round(109.99 + STICK, 2), extra_note="+ Arlo SmartHub £109.99 + SanDisk 64 GB USB stick",
 extra_src="sandisk_stick", kit_src="arlo_hub", kit_label="SmartHub", kit_price=109.99, free_records=True,
 sub=7.99, sub_name="Arlo Secure (1 camera)",
 best="People who already own Arlo cameras",
 catch="Recording needs a £7.99/month plan or a separate hub costing about £110.",
 storage="Only through an Arlo SmartHub (VMB4540, USB) or a Base Station", live="Yes", alerts="Yes",
 ai="Paid", history="None without a hub",
 paywalled="Cloud recording (7, 14 or 30 days depending on plan), object detection, activity zones, theft replacement",
 sub_text="Arlo Secure £7.99/month (1 camera, 7 days), Multi-Camera £12.99, Secure Plus £19.99 (14 days), Secure Pro £24.99",
 ha_text="No official integration; only a community add-on that goes through Arlo's cloud.",
 wifi="2.4 GHz only",
 score=dict(rec=1,live=1,alerts=1,ai=0,storage=0,ha=0),
 src=["argos_arlo","arlo_blog","arlo_plans","arlo_faq","arlo_doorbell","arlo_hubcompat","arlo_hub","tr_arlo","ambient_arlo","ha_arlo","sandisk_stick"],
 rec_src="arlo_blog", history_src="arlo_doorbell", ha_src="ha_arlo", plan_src="arlo_plans", unverified=""),
dict(cat="doorbells", id="aqara-g4", brand="Aqara", model="Video Doorbell G4", rec="yes", power=["battery","wired"], ha=1,
 price=69.00, price_note="EasyGates, UK retailer (RRP £119)", price_src="aqara_uk", buy="amz_aqara",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed (iCloud+ only for HomeKit Secure Video)",
 best="Free face recognition, Android or iPhone",
 catch="Runs on AA batteries unless wired, and setting it up in Home Assistant is fiddly.",
 storage="microSD (up to 512 GB) in the indoor chime", live="Yes", alerts="Yes",
 ai="Free: face recognition on the device", history="Yes, on the chime's card (24/7 only when wired)",
 paywalled="Nothing essential. HomeKit Secure Video needs Apple's paid iCloud+",
 sub_text="None needed",
 ha_text="Reported to work locally through Home Assistant's HomeKit Device integration; two-way audio isn't available there.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["aqara_uk","aqara_eu","aqara_specs","ha_homekit","sandisk_card"],
 rec_src="aqara_specs", history_src="aqara_specs", ha_src="ha_homekit", plan_src="aqara_specs", unverified=""),
dict(cat="doorbells", id="blink", brand="Blink", model="Battery Doorbell 2K+", rec="kit", power=["battery"], ha=0,
 price=59.99, price_note="UK RRP without Sync Module, from Blink's launch pricing; no UK shop besides Amazon found, so the table says Check price", price_src="tr_blink", buy="amz_blink", price_check=True,
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
 src=["tr_blink","camel_sm2","blink_plans","blink_sm2","ha_blink","sandisk_stick"],
 rec_src="blink_sm2", history_src="blink_sm2", ha_src="ha_blink", plan_src="blink_plans", unverified=""),
dict(cat="doorbells", id="ezviz-ep3x", brand="EZVIZ", model="EP3x Pro", rec="yes", power=["battery"], ha=0,
 price=99.99, price_note="Chester Digital Supplies, UK retailer", price_src="chester_ep3x", buy="amz_ep3x",
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
 src=["chester_ep3x","ezviz_ep3x","ezviz_blog","er_tapo","ezviz_cloud","ezviz_terms","ha_ezviz"],
 rec_src="ezviz_ep3x", history_src="ezviz_blog", ha_src="ha_ezviz", plan_src="ezviz_cloud", plan_price_region="EU", unverified="CloudPlay's UK price is app-only, so the £4.99 in the plan column is the published EU price, not a UK quote."),
dict(cat="doorbells", id="ezviz-db2", brand="EZVIZ", model="DB2 Pro Kit", rec="yes", power=["battery"], ha=0,
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
dict(cat="doorbells", id="hik", brand="Hikvision", model="DS-KB6003-WIP", rec="yes", power=["wired"], ha=1,
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

# ---------- cameras ----------
# The same shape as the doorbells, with `cat` choosing the record that renders
# the row. A camera's no-plan sum buys a card where the camera has no storage of
# its own; the Blink's sum buys the kit it needs before it records at all.
dict(cat="cameras", id="reo-rlc820a", brand="Reolink", model="RLC-820A", rec="yes", power=["poe"], ha=2,
 price=67.99, price_note="Reolink UK store sale price (RRP £79.99)", price_src="reo_gb_home",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A wired install on a budget: 4K for £68, with nothing held back",
 catch="Needs a PoE switch or injector, an Ethernet run to the camera, and a card.",
 storage="microSD (up to 512 GB), a Reolink NVR, or FTP; card not included", live="Yes", alerts="Yes",
 ai="Free: person, vehicle and animal detection on the device",
 history="Yes, motion-triggered, scheduled or 24/7 recording", paywalled="Nothing. Reolink Cloud is optional",
 sub_text="None needed. Reolink records to a microSD card or NVR; Reolink Cloud is optional",
 ha_text="Official, fully local integration; the camera works with no internet connection.",
 wifi="Wired Ethernet",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=2),
 src=["reo_gb_home","reo_rlc820a","ha_reo","sandisk_card"],
 rec_src="reo_rlc820a", history_src="reo_rlc820a", ha_src="ha_reo", plan_src="reo_rlc820a", unverified=""),
dict(cat="cameras", id="reo-argus4", brand="Reolink", model="Argus 4 Pro", rec="yes", power=["battery"], ha=2,
 power_note="The battery lasts up to three months on its own.",
 price=169.99, price_note="Reolink UK store, 1 camera with a Solar Panel 2", price_src="reo_gb_home",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A wide, dark driveway: 180° from one camera, with no fees",
 catch="The card is extra, and the 180° panorama runs at 15fps rather than 25fps.",
 storage="microSD (up to 512 GB) or a Reolink Home Hub; card not included", live="Yes", alerts="Yes",
 ai="Free: person, vehicle and animal detection on the device",
 history="Yes, motion-triggered clips on a card or Home Hub", paywalled="Nothing. Reolink Cloud is optional",
 sub_text="None needed. Reolink records to a microSD card or Home Hub; Reolink Cloud is optional",
 ha_text="Official, fully local integration. Battery cameras wake on a PIR event, so some entities update on a schedule.",
 wifi="Dual-band 2.4/5 GHz (Wi-Fi 6)",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=2),
 src=["reo_gb_home","reo_argus","ha_reo","sandisk_card"],
 rec_src="reo_argus", history_src="reo_argus", ha_src="ha_reo", plan_src="reo_argus", unverified=""),
dict(cat="cameras", id="reo-e1out", brand="Reolink", model="E1 Outdoor Pro", rec="yes", power=["wired"], ha=2,
 price=129.99, price_note="Reolink UK store", price_src="reo_gb_home",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A wide garden: 355° pan, 3× optical zoom and no fees",
 catch="Mains power at the camera, it is only IP65, and the card is extra.",
 storage="microSD (up to 512 GB), a Reolink NVR, a Home Hub, or FTP/NAS; card not included",
 live="Yes", alerts="Yes", ai="Free: person, vehicle and animal detection on the device",
 history="Yes, motion-triggered, scheduled or 24/7 recording", paywalled="Nothing. Reolink Cloud is optional",
 sub_text="None needed. Reolink records to a microSD card, NVR or Home Hub; Reolink Cloud is optional",
 ha_text="Official, fully local integration; RTSP, ONVIF and RTMP are exposed for other local apps.",
 wifi="Dual-band 2.4/5 GHz (Wi-Fi 6)",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=2),
 src=["reo_gb_home","reo_e1out","ha_reo","sandisk_card"],
 rec_src="reo_e1out", history_src="reo_e1out", ha_src="ha_reo", plan_src="reo_e1out", unverified=""),
dict(cat="cameras", id="tapo-c660", brand="TP-Link Tapo", model="C660 KIT", rec="yes", power=["battery"], ha=0,
 power_note="It can also charge over USB-C.",
 price=127.99, price_note="Tapo UK sale price (RRP £179.99)", price_src="tapo_c660",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=2.99, sub_name="Tapo Care",
 best="A sunny wall with no socket: 4K, solar and a card slot",
 catch="Not on Home Assistant's supported Tapo camera list, and the card is extra.",
 storage="microSD (up to 512 GB) on the camera; card not included", live="Yes", alerts="Yes",
 ai="Free: person, pet and vehicle detection on the device",
 history="Yes, event clips on the card; 24/7 recording with a card",
 paywalled="30-day cloud history, rich notifications, Smart Sort",
 sub_text="Optional Tapo Care £2.99/month or £29.49/year (1 camera)",
 ha_text="Home Assistant's local TP-Link integration lists the C520WS and other Tapo cameras, but not this C660 KIT. Treat live view as unsupported.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["tapo_c660","tapo_care","ha_tplink","sandisk_card"],
 rec_src="tapo_c660", history_src="tapo_c660", ha_src="ha_tplink", plan_src="tapo_care",
 unverified="Home Assistant support for this exact model is not listed on the integration's supported-device page."),
dict(cat="cameras", id="eufy-s340", brand="eufy", model="SoloCam S340", rec="yes", power=["battery"], ha=1,
 power_note="The battery lasts up to three months without sun.",
 price=179.00, price_note="eufy UK list price; a £50 coupon was advertised", price_src="eufy_s340",
 extra=0, extra_note="8 GB storage built in", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A garden corner with sun: 360° pan and 8 GB on board",
 catch="8 GB is all you get without a HomeBase, and Home Assistant needs a community add-on.",
 storage="8 GB built in, non-removable; a HomeBase S380 adds up to 16 TB",
 live="Yes", alerts="Yes", ai="Free: human and vehicle detection on the device",
 history="Yes, event clips on the built-in 8 GB", paywalled="Nothing essential; cloud backup is optional",
 sub_text="None needed. eufy records to its built-in storage; cloud backup is optional",
 ha_text="No official camera integration. The community eufy-security add-on logs in through your eufy account.",
 wifi="Wi-Fi (the band is not stated on the UK page)",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=1),
 src=["eufy_s340","ha_eufy_cam"],
 rec_src="eufy_s340", history_src="eufy_s340", ha_src="ha_eufy_cam", plan_src="eufy_s340", unverified=""),
dict(cat="cameras", id="eufy-e30", brand="eufy", model="Indoor Cam E30", rec="yes", power=["wired"], ha=1,
 price=69.99, price_note="eufy UK list price; a £14 coupon was advertised", price_src="eufy_e30",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A room, a pet or a nanny cam: 4K and on-device AI",
 catch="The card is extra, and the camera only joins 2.4 GHz Wi-Fi.",
 storage="microSD (sold separately) or a HomeBase S380", live="Yes", alerts="Yes",
 ai="Free: person, pet, audio and crying detection on the device",
 history="Yes, motion-triggered clips on a card or HomeBase",
 paywalled="Nothing essential; cloud backup is optional",
 sub_text="None needed. eufy records to a card; cloud backup is optional",
 ha_text="No official camera integration. The community eufy-security add-on logs in through your eufy account.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["eufy_e30","ha_eufy_cam","sandisk_card"],
 rec_src="eufy_e30", history_src="eufy_e30", ha_src="ha_eufy_cam", plan_src="eufy_e30", unverified=""),
dict(cat="cameras", id="aqara-g3", brand="Aqara", model="Camera Hub G3", rec="yes", power=["wired"], ha=1,
 price=79.99, price_note="Aqara UK Shop sale price (RRP £119.99)", price_src="aqara_g3",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A hallway that also needs a Zigbee hub",
 catch="The card is extra, and HomeKit Secure Video records at 1080p.",
 storage="microSD (up to 128 GB); HomeKit Secure Video needs iCloud+", live="Yes", alerts="Yes",
 ai="Free: on-device face, gesture, person and pet recognition",
 history="Yes, on the card; HomeKit Secure Video keeps 10 days in iCloud+",
 paywalled="Nothing essential. HomeKit Secure Video needs Apple's iCloud+",
 sub_text="None needed. The camera records to a card; HomeKit Secure Video is optional",
 ha_text="Works locally through Home Assistant's HomeKit Device integration; pair it as a HomeKit accessory.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["aqara_g3","ha_homekit","sandisk_card"],
 rec_src="aqara_g3", history_src="aqara_g3", ha_src="ha_homekit", plan_src="aqara_g3", unverified=""),
dict(cat="cameras", id="aqara-e1", brand="Aqara", model="Camera E1", rec="yes", power=["wired"], ha=1,
 price=48.98, price_note="Aqara UK Shop sale price (RRP £69.98)", price_src="aqara_e1",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="The cheapest way to keep footage without a plan",
 catch="The card and the power supply are both extra.",
 storage="microSD (up to 512 GB), or SMB 3.0 NAS with a card inserted", live="Yes", alerts="Yes",
 ai="Free: on-device person detection and tracking",
 history="Yes, on a card; 24 hours of events are free in Aqara's cloud",
 paywalled="Nothing essential. 30-day cloud history is a paid option",
 sub_text="None needed. 24 hours of event cloud is included; a paid membership is optional",
 ha_text="Works locally through Home Assistant's HomeKit Device integration; pair it as a HomeKit accessory.",
 wifi="Wi-Fi 6, dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["aqara_e1","ha_homekit","sandisk_card"],
 rec_src="aqara_e1", history_src="aqara_e1", ha_src="ha_homekit", plan_src="aqara_e1", unverified=""),
dict(cat="cameras", id="ring-outpro", brand="Ring", model="Outdoor Camera Pro (plug-in)", rec="no", power=["wired"], ha=0,
 price=179.99, price_note="Ring UK", price_src="ring_outpro",
 extra=0, extra_note="", free_records=False,
 sub=4.99, sub_name="Ring Solo",
 best="People already paying for Ring and Alexa",
 catch="Saves no video at all without the £4.99-a-month plan.",
 storage="None. Recording is cloud-only.", live="Yes", alerts="Yes",
 ai="Paid (person, package and vehicle alerts on Ring's plans)",
 history="None", paywalled="All recording and playback (up to 180 days), smart alerts, 24/7 recording",
 sub_text="Ring Solo £4.99/month or £49.99/year (1 device). Multi £7.99, Pro £15.99",
 ha_text="Official integration, but it goes through Ring's cloud. No local-only option.",
 wifi="2.4 GHz only",
 score=dict(rec=0,live=1,alerts=1,ai=0,storage=0,ha=0),
 src=["ring_outpro","ring_plans","ha_ring"],
 rec_src="ring_outpro", history_src="ring_outpro", ha_src="ha_ring", plan_src="ring_plans", unverified=""),
dict(cat="cameras", id="blink-out4", brand="Blink", model="Outdoor 4", rec="kit", power=["battery"], ha=0,
 price=69.99, price_note="Amazon UK, includes a Sync Module Core (which has no local storage)", price_src="amz_blink_cam",
 extra=round(39.99 + STICK, 2), extra_note="+ Sync Module 2 £39.99 + SanDisk 64 GB USB stick",
 extra_src="sandisk_stick", kit_src="amz_sm2", kit_label="Sync Module 2", kit_price=39.99, free_records=True,
 sub=2.50, sub_name="Blink Basic",
 best="The cheapest way into Amazon's cameras, if you catch a deal",
 catch="Records nothing until you add a Sync Module 2 and a USB stick, and live view stops at 5 minutes.",
 storage="Only through a Sync Module 2 + USB stick (1–256 GB); the camera has no storage",
 live="Capped at 5 minutes", alerts="Yes", ai="Paid (person and vehicle detection)",
 history="None without a Sync Module 2",
 paywalled="Cloud clips, person/vehicle detection, 90-minute live view, AI descriptions",
 sub_text="Blink Basic £2.50/month (£24.99/year); Plus £8/month; Basic AI £5.49/month",
 ha_text="Official integration, but it goes through Blink's cloud and has no live view.",
 wifi="2.4 GHz only",
 score=dict(rec=1,live=0,alerts=1,ai=0,storage=0,ha=0),
 src=["amz_blink_cam","amz_sm2","blink_storage","blink_plans","blink_sm2","ha_blink","sandisk_stick"],
 rec_src="blink_storage", history_src="blink_storage", ha_src="ha_blink", plan_src="blink_plans", unverified=""),

# ---------- smart rings ----------
# A ring has no recording and no recorder, so its sums are the price and, where
# the vendor charges one, the membership. `free_records` is the same decision
# as before: does the product give its data with no plan? `power` buckets the
# vendor's battery figure, and `wifi` carries the phones it works with.
dict(cat="rings", id="oura-4", brand="Oura", model="Ring 4", rec="brief", power=["eight"], ha=1,
 price=244.00, price_note="Amazon UK, Silver, size 9; other sizes and finishes differ", price_src="amz_oura4",
 extra=0, extra_note="", free_records=False,
 sub=5.99, sub_name="Oura Membership",
 best="The most detailed sleep and recovery data, if you will pay monthly",
 catch="Without the £5.99 monthly membership, only three daily scores work.",
 storage="Oura's cloud. Oura lets you download your data from the Membership Hub even without a plan.",
 live="No. 24/7 heart rate is part of the membership.",
 alerts="No. Wellness alerts are part of the membership.",
 ai="No. Only the three daily scores are free. Sleep stages, HRV, SpO2 and temperature need the membership.",
 history="Three daily scores only. Sleep stages, HRV, SpO2 and trends need the membership.",
 paywalled="Detailed sleep stages, 24/7 heart rate and HRV, SpO2, temperature, stress, cardiovascular age, VO2 max, women's health, reports and the API",
 sub_text="Oura Membership £5.99/month or £69.99/year after tax. The first month is free",
 ha_text="A community HACS integration brings the ring's data into Home Assistant through Oura's cloud API. Oura blocks API access without an active membership, so the integration needs the plan too.",
 wifi="iPhone and Android",
 score=dict(rec=1,sleep=0,hr=0,spo2=0,extra=0,ha=1),
 src=["amz_oura4","oura_membership","oura_free","ha_oura"],
 rec_src="oura_free", history_src="oura_free", ha_src="ha_oura", plan_src="oura_membership",
 nosub_say="£244 buys the ring. Without the membership only three daily scores work.", unverified=""),
dict(cat="rings", id="ultra-air", brand="Ultrahuman", model="Ring AIR", rec="yes", power=["six"], ha=1,
 price=329.00, price_note="Amazon UK", price_src="amz_ultra",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="Home Assistant tinkerers: the data is free, and a HACS integration pulls it in",
 catch="No SpO2 reading, and the Home Assistant route is a community cloud integration.",
 storage="Ultrahuman's cloud. The app holds the history and shows it on the phone.",
 live="Yes, in the app.",
 alerts="Yes, recovery and movement nudges.",
 ai="Free: sleep stages, HRV, skin temperature, stress, recovery and cycle insights.",
 history="Yes, full history in the app.",
 paywalled="Nothing needed. No subscription. Ultrahuman Max adds replacements and plug-ins but is not required",
 sub_text="No subscription. The ring's data is free in the app. Ultrahuman Max is an optional extra", plan_say="No subscription. The ring's data is free in the app. Ultrahuman Max is an optional extra.",
 ha_text="A community HACS integration reads the ring through Ultrahuman's cloud API. It is not local, and it needs your account.",
 wifi="iPhone and Android",
 score=dict(rec=2,sleep=1,hr=1,spo2=0,extra=1,ha=1),
 src=["amz_ultra","uh_ring","uh_nosub","ha_ultra"],
 rec_src="uh_nosub", history_src="uh_ring", ha_src="ha_ultra", plan_src="uh_nosub",
 nosub_say="No subscription. The ring and its data are the whole cost.",
 unverified="Ultrahuman's UK page does not publish minimum iOS or Android versions; check the app store listing."),
dict(cat="rings", id="rc-2", brand="RingConn", model="Gen 2", rec="yes", power=["twelve"], ha=0,
 price=259.00, price_note="Amazon UK", price_src="amz_rc2",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="The cheaper RingConn, with the same free core data",
 catch="No vibration alerts, no Home Assistant, and Gen 3 adds more sleep and vascular detail.",
 storage="RingConn's cloud. The app holds the history and shows it on the phone.",
 live="Yes, in the app.",
 alerts="App reminders only.",
 ai="Free: sleep stages, HRV, SpO2, skin temperature, stress and sleep-apnea insights.",
 history="Yes, full history in the app.",
 paywalled="Nothing needed. No app subscription for the core data",
 sub_text="No subscription. RingConn says the ring's core features need no plan", plan_say="No subscription. RingConn says the ring's core features need no plan.",
 ha_text="No official or community Home Assistant integration is documented. The ring's data stays in RingConn's app.",
 wifi="iPhone and Android",
 score=dict(rec=2,sleep=1,hr=1,spo2=1,extra=1,ha=0),
 src=["amz_rc2","rc2_product","rc_nosub","ha_index"],
 rec_src="rc_nosub", history_src="rc2_product", ha_src="ha_index", plan_src="rc_nosub",
 nosub_say="No subscription. The ring and its data are the whole cost.", unverified=""),
dict(cat="rings", id="rc-2-air", brand="RingConn", model="Gen 2 Air", rec="yes", power=["ten"], ha=0,
 price=179.00, price_note="Amazon UK", price_src="amz_rc2a",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="The cheapest way into a ring that keeps its data free",
 catch="No sleep-apnea insights, no vibration, and no Home Assistant.",
 storage="RingConn's cloud. The app holds the history and shows it on the phone.",
 live="Yes, in the app.",
 alerts="App reminders only.",
 ai="Free: sleep stages, HRV, SpO2, skin temperature and stress.",
 history="Yes, full history in the app.",
 paywalled="Nothing needed. No app subscription for the core data",
 sub_text="No subscription. RingConn says the ring's core features need no plan", plan_say="No subscription. RingConn says the ring's core features need no plan.",
 ha_text="No official or community Home Assistant integration is documented. The ring's data stays in RingConn's app.",
 wifi="iPhone and Android",
 score=dict(rec=2,sleep=1,hr=1,spo2=1,extra=0,ha=0),
 src=["amz_rc2a","rc2a_product","rc_nosub","ha_index"],
 rec_src="rc_nosub", history_src="rc2a_product", ha_src="ha_index", plan_src="rc_nosub",
 nosub_say="No subscription. The ring and its data are the whole cost.", unverified=""),
dict(cat="rings", id="rc-3", brand="RingConn", model="Gen 3", rec="yes", power=["fourteen"], ha=0,
 price=309.00, price_note="Amazon UK", price_src="amz_rc3",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="The best all-round ring: 14 days, no subscription and the deepest sleep data",
 catch="No Home Assistant integration, and it costs £50 more than the Gen 2.",
 storage="RingConn's cloud. The app holds the history and shows it on the phone.",
 live="Yes, in the app.",
 alerts="Yes, vibration alerts on the ring.",
 ai="Free: sleep stages, HRV, SpO2, temperature, stress, apnea risk and overnight vascular trends.",
 history="Yes, full history in the app.",
 paywalled="Nothing needed. No app subscription for the core data",
 sub_text="No subscription. RingConn says the ring's core features need no plan", plan_say="No subscription. RingConn says the ring's core features need no plan.",
 ha_text="No official or community Home Assistant integration is documented. The ring's data stays in RingConn's app.",
 wifi="iPhone and Android",
 score=dict(rec=2,sleep=1,hr=1,spo2=1,extra=1,ha=0),
 src=["amz_rc3","rc3_product","rc_nosub","ha_index"],
 rec_src="rc_nosub", history_src="rc3_product", ha_src="ha_index", plan_src="rc_nosub",
 nosub_say="No subscription. The ring and its data are the whole cost.", unverified=""),
dict(cat="rings", id="samsung-ring", brand="Samsung", model="Galaxy Ring", rec="yes", power=["seven"], ha=0,
 price=233.38, price_note="Amazon UK, size 7 Titanium Black; other sizes and colours list at £399", price_src="amz_samsung",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="Samsung phone owners: no subscription and the deepest Samsung Health integration",
 catch="Android only, with no iPhone support, and no Home Assistant route.",
 storage="Samsung Health's cloud. The phone app holds the history.",
 live="Yes, in Samsung Health.",
 alerts="Yes, through Samsung Health notifications.",
 ai="Free: sleep stages, heart rate, SpO2, skin temperature, stress, Energy Score and cycle tracking.",
 history="Yes, in Samsung Health.",
 paywalled="Nothing needed. Samsung charges no subscription for the ring's data",
 sub_text="No subscription. Samsung Health is free with the ring", plan_say="No subscription. Samsung Health is free with the ring.",
 ha_text="No official or community Home Assistant integration was found. The data stays in Samsung Health.",
 wifi="Android 11+ only; not iPhone",
 score=dict(rec=2,sleep=1,hr=1,spo2=1,extra=1,ha=0),
 src=["amz_samsung","samsung_support","ha_index"],
 rec_src="amz_samsung", history_src="samsung_support", ha_src="ha_index", plan_src="amz_samsung",
 nosub_say="No subscription. The ring and its data are the whole cost.",
 unverified="Samsung's UK product page did not render a price. The £399 list figure is for the other Amazon variants; £233.38 is size 7 in Titanium Black."),
dict(cat="rings", id="amazfit-helio", brand="Amazfit", model="Helio Ring", rec="yes", power=["four"], ha=0,
 price=149.90, price_note="Amazfit UK sale price, RRP £269; size 10 is out of stock", price_src="amazfit_uk",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="The cheapest smart ring, with no subscription for the basics",
 catch="Only three sizes, no published battery figure, and Aura's advanced sleep coaching is a paid extra.",
 storage="Zepp's cloud. The phone app holds the history.",
 live="Yes, in Zepp.",
 alerts="Yes, through Zepp notifications.",
 ai="Free: sleep stages, resting heart rate, HRV, SpO2, temperature, stress and readiness.",
 history="Yes, in Zepp.",
 paywalled="Nothing for the core data. Zepp Aura's advanced sleep reports and unlimited AI assistant are optional paid extras",
 sub_text="No subscription for the ring's data. Zepp Aura is an optional paid extra, priced in dollars on Amazfit's UK page", plan_say="No subscription for the ring's data. Zepp Aura is an optional paid extra.",
 ha_text="No official integration. A community Zepp bridge exists for watches, but it is not confirmed for this ring.",
 wifi="iPhone and Android (minimum versions not stated)",
 score=dict(rec=2,sleep=1,hr=1,spo2=1,extra=1,ha=0),
 src=["amazfit_uk","amazfit_aura","ha_zepp"],
 rec_src="amazfit_uk", history_src="amazfit_uk", ha_src="ha_zepp", plan_src="amazfit_uk",
 nosub_say="No subscription for the ring's data. Zepp Aura is optional.",
 unverified="Amazfit's UK page does not publish a battery-life figure; four days comes from retailer spec sheets, not the manufacturer. Zepp Aura's UK price is not published either."),
]

# A row's Amazon price and buy links carry the tag, so a new Amazon row is
# tagged without anyone remembering to. An Amazon page cited for a sundry
# stays a plain citation.
for _r in ROWS:
    for _key in (_r["price_src"], _r.get("buy")):
        if _key:
            _name, _url = S[_key]
            S[_key] = (_name, amazon_tagged(_url))

# ---------- each row's verdict and its plain words ----------
# Authored beside the rows and attached to them below, so a row carries its own
# verdict and sentences by the time anything reads it.
VERDICT = {
    "reo-poe": "best", "reo-wifi": "wired", "reo-batt": "batt",
    "tapo-d230": "easy", "ring": "avoid", "blink": "avoid", "arlo": "avoid",
    "reo-rlc820a": "best", "reo-argus4": "batt", "reo-e1out": "ptz",
    "tapo-c660": "solar", "aqara-g3": "indoor", "aqara-e1": "value",
    "ring-outpro": "avoid", "blink-out4": "avoid",
    "rc-3": "best", "rc-2-air": "value",
    "ultra-air": "ha", "samsung-ring": "galaxy", "amazfit-helio": "budget",
    "oura-4": "avoid",
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
    "reo-rlc820a": ("Powered by an Ethernet cable (PoE): one cable carries both power and video.",
                    "A microSD card in the camera (up to 512 GB), a Reolink NVR, or an FTP server."),
    "reo-argus4": ("Runs on its rechargeable battery, or on the solar panel in the box.",
                   "A microSD card in the camera (up to 512 GB), or a Reolink Home Hub indoors."),
    "reo-e1out": ("Mains power from the 12V adapter; there is no battery.",
                  "A microSD card (up to 512 GB), a Reolink NVR, a Home Hub, or FTP/NAS."),
    "tapo-c660": ("Runs on its rechargeable battery and the solar panel in the box.",
                  "A microSD card (up to 512 GB) in the camera."),
    "eufy-s340": ("Runs on its built-in battery and the solar panel in the box.",
                  "8 GB is built into the camera. A HomeBase S380 adds up to 16 TB."),
    "eufy-e30": ("Plugged into the mains.",
                 "A microSD card (sold separately), or a HomeBase S380."),
    "aqara-g3": ("Plugged into the mains over USB-C; the power supply is not included.",
                 "A microSD card (up to 128 GB), or Apple's iCloud+ through HomeKit Secure Video."),
    "aqara-e1": ("Plugged into the mains over USB-C; the 2A power supply is not included.",
                 "A microSD card (up to 512 GB), or an SMB 3.0 NAS with a card inserted."),
    "ring-outpro": ("Plugged into a standard socket.",
                    "None. The camera has no storage of its own."),
    "blink-out4": ("Runs on two AA lithium batteries.",
                   "Recording needs a Sync Module 2 and a USB stick (1–256 GB)."),
    "oura-4": ("A rechargeable ring battery that Oura says lasts five to eight days.",
               "Oura's cloud holds the history, and Oura lets you download your data even without a membership."),
    "ultra-air": ("A rechargeable ring battery that Ultrahuman says lasts four to six days in Turbo mode.",
                  "Ultrahuman's cloud holds the history, and the app shows it on the phone."),
    "rc-2": ("A rechargeable ring battery that RingConn says lasts up to 12 days.",
             "RingConn's cloud holds the history, and the app shows it on the phone."),
    "rc-2-air": ("A rechargeable ring battery that RingConn says lasts up to 10 days.",
                 "RingConn's cloud holds the history, and the app shows it on the phone."),
    "rc-3": ("A rechargeable ring battery that RingConn says lasts up to 14 days with vibration off.",
             "RingConn's cloud holds the history, and the app shows it on the phone."),
    "samsung-ring": ("A rechargeable ring battery that Samsung says lasts up to 7 days on the largest sizes.",
                     "Samsung Health's cloud holds the history, and the phone app shows it."),
    "amazfit-helio": ("A rechargeable ring battery that Amazfit's UK page does not put a figure on. Retailer spec sheets say about four days.",
                      "Zepp's cloud holds the history, and the phone app shows it."),
}

# ---------- row shape ----------
# The unknown-key test is what catches a misspelling, which would otherwise read
# as a valid optional field and quietly skip a sentence or print nothing. The
# build runs this before it writes anything, and the audit runs it over the
# files that shipped.
REQUIRED_ROW_KEYS = (
    "cat", "id", "brand", "model", "rec", "ha", "price", "price_note",
    "price_src", "extra", "extra_note", "free_records", "sub", "sub_name",
    "best", "catch", "sub_text", "ha_text", "score", "src", "unverified",
    "rec_src", "history_src", "ha_src", "plan_src",
)
OPTIONAL_ROW_KEYS = (
    "power_note", "cards", "plan_price_region", "extra_src", "kit_src", "kit_label",
    "kit_price", "nosub_say", "plan_say",
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
    rows = cat.get("rows")
    if rows is None:
        rows = [r for r in ROWS if r.get("cat") == cat["slug"]]
    sources = S
    rec_label = {key: label for key, label, _ in cat["rec"]}
    power_label = dict(cat["powers"])
    part_max = {key: maximum for key, _, maximum in cat["score_parts"]}
    required = tuple(dict.fromkeys(REQUIRED_ROW_KEYS + tuple(cat["required_keys"])))
    allowed = required + OPTIONAL_ROW_KEYS + DERIVED_ROW_KEYS
    problems = []
    if not rows:
        problems.append(f"{cat['slug']}: no rows are attached to the record")
    for r in rows:
        rid = r.get("id", "(no id)")
        missing = [k for k in required if k not in r]
        unknown = [k for k in r if k not in allowed]
        if missing: problems.append(f"{rid}: missing {', '.join(missing)}")
        if unknown: problems.append(f"{rid}: unknown {', '.join(unknown)}")
        if r.get("cat") != cat["slug"]:
            problems.append(f"{rid}: cat {r.get('cat')!r} is not {cat['slug']!r}")
        for key in ("price_src", "rec_src", "history_src", "ha_src", "plan_src", "extra_src", "kit_src"):
            if key in r and r[key] not in sources:
                problems.append(f"{rid}: {key} {r[key]!r} is not in the source register")
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
        if r.get("rec") not in rec_label:
            problems.append(
                f"{rid}: rec {r.get('rec')!r} is not one of {', '.join(rec_label)}"
            )
        for value in r.get("power") or ():
            if value not in power_label:
                problems.append(
                    f"{rid}: power {value!r} is not one of {', '.join(power_label)}"
                )
        if not isinstance(r.get("ha"), int) or isinstance(r.get("ha"), bool) or not 0 <= r["ha"] <= 2:
            problems.append(f"{rid}: ha {r.get('ha')!r} is not a whole number from 0 to 2")
        parts = r.get("score") or {}
        for key, value in parts.items():
            if key not in part_max:
                problems.append(
                    f"{rid}: score {key!r} is not one of {', '.join(part_max)}"
                )
            elif not isinstance(value, int) or not 0 <= value <= part_max[key]:
                problems.append(
                    f"{rid}: score {key} is {value!r}, outside 0 to {part_max[key]}"
                )
        missing_parts = [key for key in part_max if key not in parts]
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
    headlines = [r["id"] for r in rows if r.get("verdict") == cat["headline"]]
    if not headlines:
        problems.append(f"no row carries the headline verdict {cat['headline']!r}")
    return problems


def authored_problems():
    """Every hand-authored verdict and plain sentence names a row that exists."""
    problems = []
    ids = {r["id"] for r in ROWS}
    for rid in VERDICT:
        if rid not in ids:
            problems.append(f"VERDICT has an entry for a row that does not exist: {rid}")
    for rid in PLAIN:
        if rid not in ids:
            problems.append(f"PLAIN has an entry for a row that does not exist: {rid}")
    return problems


# ---------- derived figures ----------
def money(x, decimals=2):
    """£ figure. decimals=None keeps whole pounds whole and shows pence otherwise."""
    if x is None: return "—"
    if decimals is None: decimals = 0 if float(x).is_integer() else 2
    return f"£{x:,.{decimals}f}"

def _derive(cat):
    """One category's rows, vocabulary, source numbering and slider ends."""
    rows = [r for r in ROWS if r.get("cat") == cat["slug"]]
    cat["rows"] = rows
    cat["sources"] = S
    cat["labels"] = labels(cat)
    cat["rec_label"] = {key: label for key, label, _ in cat["rec"]}
    cat["rec_rank"] = {key: rank for key, _, rank in cat["rec"]}
    cat["power_label"] = dict(cat["powers"])
    cat["score_parts"] = list(cat["score_parts"])
    cat["score_max"] = sum(maximum for _, _, maximum in cat["score_parts"])
    cat["part_max"] = {key: maximum for key, _, maximum in cat["score_parts"]}
    for r in rows:
        r["cards"] = r.get("cards", 1)
        r["plan_region"] = r.get("plan_price_region", "UK")
        # A second card is a second purchase: the base extra has one already.
        if r["cards"] > 1: r["extra"] = round(r["extra"] + CARD * (r["cards"] - 1), 2)
        r["score_total"] = sum(r["score"].values())
        r["verdict"] = VERDICT.get(r["id"])
        r["plain"] = PLAIN.get(r["id"])
        r["nosub3"] = round(r["price"] + r["extra"], 2)
        months = cat["months"]
        r["sub3"] = round(r["price"] + months * r["sub"], 2) if r["sub"] is not None else None
        # cheapest way to keep recordings for the category's period
        opts = []
        if r["free_records"]: opts.append(r["nosub3"])
        if r["sub3"] is not None: opts.append(r["sub3"])
        # A row with neither route has no total to print. `row_problems()`
        # rejects it by name before anything is written; `None` here keeps the
        # module importable so that the guard can run at all.
        r["keep3"] = min(opts) if opts else None
        # Which of the two figures the sort uses, and what to call it. The page
        # says so in words and bolds that cell, so the order never looks broken.
        if r["keep3"] is None:
            r["keep_basis"], r["keep_note"] = "none", "no way to keep recordings"
        elif r["free_records"] and (r["sub3"] is None or r["nosub3"] <= r["sub3"]):
            r["keep_basis"], r["keep_note"] = "nosub", cat["labels"]["keep_free"]
        else:
            r["keep_basis"], r["keep_note"] = "sub", f"with the {r['sub_name']} plan"
        m_free = f"{money(r['price'])}" + (f" + {money(r['extra'])} ({r['extra_note'].lstrip('+ ')})" if r["extra"] else "") + f" = {money(r['nosub3'])}"
        if not r["free_records"]:
            m_free += cat["labels"]["maths_no_route"] if r["rec"] == "no" else cat["labels"]["maths_brief"]
        m_sub = (
            f"{money(r['price'])} + {months} × {money(r['sub'])} ({r['sub_name']}) = {money(r['sub3'])}"
            if r["sub3"] is not None
            else cat.get("no_plan_note", "No subscription offered or needed")
        )
        r["maths_free"], r["maths_sub"] = m_free, m_sub
    # The slider's ends are the data's own: a row priced below a typed-in floor
    # would disappear from the default view of the page it was added to, and a
    # ceiling off the handle's 5-step grid would snap the dearest row out of
    # range just as quietly.
    prices = [r["price"] for r in rows]
    cat["minp"] = int(min(prices) // 10 * 10) if prices else 0
    cat["maxp"] = int(ceil(max(prices) / 5) * 5) if prices else 0
    # footnote numbering, per category: a reader on the cameras page sees its
    # own register start at 1, not the doorbells' numbering with gaps in it.
    cat["order"] = []
    for r in rows:
        for key in r["src"]:
            if key not in cat["order"]:
                cat["order"].append(key)
    cat["fn"] = {key: i + 1 for i, key in enumerate(cat["order"])}


for _category in CATEGORIES:
    _derive(_category)


class Dataset:
    """One category's data, as its page and its checks read it."""

    def __init__(self, cat):
        self.cat = cat
        self.ROWS = cat["rows"]
        self.S = S
        self.FN = cat["fn"]
        self.CARD = CARD
        self.STICK = STICK
        self.CHECKED = cat["checked"]
        self.CHECKED_ISO = cat["checked_iso"]
        self.REC_LABEL = cat["rec_label"]
        self.REC_RANK = cat["rec_rank"]
        self.POWER_LABEL = cat["power_label"]
        self.SCORE_PARTS = cat["score_parts"]
        self.SCORE_MAX = cat["score_max"]
        self.MONTHS = cat["months"]
        self.money = money


DATASETS = {cat["slug"]: Dataset(cat) for cat in CATEGORIES}
