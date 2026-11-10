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
from urllib.parse import quote, urlparse

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
 "ring_4kpro": ("Ring UK: Battery Video Doorbell 4K Pro", "https://en-uk.ring.com/products/battery-doorbell-pro-2nd-gen"),
 "ring_wpro": ("Ring UK: Wired Video Doorbell 4K Pro", "https://en-uk.ring.com/products/wired-video-doorbell-pro-3-gen"),
 "ring_elite": ("Ring UK: Wired Video Doorbell 4K Elite", "https://en-uk.ring.com/products/wired-doorbell-elite-2nd-gen"),
 "ring_wpro_spec": ("Ring support: Wired Doorbell 4K Pro compliance", "https://ring.com/gb/en/support/articles/j5174/safety-compliance-wired-doorbell-pro-3rd-gen"),
 "indy_ring": ("The Independent, Feb 2026", "https://www.independent.co.uk/home-improvement/ring-video-doorbell-subscription-without-b2915224.html"),
 "ha_ring": ("Home Assistant: Ring", "https://www.home-assistant.io/integrations/ring/"),
 "nest_prod": ("Google Store UK: Nest Doorbell", "https://store.google.com/gb/product/nest_doorbell_battery?hl=en-GB"),
 "nest_prem": ("Google Home Premium UK", "https://store.google.com/gb/product/google_home_premium?hl=en-GB"),
 "ha_nest": ("Home Assistant: Nest", "https://www.home-assistant.io/integrations/nest/"),
 "nest_plans": ("Google Home Premium: what you get", "https://support.google.com/googlehome/answer/9233159?hl=en-GB"),
 "eufy_prod": ("eufy UK: E340", "https://www.eufy.com/uk/products/T8214311"),
 "eufy_c31": ("eufy UK: C31", "https://www.eufy.com/uk/products/t8223311"),
 "eufy_s4": ("Anker UK: eufy Video Doorbell S4", "https://www.anker.com/uk/products/e82153f1"),
 "eufy_cloud": ("eufy UK cloud plans", "https://www.eufy.com/uk/cloud-storage"),
 "eufy_cloud_uk": ("Anker UK: eufy cloud plan prices", "https://www.anker.com/uk/blogs/security-camera/cloud-security-cameras"),
 "verge_eufy": ("The Verge, Nov 2022", "https://www.theverge.com/2022/11/30/23486753/anker-eufy-security-camera-cloud-private-encryption-authentication-storage"),
 "sha_nosub": ("smarthomeassistant.co.uk guide", "https://smarthomeassistant.co.uk/articles/smart-security/best-video-doorbell-no-subscription-uk"),
 "reo_store": ("Reolink UK store", "https://store.reolink.com/gb/video-doorbells/"),
 "reo_batt": ("Reolink UK battery doorbells", "https://store.reolink.com/gb/wireless-doorbell-camera/"),
 "machinemart_reo": ("Machine Mart: Reolink Battery", "https://www.machinemart.co.uk/p/reolink-2k-wifi-ai-battery-video-doorbell--64g"),
 "reo_cloud": ("Reolink Cloud UK plans", "https://cloud.reolink.com/cloud-plan"),
 "reo_faq": ("Reolink doorbell FAQ", "https://support.reolink.com/articles/29213749981209-Reolink-Video-Doorbell-Cameras-FAQ/"),
 "reo_hub": ("Reolink UK Home Hub", "https://store.reolink.com/gb/home-hub-series/"),
 "ha_reo": ("Home Assistant: Reolink", "https://www.home-assistant.io/integrations/reolink/"),
 "tapo_d235": ("Tapo UK: D235", "https://uk.store.tapo.com/products/video-doorbell-wired-and-battery-tapo-d235"),
 "tapo_d260": ("Tapo UK: Doorbell Pro (D260)", "https://uk.store.tapo.com/products/tapo-doorbell-pro-tapo-d260-4k-video-doorbell"),
 "tapo_td21": ("Tapo UK: TD21", "https://uk.store.tapo.com/products/battery-video-doorbell-2k-3mp-colour-night-vision-tapo-td21"),
 "tapo_care": ("Tapo Care UK", "https://uk.store.tapo.com/pages/tapo-care"),
 "ha_tplink": ("Home Assistant: TP-Link Smart Home", "https://www.home-assistant.io/integrations/tplink/"),
 "tapo_td21_manual": ("Tapo TD21 setup guide", "https://www.tapo.com/en/manuals/1094/"),
 "er_tapo": ("Expert Reviews: EZVIZ EP3x Pro review", "https://www.expertreviews.co.uk/technology/home-security/ezviz-ep3x-pro-video-doorbell-review"),
 "argos_arlo": ("Argos: Arlo doorbell", "https://www.argos.co.uk/product/4379311"),
 "arlo_2k": ("Arlo UK: 2K Wireless Video Doorbell", "https://www.arlo.com/en_gb/doorbells/arlo-2k-wireless-video-doorbell"),
 "arlo_fhd": ("Arlo UK: Essential Wireless Video Doorbell FHD", "https://www.arlo.com/en_gb/doorbells/arlo-fhd-wireless-video-doorbell"),
 "reo_batt2": ("Reolink UK: Battery Video Doorbell (2nd Gen)", "https://reolink.com/gb/product/reolink-video-doorbell-2nd-gen/"),
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
 "aqara_g410": ("Aqara UK Shop: Doorbell Camera Hub G410 Select", "https://www.aqara-shop.co.uk/product/aqara-doorbell-camera-hub-g410-select/"),
 "aqara_g410_specs": ("Aqara G410 specifications", "https://www.aqara.com/us/product/doorbell-camera-hub-g410-specs/"),
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
 "aqara_g100": ("Aqara UK Shop: Camera G100 Select", "https://www.aqara-shop.co.uk/product/aqara-camera-g100-select/"),
 "tapo_c675d": ("Tapo UK: C675D KIT", "https://uk.store.tapo.com/products/tapo-c675d-kit-4k-solar-powered-dual-lens-pan-tilt-security-camera-kit"),
 "aqara_g5pro": ("Aqara UK Shop: Camera Hub G5 Pro (Wi-Fi 32GB)", "https://www.aqara-shop.co.uk/product/aqara-camera-hub-g5-pro-wi-fi-32gb/"),
 "aqara_g350": ("Aqara UK Shop: Camera Hub G350 Select", "https://www.aqara-shop.co.uk/product/aqara-camera-hub-g350-select/"),
 "reo_altas": ("Reolink UK: Altas PT Ultra", "https://reolink.com/gb/product/altas-pt-ultra/"),
 "reo_arguspt": ("Reolink UK: Argus PT Ultra", "https://reolink.com/gb/product/argus-pt-ultra/"),
 "amz_blink_mini4k": ("Amazon UK: Blink Mini 4K+", "https://www.amazon.co.uk/dp/B0GWSJV4H5"),
 "blink_mini4k_specs": ("Blink: Mini 4K+ FAQ", "https://support.blinkforhome.com/en_GB/mini-4k-plus-faq/faq-mini-4k-plus"),
 "ring_outpro": ("Ring UK: Outdoor Camera 4K Pro (plug-in)", "https://en-uk.ring.com/products/stick-up-cam-pro-plug-in"),
 "ring_plus": ("Ring UK: Outdoor Camera Plus (plug-in)", "https://en-uk.ring.com/products/outdoor-cam-plus-plugin"),
 "amz_blink_cam": ("Amazon UK: Blink Outdoor 4", "https://www.amazon.co.uk/blink-camera-outdoor-4/dp/B0DHLTMW3X"),
 "amz_sm2": ("Amazon UK: Blink Sync Module 2", "https://www.amazon.co.uk/dp/B08BJ9ZCZC"),
 "blink_storage": ("Blink: local storage options", "https://support.blinkforhome.com/en_GB/blink-storage-options"),
 # Blink sells through Amazon rather than a UK shop of its own, so the 2K+'s
 # price is the listing's, read in the browser on the day it was added, and its
 # specs are Blink's own support page for the model.
 "amz_blink_2kp": ("Amazon UK: Blink Outdoor 2K+", "https://www.amazon.co.uk/blink-outdoor-camera-2k-/dp/B0F964Q9Y8"),
 "blink_2kp_specs": ("Blink: Outdoor 2K+ technical specifications", "https://support.blinkforhome.com/en_US/outdoor-2k-technical-specifications"),
 "blink_liveview": ("Blink: Extended Live View", "https://support.blinkforhome.com/using-mini/extended-live-view"),
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
 "uh_faq": ("Ultrahuman: Ring AIR FAQ", "https://www.ultrahuman.com/global/ring/faq"),
 "ha_ultra": ("Home Assistant: Ultrahuman (community)", "https://github.com/anant-j/Ultrahuman"),
 "ultra_pro": ("Ultrahuman UK: Ring PRO", "https://www.ultrahuman.com/gb/ring-pro/buy"),
 "uh_pro": ("Ultrahuman Ring PRO", "https://www.ultrahuman.com/gb/ring-pro/"),
 "amz_rc2": ("Amazon UK: RingConn Gen 2", "https://www.amazon.co.uk/dp/B0DG2QKMFX"),
 "rc2_product": ("RingConn Gen 2", "https://ringconn.com/products/ringconn-gen-2"),
 "amz_rc2a": ("Amazon UK: RingConn Gen 2 Air", "https://www.amazon.co.uk/dp/B0DWK4QQ7H"),
 "rc2a_product": ("RingConn Gen 2 Air", "https://ringconn.com/products/ringconn-gen-2-air"),
 "amz_rc3": ("Amazon UK: RingConn Gen 3", "https://www.amazon.co.uk/dp/B0GVSGY854"),
 "rc3_product": ("RingConn Gen 3", "https://ringconn.com/products/ringconn-gen-3"),
 "rc_nosub": ("RingConn: what the rings cost to run", "https://ringconn.com/blogs/guides/ringconn-cost-guide"),
 "amz_samsung": ("Amazon UK: Samsung Galaxy Ring", "https://www.amazon.co.uk/dp/B0DNTFZLDZ"),
 "samsung_support": ("Samsung UK: how to use Galaxy Ring", "https://www.samsung.com/uk/support/mobile-devices/how-to-use-the-samsung-galaxy-ring/"),
 # Where a ring is sold by more than one UK shop, each offer cites its own page
 # and names the configuration its price is for.
 "argos_oura4": ("Argos: Oura Ring 4", "https://www.argos.co.uk/product/7727465"),
 "argos_ultra": ("Argos: Ultrahuman Ring AIR", "https://www.argos.co.uk/product/4165068"),
 "argos_rc2": ("Argos: RingConn Gen 2", "https://www.argos.co.uk/product/7614640"),
 "currys_rc2": ("Currys: RingConn Gen 2", "https://www.currys.co.uk/products/ringconn-gen-2-smart-ring-matte-black-size-7-10278293.html"),
 "currys_samsung": ("Currys: Samsung Galaxy Ring", "https://www.currys.co.uk/products/samsung-galaxy-ring-titanium-gold-size-14-10277185.html"),
 "oura_store5": ("Oura: Ring 5", "https://ouraring.com/store/rings/oura-ring-5/silver"),
 "argos_oura5": ("Argos: Oura Ring 5", "https://www.argos.co.uk/product/8566340"),
 "currys_oura5": ("Currys: Oura Ring 5", "https://www.currys.co.uk/products/oura-ring-5-silver-size-8-10304738.html"),
 "amazfit_uk": ("Amazfit UK: Helio Ring", "https://uk.amazfit.com/products/amazfit-helio-ring"),
 "amazfit_aura": ("Amazfit UK: Zepp Aura", "https://uk.amazfit.com/pages/zepp-aura"),
 "ha_zepp": ("Home Assistant: Zepp2Hass (community)", "https://community.home-assistant.io/t/zepp2hass-connect-your-amazfit-zepp-watch-to-home-assistant/973979"),
 "ha_index": ("Home Assistant integrations", "https://www.home-assistant.io/integrations/"),
 # Printers: the maker's UK page carries the printer's price and its ink, so
 # the printer page is the source for both where it publishes the cartridge.
 "epson_et2951": ("Epson UK: EcoTank ET-2951", "https://www.epson.co.uk/en_GB/products/printers/inkjet/consumer/ecotank-et-2951-a4-multifunction-wi-fi-ink-tank-printer,-with-up-to-3-years-of-ink-included/p/52035"),
 "canon_g3590": ("Canon UK: PIXMA G3590", "https://www.canon.co.uk/store/canon-pixma-g3590-3-in-1-refillable-megatank-inkjet-printer/6706C008/"),
 "canon_g3570": ("Canon UK: PIXMA G3570", "https://www.canon.co.uk/store/canon-pixma-g3570-wireless-colour-3-in-1-refillable-megatank-printer-black/5805C008/"),
 "canon_g3570_spec": ("Canon UK: PIXMA G3570 specifications", "https://www.canon.co.uk/printers/pixma-g3570-series/specifications/"),
 "canon_ts6550i": ("Canon UK: PIXMA TS6550i", "https://www.canon.co.uk/store/canon-pixma-ts6550i-wireless-colour-3-in-1-inkjet-photo-printer/7179C008/"),
 "canon_ts6550i_price": ("Canon UK: PIXMA Print Plan printers", "https://www.canon.co.uk/store/pixma-print-plan-printers/"),
 "canon_ts6550i_xl": ("Canon UK: PG-595XL + CL-586XL value pack", "https://www.canon.co.uk/store/canon-pg-595xl-cl-586xl-high-yield-ink-cartridges-photo-paper-value-pack/7170C004/"),
 "canon_print_plan": ("Canon UK: PIXMA Print Plan", "https://www.canon.co.uk/printer-ink-subscription/pixma-print-plan"),
 "brother_j1310dw": ("Brother UK: DCP-J1310DW", "https://store.brother.co.uk/devices/inkjet/dcpj/dcpj1310dw"),
 "brother_ecopro": ("Brother EcoPro UK", "https://ecopro.brother.co.uk/"),
 "brother_lc521": ("Brother UK: LC521 ink cartridges", "https://store.brother.co.uk/supplies/inkjet/ink-cartridges-single-pack/lc/lc521bk"),
 "brother_j1200w": ("Brother UK: DCP-J1200W", "https://store.brother.co.uk/devices/inkjet/dcpj/dcpj1200w"),
 "brother_j1200w_ink": ("Brother UK: LC424 ink for the DCP-J1200W", "https://store.brother.co.uk/devices/inkjet/dcpj/dcpj1200w"),
 "ryman_j1200w": ("Ryman: DCP-J1200W clearance", "https://www.ryman.co.uk/brother-dcp-j1200w-3-in-1-wireless-inkjet-printer-1"),
 "hp_envy6530e": ("HP UK: Envy 6530e", "https://www.hp.com/gb-en/shop/products/printers/hp-envy-6530e-all-in-one-printer-714p1b-687"),
 "hp_envy6520e": ("HP UK store: Envy printers", "https://www.hp.com/gb-en/shop/listings/printers?subbrand=hp-envy"),
 "hp_308pack": ("HP UK: HP+ terms and 308 ink", "https://www.hp.com/gb-en/shop/products/printers/hp-envy-6530e-all-in-one-printer-714p1b-687"),
 "hp_instantink": ("HP Instant Ink UK", "https://instantink.hpconnected.com/uk/en/l/"),
 # Pet trackers: the vendor's own page carries the model and its price; the
 # support pages carry the data term, the plan and the app requirements.
 "pitpat_product": ("PitPat UK: GPS dog tracker", "https://www.pitpat.com/gps-tracker"),
 "pitpat_spec": ("PitPat: tracker specifications", "https://www.pitpat.com/device/pitpat-dog-gps-tracker-technical-specifications"),
 "pitpat_life": ("PitPat LIFE", "https://www.pitpat.com/pitpatlife"),
 "pitpat_terms": ("PitPat: connectivity and live tracking service", "https://terms.pitpat.com/kb/guide/en-GB/connectivity-live-tracking-service-asdbD8CvhD/Steps/4455976"),
 "pitpat_faqs": ("PitPat GPS FAQs", "https://www.pitpat.com/gps-tracker/faqs"),
 "pawva_x01": ("PAWVA X01+", "https://www.pawva.co.uk/product-page/pawva-x01-gps-dog-tracker-with-light-sound"),
 "pawva_home": ("PAWVA UK", "https://www.pawva.co.uk/"),
 "pawva_x05": ("PAWVA X05", "https://www.pawva.co.uk/product-page/pawva-x05-gps-dog-tracker"),
 "pawva_bundle": ("PAWVA PackTracker bundle", "https://www.pawva.co.uk/product-page/packtracker-gps-system"),
 "ofcom_3g": ("Ofcom: 3G switch-off", "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/3g-switch-off"),
 "tractive_dog6": ("Tractive UK: DOG 6", "https://tractive.com/en/pd/gps-tracker-dog?shopCountry=GB"),
 "tractive_cat6": ("Tractive UK: CAT 6 Mini", "https://tractive.com/en/pd/gps-tracker-cat?shopCountry=GB"),
 "tractive_plans": ("Tractive UK: plans", "https://tractive.com/en/c/plans?shopCountry=GB"),
 "tractive_premium": ("Tractive: Premium plan features", "https://help.tractive.com/hc/en-us/articles/360000222729-What-features-does-the-Premium-plan-offer"),
 "tractive_app": ("Tractive: app requirements", "https://help.tractive.com/hc/en-us/articles/206188539-How-to-download-the-Tractive-GPS-app"),
 "weenect_xt": ("Weenect UK: XT", "https://www.weenect.com/uk/en/gps-dog-tracker/weenect-xt"),
 "weenect_subs": ("Weenect UK: subscriptions", "https://www.weenect.com/uk/en/subscriptions"),
 "weenect_coverage": ("Weenect: network coverage", "https://www.weenect.com/uk/en/network-coverage"),
 "weenect_support": ("Weenect: subscription prices", "https://help.weenect.com/hc/en-gb/articles/207813809-How-Much-Does-a-Subscription-to-the-Weenect-Service-Cost"),
 "pawfit_3": ("Pawfit UK: Pawfit 3", "https://www.pawfit.com/en-gb/product/pawfit-3.html"),
 "pawfit_plans": ("Pawfit UK: subscriptions", "https://www.pawfit.com/en-gb/subscription.html"),
 "pawfit_compare": ("Pawfit: tracker comparison", "https://www.pawfit.com/en-gb/pawfit-trackers-compare.html"),
 "amz_pawfit": ("Amazon UK: Pawfit 3", "https://www.amazon.co.uk/Pawfit-Activity-Included-Embedded-Waterproof/dp/B082F7J7LW"),
 "apple_airtag": ("Apple UK: AirTag", "https://www.apple.com/uk/airtag"),
 "apple_airtag_buy": ("Apple UK: buy AirTag", "https://www.apple.com/uk/shop/buy-airtag/airtag/1-pack"),
 # Baby monitors: a local monitor's specification is the maker's page; a
 # hybrid's or a Wi-Fi monitor's is too, and the retailer page is where the
 # price is published.
 "vtech_vm4263": ("VTech UK: VM4263", "https://www.vtechphones.eu/en-UK/baby-care/video-baby-monitor/VM4263"),
 "mamas_vm4263": ("Mamas & Papas: VTech VM4263", "https://www.mamasandpapas.com/products/vtech-vm4263-3-5inch-monitor-679102700"),
 "argos_vm4263": ("Argos: VTech VM4263", "https://www.argos.co.uk/product/7895995"),
 "philips_scd881": ("Philips UK: Avent SCD881/05 support", "https://www.philips.co.uk/c-p/SCD881_05/video-baby-monitor-advanced/support"),
 "currys_scd881": ("Currys: Avent SCD881/05", "https://www.currys.co.uk/products/philips-avent-avent-scd88105-video-baby-monitor-coral-cream-10289086.html"),
 "philips_scd951": ("Philips UK: Avent Connected SCD951/26", "https://www.philips.co.uk/c-p/SCD951_26/connected-connected-baby-monitor"),
 "philips_spec": ("Philips UK: SCD951/26 specifications", "https://www.philips.co.uk/shop/UK_Klarna/mother-child-care/baby-monitors-thermometers/connected-connected-baby-monitor/p/SCD951_26"),
 "philips_pairs": ("Philips: pairing a parent unit", "https://www.philips.co.uk/c-f/XC000021639/can-i-connect-my-baby-camera-to-a-parent-unit-of-another-baby-monitor"),
 "philips_manual": ("Philips: SCD951/SCD953 user manual", "https://www.documents.philips.com/assets/20241120/ca09a46c127b4df18c69b22e0036abdf.pdf"),
 "currys_scd951": ("Currys: Avent Connected SCD951/26", "https://www.currys.co.uk/products/philips-avent-avent-connected-scd95126-smart-video-baby-monitor-white-10289121.html"),
 "amz_scd951": ("Amazon UK: Avent Connected SCD951/26", "https://www.amazon.co.uk/Philips-Connected-Screentime-SCD951-26/dp/B0DSLN78G2"),
 "eufy_c10": ("eufy UK: Baby Monitor C10", "https://www.eufy.com/uk/products/e6310221"),
 "nanit_pro": ("Nanit UK: Pro camera", "https://nanituk.co.uk/products/nanit-pro-camera"),
 "nanit_memberships": ("Nanit UK: memberships", "https://nanituk.co.uk/pages/memberships"),
 "nanit_breathing": ("Nanit UK: Breathing Band", "https://nanituk.co.uk/products/nanit-breathing-band%E2%84%A2-outlet-item"),
 "owlet_sock": ("Owlet UK: Dream Sock", "https://owletbabycare.co.uk/products/dream-sock-pulse-oximeter-pediatric"),
 "owlet_360": ("Owlet: Owlet360", "https://owletbabycare.co.uk/pages/owlet-360"),
 "owlet_support": ("Owlet support: Owlet360 FAQ", "https://support.owletcare.com/hc/en-us/articles/36307322862093-Owlet360-FAQ"),

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


# Awin: publisher 3141383. A deep link hands the click to the network, which
# sets its own cookie and forwards the reader to the shop's own page; the
# destination travels percent-encoded in `ued`. No script goes on this site, so
# the redirect is the whole integration, and the claim in the footer that this
# page sets no cookie stays true.
AWIN_PUBLISHER = "3141383"
AWIN_CLICK = "https://www.awin1.com/cread.php"


def awin_tagged(url, merchant):
    return (f"{AWIN_CLICK}?awinmid={merchant}&awinaffid={AWIN_PUBLISHER}"
            f"&ued={quote(url, safe='')}")


# Awin advertiser ids, by source key. The id belongs to the merchant, not to us:
# a wrong one credits another advertiser, so a shop whose id is not confirmed in
# the Awin account stays a plain link rather than a mistracked one.
# Currys is on Awin (advertiser 1599, 3% for editorial), so its offers are the
# live part of the integration. Argos sells two of these rings and has no
# programme we are in, so its links stay plain.
# Programme status, by Awin advertiser id, for publisher 3141383. Only an
# approved programme is a live affiliate: a rejected or pending one earns
# nothing, so its shop is linked plainly and ranks as PAY_RETAIL. Move an id to
# "approved" only once Awin confirms it, then list its source keys below.
AWIN_PROGRAMMES = {
    1599: ("Currys", "rejected"),      # 5 Nov 2026: site does not complement brand
    3090: ("Very", "rejected"),        # 5 Nov 2026: publisher type
    69428: ("Ultrahuman", "pending"),
}
AWIN_PENDING_BRANDS = ("Arlo", "Anker/eufy", "Aqara", "Reolink")  # pending, ids unconfirmed


def awin_live(merchant):
    return AWIN_PROGRAMMES.get(merchant, ("", "unknown"))[1] == "approved"


# Source key -> Awin advertiser id. Only approved programmes are tagged.
AWIN_LINKS = {
    "currys_rc2": 1599, "currys_samsung": 1599, "currys_oura5": 1599,
}
AWIN_MERCHANTS = {k: m for k, m in AWIN_LINKS.items() if awin_live(m)}


# ---------- where to buy ----------
# A ring is sold by several UK shops and its price moves with size and finish,
# so a row lists the offers that were checked rather than one price. The page
# shows one of them: the cheapest, unless another offer is within
# OFFER_WINDOW of it and pays us more. `pay` is a rank and not a rate, because
# only Amazon publishes a fixed percentage, and the shop's own configuration
# travels in `note` so two prices are never compared across a size or finish.
OFFER_WINDOW = 5.0
PAY_RETAIL = 1   # a UK shop we have no programme with: it pays us nothing
PAY_AMAZON = 2   # Amazon UK Associates: a small rate on the whole price
PAY_BRAND = 3    # a brand programme that pays more again (Ultrahuman 7-15%)


def offer_winner(offers):
    """The offer a reader sees: cheapest, then the one that pays us most.

    Only an offer within OFFER_WINDOW of the cheapest can win, so the shop that
    pays us better can never add more than that to the price. A tie falls to
    the cheaper offer and then to the shop's name, so the winner is a function
    of the data rather than of the order the list is written in.
    """
    cheapest = min(o["price"] for o in offers)
    near = [o for o in offers if o["price"] <= cheapest + OFFER_WINDOW + 1e-9]
    return min(near, key=lambda o: (-o["pay"], o["price"], o["shop"]))


def offer_shown(offers):
    """The offer whose price the reader sees.

    The winner, unless the winner is Amazon: Amazon's rules bar showing its
    price, so the figure comes from another UK shop at the same price, while
    the link stays Amazon's. With no such shop the winner comes back and the
    row says "Check price".
    """
    won = offer_winner(offers)
    if won["pay"] != PAY_AMAZON:
        return won
    twins = [o for o in offers if o is not won and o["pay"] != PAY_AMAZON
             and abs(o["price"] - won["price"]) < 1e-9]
    return min(twins, key=lambda o: o["shop"]) if twins else won


# rec: 'yes' records free out of the box / 'kit' needs extra hardware or very limited / 'no'
# score parts: rec 0-2, live 0-1, alerts 0-1, ai 0-1, storage_in_box 0-1, ha 0-2  (max 8)
ROWS = [
# ---------- printers ----------
# A tank's 3-year sum is its price alone: the bottles in the box outlast the
# period at 100 pages a month. A cartridge printer's sum buys 36 months of
# original cartridges, priced from the maker's own UK ink page and ISO yields.
# Starter cartridges are ignored in both routes, so the retail figure is an
# upper bound and the plan is often the cheaper route for a cartridge model.
dict(cat="printers", id="epson-et-2951", brand="Epson", model="EcoTank ET-2951", rec="yes", power=["tank"], ha=2,
 price=239.99, price_note="Epson UK (was £319.99)", price_src="epson_et2951",
 extra=0, extra_note="Ink bottles in the box", free_records=True,
 sub=None, sub_name="No Epson ink plan",
 best="A busy household that wants the ink paid for up front",
 catch="The dearest printer here, and the paper tray holds only 100 sheets.",
 storage="Six bottles in the box: 6,600 black and 5,500 colour pages",
 live="15 ppm mono, 8 ppm colour (ISO)", alerts="Automatic",
 ai="Yes, flatbed scan and copy",
 history="Yes, refill from bottles with no plan or account",
 paywalled="Nothing. Epson ReadyPrint MAX is optional",
 sub_text="None needed. Epson's optional ReadyPrint MAX plan does not change the ink in the box",
 ha_text="No account needed; AirPrint and Mopria print without an app.",
 wifi="Wi-Fi, Wi-Fi Direct and USB",
 score=dict(rec=2,storage=1,live=1,alerts=1,ai=1,ha=2),
 src=["epson_et2951"],
 rec_src="epson_et2951", history_src="epson_et2951", ha_src="epson_et2951", plan_src="epson_et2951", unverified=""),
# Canon's cheapest current MegaTank. The four bottles in the box are the ink
# route, like Epson's, so the three-year sum is the printer's price alone.
dict(cat="printers", id="canon-pixma-g3590", brand="Canon", model="PIXMA G3590", rec="yes", power=["tank"], ha=2,
 price=189.99, price_note="Canon UK store sale (was £249.99)", price_src="canon_g3590",
 extra=0, extra_note="Ink bottles in the box", free_records=True,
 sub=None, sub_name="No Canon ink plan",
 best="A cheaper tank that still covers three years of ink",
 catch="Slower than the Epson at 11/6 ipm, with the same 100-sheet tray.",
 storage="Four GI-51 bottles in the box: 6,000 black and 7,700 colour pages",
 live="11 ipm mono, 6 ipm colour (ISO)", alerts="Automatic",
 ai="Yes, flatbed scan and copy",
 history="Yes, refill from GI-51 bottles with no plan or account",
 paywalled="Nothing. Canon Auto-Ink Delivery is optional",
 sub_text="None needed. Canon's optional Auto-Ink Delivery sends bottles when low",
 ha_text="No account needed. The Canon PRINT app is optional.",
 wifi="Wi-Fi and USB",
 score=dict(rec=2,storage=1,live=1,alerts=1,ai=1,ha=2),
 src=["canon_g3590"],
 rec_src="canon_g3590", history_src="canon_g3590", ha_src="canon_g3590", plan_src="canon_g3590", unverified=""),
# Canon's previous MegaTank, still listed by Canon UK. It is the older 3-in-1
# with manual two-sided printing, and Canon prices it above the newer G3590,
# so the row records what the newer model's sale price actually buys.
dict(cat="printers", id="canon-pixma-g3570", brand="Canon", model="PIXMA G3570", rec="yes", power=["tank"], ha=2,
 price=229.99, price_note="Canon UK store (was £264.98)", price_src="canon_g3570",
 extra=0, extra_note="Ink bottles in the box", free_records=True,
 sub=None, sub_name="No Canon ink plan",
 best="A heavy household that can live without automatic duplex",
 catch="Older than the G3590, and two-sided printing is manual rather than automatic.",
 storage="Four GI-51 bottles in the box: 6,000 black and 7,700 colour pages",
 live="11 ipm mono, 6 ipm colour (ISO)", alerts="Manual",
 ai="Yes, flatbed scan and copy",
 history="Yes, refill from GI-51 bottles with no plan or account",
 paywalled="Nothing. Canon Auto-Ink Delivery is optional",
 sub_text="None needed. Canon's optional Auto-Ink Delivery sends bottles when low",
 ha_text="No account needed. The Canon PRINT app is optional.",
 wifi="Wi-Fi (2.4 and 5 GHz) and USB",
 score=dict(rec=2,storage=1,live=1,alerts=0,ai=1,ha=2),
 src=["canon_g3570","canon_g3570_spec"],
 rec_src="canon_g3570", history_src="canon_g3570", ha_src="canon_g3570", plan_src="canon_g3570", unverified=""),
# Canon's cartridge sibling. The £49.99 is the current Canon sale, and the
# plan route is cheaper than retail because six 300-page XL packs cost
# £365.94 while 36 months of the 100-page plan cost £161.64.
dict(cat="printers", id="canon-pixma-ts6550i", brand="Canon", model="PIXMA TS6550i", rec="yes", power=["cart"], ha=2,
 price=49.99, price_note="Canon UK store sale (was £89.99)", price_src="canon_ts6550i_price",
 extra=365.94, extra_note="+ 6 PG-595XL/CL-586XL packs (300 pages each)", extra_src="canon_ts6550i_xl", free_records=True,
 sub=4.49, sub_name="PIXMA Print Plan 100",
 best="A cheap printer with the cheapest plan route",
 catch="The £49.99 is a sale price, and the starter cartridges hold about 180 pages each.",
 storage="Starter cartridges: about 180 black and 180 colour pages",
 live="15 ipm mono, 10 ipm colour (ISO)", alerts="Automatic",
 ai="Yes, flatbed scan and copy",
 history="Yes, PG-595 and CL-586 cartridges from any shop with no account",
 paywalled="Nothing. PIXMA Print Plan is optional",
 sub_text="PIXMA Print Plan £4.49/month for 100 pages; 30 pages £2.49, 60 pages £3.99, 200 pages £8.99",
 ha_text="No account needed. The Canon PRINT app is optional.",
 wifi="Wi-Fi and USB",
 score=dict(rec=2,storage=0,live=1,alerts=1,ai=1,ha=2),
 src=["canon_ts6550i","canon_ts6550i_price","canon_ts6550i_xl","canon_print_plan"],
 rec_src="canon_ts6550i", history_src="canon_ts6550i", ha_src="canon_ts6550i", plan_src="canon_print_plan", unverified=""),
dict(cat="printers", id="brother-dcp-j1310dw", brand="Brother", model="DCP-J1310DW", rec="yes", power=["cart"], ha=2,
 price=132.23, price_note="Brother UK store", price_src="brother_j1310dw",
 extra=277.46, extra_note="+ 36 months of LC521 cartridges", extra_src="brother_lc521", free_records=True,
 sub=4.49, sub_name="Brother EcoPro 100",
 best="A current Brother whose cartridges print 500 pages each",
 catch="The starter cartridges run out after about 200 pages, and retail LC521 ink costs £277 over three years.",
 storage="Starter cartridges only: about 200 black and 200 colour pages",
 live="16 ppm mono, 9 ppm colour (ISO)", alerts="Automatic",
 ai="Yes, flatbed scan and copy",
 history="Yes, LC521 cartridges from any shop with no account",
 paywalled="Nothing. Brother EcoPro is optional",
 sub_text="EcoPro £4.49/month for 100 pages; 50 pages £2.99, 300 pages £9.99",
 ha_text="No account needed; AirPrint and Mopria print without an app.",
 wifi="Wi-Fi (2.4 and 5 GHz), Wi-Fi Direct and USB",
 score=dict(rec=2,storage=0,live=1,alerts=1,ai=1,ha=2),
 src=["brother_j1310dw","brother_ecopro","brother_lc521"],
 rec_src="brother_j1310dw", history_src="brother_j1310dw", ha_src="brother_j1310dw", plan_src="brother_ecopro",        nosub_say="36 months of LC521 cartridges at 100 pages a month, 50 mono and 50 colour.", unverified=""),
# Brother's previous small inkjet. Brother UK no longer prices it, so the £40 is
# a Ryman clearance, and the ink route is the LC424 multipack at £75 for 750
# pages of each colour, so 2.4 packs cover 36 months at 100 pages a month.
dict(cat="printers", id="brother-dcp-j1200w", brand="Brother", model="DCP-J1200W", rec="yes", power=["cart"], ha=2,
 price=40.00, price_note="Ryman clearance (was £69.99); Brother no longer prices it", price_src="ryman_j1200w",
 extra=180.00, extra_note="+ 2.4 LC424 multipacks (750 pages each)", extra_src="brother_j1200w_ink", free_records=True,
 sub=4.49, sub_name="Brother EcoPro 100",
 best="The cheapest way into a 3-in-1, while the clearance lasts",
 catch="The £40 is a clearance on a printer Brother no longer prices, and retail LC424 ink costs £180 over three years.",
 storage="In-box inks: about 720 black and 480 colour pages",
 live="16 ipm mono, 9 ipm colour (ISO)", alerts="Manual",
 ai="Yes, flatbed scan and copy",
 history="Yes, LC424 cartridges from any shop with no account",
 paywalled="Nothing. Brother EcoPro is optional",
 sub_text="EcoPro £4.49/month for 100 pages; 50 pages £2.99, 300 pages £9.99",
 ha_text="No account needed; AirPrint and Mopria print without an app.",
 wifi="Wi-Fi (2.4 GHz) and USB",
 score=dict(rec=2,storage=0,live=1,alerts=0,ai=1,ha=2),
 src=["ryman_j1200w","brother_j1200w","brother_j1200w_ink","brother_ecopro"],
 rec_src="brother_j1200w", history_src="brother_j1200w_ink", ha_src="brother_j1200w", plan_src="brother_ecopro",
 nosub_say="36 months of LC424 multipacks at 100 pages a month, 50 mono and 50 colour.", unverified=""),
dict(cat="printers", id="hp-envy-6530e", brand="HP", model="Envy 6530e", rec="brief", power=["cart"], ha=0,
 price=71.80, price_note="HP UK (was £106)", price_src="hp_envy6530e",
 extra=547.35, extra_note="+ 15 HP 308 black/tri-colour packs", extra_src="hp_envy6530e", free_records=True,
 sub=6.49, sub_name="HP Instant Ink 100 pages",
 best="A light household that will take the ink plan",
 catch="Retail ink is the dearest here, HP+ needs an account, and the printer is set to original HP ink.",
 storage="Setup cartridges only: about 120 black and 75 colour pages",
 live="10 ppm mono, 7 ppm colour (ISO)", alerts="Automatic",
 ai="Yes, flatbed scan, copy and a 35-sheet ADF",
 history="Yes, HP 308 cartridges, but the printer is set to original HP ink",
 paywalled="Nothing. Instant Ink is optional",
 sub_text="Instant Ink £6.49/month for 100 pages; 50 pages £4.49, 300 pages £13.49",
 ha_text="An HP account is required. HP+ activation at setup ties the printer to HP's service.",
 wifi="Wi-Fi (2.4 and 5 GHz), Wi-Fi Direct and USB",
 score=dict(rec=1,storage=0,live=1,alerts=1,ai=1,ha=0),
 src=["hp_envy6530e","hp_instantink"],
 rec_src="hp_envy6530e", history_src="hp_envy6530e", ha_src="hp_envy6530e", plan_src="hp_instantink",        nosub_say="36 months of HP 308 black/tri-colour packs at 100 pages a month, 50 mono and 50 colour.", unverified=""),
# HP's previous Envy, still listed on HP's UK store. It takes the same 308 packs
# as the 6530e, so the three-year sum is the same ink at a dearer printer.
dict(cat="printers", id="hp-envy-6520e", brand="HP", model="Envy 6520e", rec="brief", power=["cart"], ha=0,
 price=97.90, price_note="HP UK (was £106)", price_src="hp_envy6520e",
 extra=547.35, extra_note="+ 15 HP 308 black/tri-colour packs", extra_src="hp_308pack", free_records=True,
 sub=6.49, sub_name="HP Instant Ink 100 pages",
 best="A household that wants automatic duplex and will take the plan",
 catch="Costs £26 more than the 6530e at HP's prices, and retail 308 ink is the dearest route here.",
 storage="Setup cartridges only: about 120 black and 75 colour pages",
 live="10 ppm mono, 7 ppm colour (ISO)", alerts="Automatic",
 ai="Yes, flatbed scan and copy",
 history="Yes, HP 308 cartridges, but the printer is set to original HP ink",
 paywalled="Nothing. Instant Ink is optional",
 sub_text="Instant Ink £6.49/month for 100 pages; 50 pages £4.49, 300 pages £13.49",
 ha_text="An HP account is required. HP+ activation at setup ties the printer to HP's service.",
 wifi="Wi-Fi, Wi-Fi Direct and USB",
 score=dict(rec=1,storage=0,live=1,alerts=1,ai=1,ha=0),
 src=["hp_envy6520e","hp_308pack","hp_instantink"],
 rec_src="hp_envy6520e", history_src="hp_308pack", ha_src="hp_envy6520e", plan_src="hp_instantink",
 nosub_say="36 months of HP 308 black/tri-colour packs at 100 pages a month, 50 mono and 50 colour.", unverified=""),
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
dict(cat="doorbells", id="ring-4kpro", brand="Ring", model="Battery Video Doorbell 4K Pro", rec="no", power=["battery"], ha=0,
 price=219.99, price_note="Ring UK", price_src="ring_4kpro",
 extra=0, extra_note="", free_records=False,
 sub=4.99, sub_name="Ring Solo",
 best="Ring households that want the sharpest battery doorbell",
 catch="Saves no video at all unless you pay £4.99 a month, and Ring publishes no battery-life figure.",
 storage="None. No on-device or hub storage.", live="Yes", alerts="Yes, motion and button-press alerts",
 ai="Paid (person, package and vehicle alerts on Ring's plans page)",
 history="None", paywalled="All recording and playback (up to 180 days), smart alerts, Extended Live View; 24/7 recording is £3/month extra per device",
 sub_text="Ring Solo £4.99/month or £49.99/year (1 device). Multi £7.99/month, AI Pro £15.99/month",
 ha_text="Official integration, but it goes through Ring's cloud. No local-only option.",
 wifi="Dual-band 2.4/5 GHz (Wi-Fi 6)",
 score=dict(rec=0,live=1,alerts=1,ai=0,storage=0,ha=0),
 src=["ring_4kpro","ring_plans","ha_ring"],
 rec_src="ring_plans", history_src="ring_plans", ha_src="ha_ring", plan_src="ring_plans",
 unverified=""),
dict(cat="doorbells", id="ring-wpro", brand="Ring", model="Wired Video Doorbell 4K Pro", rec="no", power=["wired"], ha=0,
 price=219.99, price_note="Ring UK", price_src="ring_wpro",
 extra=0, extra_note="", free_records=False,
 sub=4.99, sub_name="Ring Solo",
 best="Ring households replacing an existing wired bell",
 catch="Saves no video at all unless you pay £4.99 a month, and there is no battery option.",
 storage="None. No on-device or hub storage.", live="Yes", alerts="Yes, motion and button-press alerts",
 ai="Paid (person, package and vehicle alerts on Ring's plans page)",
 history="None", paywalled="All recording and playback (up to 180 days), smart alerts, Extended Live View; 24/7 recording is £3/month extra per device",
 sub_text="Ring Solo £4.99/month or £49.99/year (1 device). Multi £7.99/month, AI Pro £15.99/month",
 ha_text="Official integration, but it goes through Ring's cloud. No local-only option.",
 wifi="Dual-band Wi-Fi 6 (2.4 and 5 GHz)",
 score=dict(rec=0,live=1,alerts=1,ai=0,storage=0,ha=0),
 src=["ring_wpro","ring_wpro_spec","ring_plans","ha_ring"],
 rec_src="ring_plans", history_src="ring_plans", ha_src="ha_ring", plan_src="ring_plans", unverified=""),
dict(cat="doorbells", id="ring-elite", brand="Ring", model="Wired Video Doorbell 4K Elite", rec="no", power=["poe"], ha=0,
 price=449.99, price_note="Ring UK", price_src="ring_elite",
 extra=0, extra_note="", free_records=False,
 sub=4.99, sub_name="Ring Solo",
 best="Gated entries and new builds that can run an Ethernet cable to the door",
 catch="Saves no video at all unless you pay £4.99 a month, and it needs PoE+ from a switch or injector.",
 storage="None. No on-device or hub storage.", live="Yes", alerts="Yes, motion and button-press alerts",
 ai="Paid (person, package and vehicle alerts on Ring's plans page)",
 history="None", paywalled="All recording and playback (up to 180 days), smart alerts, Extended Live View; 24/7 recording is £3/month extra per device",
 sub_text="Ring Solo £4.99/month or £49.99/year (1 device). Multi £7.99/month, AI Pro £15.99/month",
 ha_text="Official integration, but it goes through Ring's cloud. No local-only option.",
 wifi="None: the Ethernet cable carries power and data, so it joins no Wi-Fi network",
 score=dict(rec=0,live=1,alerts=1,ai=0,storage=0,ha=0),
 src=["ring_elite","ring_plans","ha_ring"],
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
 price=121.99, price_note="eufy UK, sale price (RRP £169.99)", price_src="eufy_prod", buy="amz_e340",
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
 src=["eufy_prod","eufy_cloud","eufy_cloud_uk","verge_eufy","sha_nosub","ha_eufy"],
 rec_src="eufy_prod", history_src="eufy_prod", ha_src="ha_eufy", plan_src="eufy_cloud_uk", unverified=""),
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
 src=["eufy_c31","eufy_cloud","eufy_cloud_uk","ha_eufy","sandisk_card"],
 rec_src="eufy_c31", history_src="eufy_c31", ha_src="ha_eufy", plan_src="eufy_cloud_uk", unverified=""),
dict(cat="doorbells", id="eufy-s4", brand="eufy", model="Video Doorbell S4", rec="yes", power=["wired"], ha=1,
 price=269.99, price_note="Anker UK, with Chime 2", price_src="eufy_s4",
 extra=0, extra_note="4 GB storage built in", free_records=True,
 sub=3.99, sub_name="eufy Cloud Backup Basic",
 best="A busy doorstep where a tall visitor and a low parcel must both fit",
 catch="The dearest doorbell here, it needs your existing wiring, and Home Assistant support is unofficial.",
 storage="4 GB built into the doorbell; no card slot", live="Yes", alerts="Yes",
 ai="Free: on-device person detection and auto-framing",
 history="Yes, event clips kept on the doorbell",
 paywalled="Nothing essential; cloud backup is optional",
 sub_text="Optional Cloud Backup £3.99/month or £39.99/year (1 device); £12.99/month for all devices",
 ha_text="Community integration only (ha-eufy-sdk), which still logs in through your eufy account.",
 wifi="Dual-band 2.4/5 GHz (Wi-Fi 6)",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=1),
 src=["eufy_s4","eufy_cloud","eufy_cloud_uk","ha_eufy"],
 rec_src="eufy_s4", history_src="eufy_s4", ha_src="ha_eufy", plan_src="eufy_cloud_uk",
 unverified=""),
dict(cat="doorbells", id="reo-wifi", brand="Reolink", model="Video Doorbell WiFi", rec="yes", power=["wired"], ha=2,
 price=109.99, price_note="Reolink UK store", price_src="reo_store",
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
 price=99.99, price_note="Reolink UK store", price_src="reo_store",
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
 price=119.99, price_note="Machine Mart, includes 64 GB card", price_src="machinemart_reo",
 extra=0, extra_note="64 GB card included (Machine Mart)", free_records=True,
 sub=4.17, sub_name="Reolink Cloud Standard (up to 5 cameras)",
 best="Battery install with 5 GHz Wi-Fi and no fees",
 catch="Footage sits on a card in the doorbell itself unless you add a Home Hub.",
 storage="microSD in the doorbell, or a Home Hub indoors (up to 1 TB)", live="Yes", alerts="Yes",
 ai="Free: person, vehicle and package detection", history="Yes, on card or hub", paywalled="Nothing",
 sub_text="Optional Reolink Cloud. UK £4.17/month, or £2.87/month billed yearly (£34.44/year) for up to 5 cameras",
 ha_text="Official integration through a Reolink Home Hub or NVR, which streams the battery doorbell locally.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=1),
 src=["machinemart_reo","reo_batt","reo_hub","reo_cloud","ha_reo"],
 rec_src="reo_batt", history_src="reo_batt", ha_src="ha_reo", plan_src="reo_cloud",
 unverified=""),
dict(cat="doorbells", id="reo-batt2", brand="Reolink", model="Battery Video Doorbell (2nd Gen)", rec="yes", power=["battery","wired"], ha=1,
 power_note="The battery lasts up to 300 days, and 8–24 VAC doorbell wiring keeps it topped up.",
 price=119.99, price_note="Reolink UK store (was £139.99)", price_src="reo_batt2",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=4.17, sub_name="Reolink Cloud Standard (up to 5 cameras)",
 best="A battery doorbell with a head-to-toe 2K view and no fees",
 catch="The microSD card is not in the box, and without doorbell wiring the battery comes off to charge.",
 storage="microSD (up to 512 GB) in the doorbell, or a Home Hub or NVR; card not included",
 live="Yes", alerts="Yes",
 ai="Free: person, vehicle, animal and package detection on the device",
 history="Yes, motion clips on the card, Home Hub or NVR",
 paywalled="Nothing. Reolink Cloud is optional",
 sub_text="Optional Reolink Cloud. UK £4.17/month, or £2.87/month billed yearly (£34.44/year) for up to 5 cameras",
 ha_text="Official integration through a Reolink Home Hub or NVR, which streams the battery doorbell locally.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["reo_batt2","reo_cloud","ha_reo","sandisk_card"],
 rec_src="reo_batt2", history_src="reo_batt2", ha_src="ha_reo", plan_src="reo_cloud", unverified=""),
dict(cat="doorbells", id="tapo-d235", brand="TP-Link Tapo", model="D235", rec="yes", power=["battery","wired"], ha=0,
 price=89.99, price_note="Tapo UK, in stock (RRP £119.99)", price_src="tapo_d235",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=2.99, sub_name="Tapo Care",
 best="An easy battery doorbell that can be hardwired for 24/7 recording",
 catch="The microSD card is extra, and Home Assistant has no route to the live video.",
 storage="microSD (up to 512 GB) in the doorbell itself", live="Yes", alerts="Yes",
 ai="Free: person, pet, vehicle and package detection",
 history="Yes, on the card; 24/7 only when hardwired",
 paywalled="30-day cloud history, snapshot notifications, Smart Sort",
 sub_text="Optional Tapo Care from £2.99/month or £29.49/year",
 ha_text="Not listed as supported by Home Assistant's official TP-Link integration, and no local route is documented.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["tapo_d235","tapo_care","ha_tplink","sandisk_card"],
 rec_src="tapo_d235", history_src="tapo_d235", ha_src="ha_tplink", plan_src="tapo_care", unverified=""),
dict(cat="doorbells", id="tapo-td21", brand="TP-Link Tapo", model="TD21", rec="yes", power=["battery"], ha=0,
 price=44.99, price_note="Tapo UK, in stock (RRP £56.00)", price_src="tapo_td21", buy="amz_td21",
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
dict(cat="doorbells", id="tapo-d260", brand="TP-Link Tapo", model="Doorbell Pro (D260)", rec="yes", power=["battery","wired"], ha=0,
 price=219.99, price_note="Tapo UK, sold out at the check", price_src="tapo_d260",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=2.99, sub_name="Tapo Care",
 best="Tapo households that want 4K and radar detection with no plan",
 catch="The dearest battery doorbell here, the card is extra, and Home Assistant has no route to the live video.",
 storage="microSD (up to 512 GB) in the doorbell itself", live="Yes", alerts="Yes",
 ai="Free: person, animal, vehicle, package and face detection, plus radar",
 history="Yes, on the card; 24/7 only when hardwired",
 paywalled="30-day cloud history, snapshot notifications, Smart Sort",
 sub_text="Optional Tapo Care from £2.99/month or £29.49/year",
 ha_text="Not listed as supported by Home Assistant's official TP-Link integration, and no local route is documented.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["tapo_d260","tapo_care","ha_tplink","sandisk_card"],
 rec_src="tapo_d260", history_src="tapo_d260", ha_src="ha_tplink", plan_src="tapo_care", unverified=""),
dict(cat="doorbells", id="arlo", brand="Arlo", model="Essential Video Doorbell 2K (2nd gen)", rec="kit", power=["battery"], ha=0,
 power_note="Can be wired to an existing chime for trickle charging, but still runs on its battery.",
 price=69.99, price_note="Arlo UK, half price (was £139.99)", price_src="arlo_2k",
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
 src=["arlo_2k","arlo_blog","arlo_plans","arlo_faq","arlo_doorbell","arlo_hubcompat","arlo_hub","tr_arlo","ambient_arlo","ha_arlo","sandisk_stick"],
 rec_src="arlo_blog", history_src="arlo_doorbell", ha_src="ha_arlo", plan_src="arlo_plans", unverified=""),
dict(cat="doorbells", id="arlo-fhd", brand="Arlo", model="Essential Wireless Video Doorbell FHD", rec="kit", power=["battery"], ha=0,
 power_note="Can be wired to an existing chime for trickle charging, but still runs on its battery.",
 price=49.99, price_note="Arlo UK, Black Friday price (was £89.99)", price_src="arlo_fhd",
 extra=round(109.99 + STICK, 2), extra_note="+ Arlo SmartHub £109.99 + SanDisk 64 GB USB stick",
 extra_src="sandisk_stick", kit_src="arlo_hub", kit_label="SmartHub", kit_price=109.99, free_records=True,
 sub=7.99, sub_name="Arlo Secure (1 camera)",
 best="The cheapest Arlo doorbell, if you already run Arlo kit",
 catch="Records nothing without a £7.99/month plan or a hub costing about £110, and it is only 1080p.",
 storage="Only through an Arlo SmartHub (VMB4540, USB) or a Base Station", live="Yes", alerts="Yes",
 ai="Paid", history="None without a hub",
 paywalled="Cloud recording (7, 14 or 30 days depending on plan), object detection, activity zones, theft replacement",
 sub_text="Arlo Secure £7.99/month (1 camera, 7 days), Multi-Camera £12.99, Secure Plus £19.99 (14 days), Secure Pro £24.99",
 ha_text="No official integration; only a community add-on that goes through Arlo's cloud.",
 wifi="2.4 GHz only",
 score=dict(rec=1,live=1,alerts=1,ai=0,storage=0,ha=0),
 src=["arlo_fhd","arlo_blog","arlo_plans","arlo_faq","arlo_doorbell","arlo_hubcompat","arlo_hub","ha_arlo","sandisk_stick"],
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
dict(cat="doorbells", id="aqara-g410", brand="Aqara", model="Doorbell Camera Hub G410 Select", rec="yes", power=["battery","wired"], ha=1,
 price=129.98, price_note="Aqara UK Shop sale price (RRP £149.99)", price_src="aqara_g410",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed (iCloud+ only for HomeKit Secure Video)",
 best="Apple Home or Matter households that want a doorbell and a hub in one",
 catch="The chime hub holds the card, which is not included, and no power supply is in the box.",
 storage="microSD (up to 512 GB) in the indoor chime hub, NAS, or Aqara's encrypted cloud", live="Yes", alerts="Yes",
 ai="Free: on-device face recognition and mmWave presence detection",
 history="Yes, on the chime's card (24/7 only when wired)",
 paywalled="Nothing essential. HomeKit Secure Video needs Apple's iCloud+, and Aqara's HomeGuardian plan adds cloud AI",
 sub_text="None needed",
 ha_text="Reported to work locally through Home Assistant's HomeKit Device integration, and it streams over RTSP; the doorbell also bridges Matter devices.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["aqara_g410","aqara_g410_specs","ha_homekit","sandisk_card"],
 rec_src="aqara_g410", history_src="aqara_g410", ha_src="ha_homekit", plan_src="aqara_g410", unverified=""),
dict(cat="doorbells", id="blink", brand="Blink", model="Battery Doorbell 2K+", rec="kit", power=["battery"], ha=0,
 price=59.99, price_note="Amazon UK, without the Sync Module", price_src="amz_blink", buy="amz_blink", price_check=True,
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
dict(cat="doorbells", id="ezviz-ep3x", brand="EZVIZ", model="EP3x Pro", rec="yes", power=["battery"], ha=0,
 price=99.99, price_note="Chester Digital Supplies, UK retailer", price_src="chester_ep3x", buy="amz_ep3x",
 extra=0, extra_note="32 GB storage built in", free_records=True,
 sub=4.99, sub_name="EZVIZ CloudPlay 7-day",
 best="Two cameras on a budget, with storage built in",
 catch="Expert Reviews found its motion detection unreliable and the app confusing.",
 storage="32 GB built in, no card needed", live="Yes", alerts="Yes",
 ai="Free: human and package detection", history="Yes, on built-in storage",
 paywalled="Nothing essential. CloudPlay is optional",
 sub_text="Optional CloudPlay. EZVIZ publishes UK prices only in its app; the €4.99/month (7 days) shown is its EU price",
 ha_text="Official integration, but it goes through EZVIZ's cloud; this battery model isn't named in its supported list.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=0),
 src=["chester_ep3x","ezviz_ep3x","ezviz_blog","er_tapo","ezviz_cloud","ezviz_terms","ha_ezviz"],
 rec_src="ezviz_ep3x", history_src="ezviz_blog", ha_src="ha_ezviz", plan_src="ezviz_cloud", plan_price_region="EU", unverified=""),
dict(cat="doorbells", id="ezviz-db2", brand="EZVIZ", model="DB2 Pro Kit", rec="yes", power=["battery"], ha=0,
 price=114.99, price_note="ER Tech, UK retailer", price_src="ertech_db2",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=4.99, sub_name="EZVIZ CloudPlay 7-day",
 best="Flats and rentals: no wiring, and footage stays indoors in the chime",
 catch="2.4 GHz Wi-Fi only, and the card is sold separately.",
 storage="microSD (up to 256 GB) in the included indoor chime", live="Yes", alerts="Yes",
 ai="Free: PIR plus human-shape detection", history="Yes, on the chime's card", paywalled="Nothing essential",
 sub_text="Optional CloudPlay. EZVIZ publishes UK prices only in its app; the €4.99/month (7 days) shown is its EU price",
 ha_text="Official integration, but it goes through EZVIZ's cloud; this battery model isn't named in its supported list.",
 wifi="2.4 GHz only",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["ertech_db2","ezviz_blog","ezviz_cloud","ezviz_terms","ha_ezviz","sandisk_card"],
 rec_src="ertech_db2", history_src="ertech_db2", ha_src="ha_ezviz", plan_src="ezviz_cloud", plan_price_region="EU", unverified=""),
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
 price=79.99, price_note="Reolink UK store", price_src="reo_gb_home",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A wired install on a budget: 4K for £80, with nothing held back",
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
 price=144.49, price_note="Reolink UK store, 1 camera with a Solar Panel 2", price_src="reo_gb_home",
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
dict(cat="cameras", id="reo-altas", brand="Reolink", model="Altas PT Ultra", rec="yes", power=["battery"], ha=2,
 power_note="The battery lasts up to 500 days in PIR mode, or 96 hours recording continuously.",
 price=152.99, price_note="Reolink UK store, 1 camera with a Solar Panel 2", price_src="reo_altas",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A gate or yard watched all day: 4K pan-tilt with 96 hours of continuous recording",
 catch="The card is extra, and continuous recording empties the battery in about four days without sun.",
 storage="microSD (up to 512 GB) or a Reolink Home Hub; card not included", live="Yes", alerts="Yes",
 ai="Free: person, vehicle and animal detection on the device",
 history="Yes, motion clips or scheduled continuous recording on a card or Home Hub",
 paywalled="Nothing. Reolink Cloud is optional",
 sub_text="None needed. Reolink records to a microSD card or Home Hub; Reolink Cloud is optional",
 ha_text="Official, fully local integration. Battery cameras wake on a PIR event, so some entities update on a schedule.",
 wifi="Dual-band 2.4/5 GHz (Wi-Fi 6)",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=2),
 src=["reo_altas","ha_reo","sandisk_card"],
 rec_src="reo_altas", history_src="reo_altas", ha_src="ha_reo", plan_src="reo_altas", unverified=""),
dict(cat="cameras", id="reo-arguspt", brand="Reolink", model="Argus PT Ultra", rec="yes", power=["battery"], ha=2,
 power_note="The 3W solar panel in the box keeps it charged on 20 minutes of sun a day.",
 price=118.99, price_note="Reolink UK store, 1 camera with a Solar Panel (was £139.99)", price_src="reo_gb_home",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A garden corner on a budget: 4K pan and tilt for £119, with nothing held back",
 catch="The card is extra, and the 3W solar panel has to keep a pan-tilt head charged all year.",
 storage="microSD (up to 512 GB) or a Reolink Home Hub; card not included", live="Yes", alerts="Yes",
 ai="Free: person, vehicle and animal detection on the device",
 history="Yes, motion-triggered clips on a card or Home Hub",
 paywalled="Nothing. Reolink Cloud is optional",
 sub_text="None needed. Reolink records to a microSD card or Home Hub; Reolink Cloud is optional",
 ha_text="Official, fully local integration. Battery cameras wake on a PIR event, so some entities update on a schedule.",
 wifi="Dual-band 2.4/5 GHz (Wi-Fi 6)",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=2),
 src=["reo_gb_home","reo_arguspt","ha_reo","sandisk_card"],
 rec_src="reo_arguspt", history_src="reo_arguspt", ha_src="ha_reo", plan_src="reo_arguspt", unverified=""),
dict(cat="cameras", id="tapo-c660", brand="TP-Link Tapo", model="C660 KIT", rec="yes", power=["battery"], ha=0,
 power_note="It can also charge over USB-C.",
 price=109.99, price_note="Tapo UK sale price (RRP £179.99)", price_src="tapo_c660",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=2.99, sub_name="Tapo Care",
 best="A sunny wall with no socket: 4K, solar and a card slot",
 catch="Not on Home Assistant's supported Tapo camera list, and the card is extra.",
 storage="microSD (up to 512 GB) on the camera; card not included", live="Yes", alerts="Yes",
 ai="Free: person, pet and vehicle detection on the device",
 history="Yes, event clips on the card; 24/7 recording with a card",
 paywalled="30-day cloud history, rich notifications, Smart Sort",
 sub_text="Optional Tapo Care £2.99/month or £29.49/year (1 camera)",
 ha_text="Home Assistant's local TP-Link integration lists the C520WS and other Tapo cameras, but not this C660 KIT. Tapo also lists no RTSP or ONVIF for it, so treat live view as unsupported.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["tapo_c660","tapo_care","ha_tplink","sandisk_card"],
 rec_src="tapo_c660", history_src="tapo_c660", ha_src="ha_tplink", plan_src="tapo_care",
 unverified=""),
dict(cat="cameras", id="tapo-c675d", brand="TP-Link Tapo", model="C675D KIT", rec="yes", power=["battery"], ha=0,
 power_note="The 10,000 mAh battery lasts up to three months, and the solar panel is in the box.",
 price=189.99, price_note="Tapo UK sale price (RRP £239.99)", price_src="tapo_c675d",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=2.99, sub_name="Tapo Care",
 best="Two views from one camera: a 169° wide lens and a 4K pan-tilt zoom",
 catch="It has no RTSP or ONVIF, so Home Assistant cannot pull the stream, and the card is extra.",
 storage="microSD (up to 512 GB) on the camera; card not included", live="Yes", alerts="Yes",
 ai="Free: person, pet and vehicle detection on the device",
 history="Yes, event clips on the card; 24/7 capture with a card",
 paywalled="30-day cloud history, rich notifications, Smart Sort",
 sub_text="Optional Tapo Care £2.99/month or £29.49/year (1 camera)",
 ha_text="Tapo lists no RTSP or ONVIF support for this model, so Home Assistant has no local stream.",
 wifi="Dual-band 2.4/5 GHz",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=0),
 src=["tapo_c675d","tapo_care","sandisk_card"],
 rec_src="tapo_c675d", history_src="tapo_c675d", ha_src="tapo_c675d", plan_src="tapo_care", unverified=""),
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
 price=69.99, price_note="eufy UK list price; an £18 coupon was advertised", price_src="eufy_e30",
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
 price=119.99, price_note="Aqara UK Shop", price_src="aqara_g3",
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
 price=55.99, price_note="Aqara UK Shop sale price (RRP £69.98)", price_src="aqara_e1",
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
dict(cat="cameras", id="aqara-g100", brand="Aqara", model="Camera G100 Select", rec="yes", power=["wired"], ha=1,
 price=36.98, price_note="Aqara UK Shop sale price (RRP £41.99)", price_src="aqara_g100",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A shed or a back door watched cheaply",
 catch="The card is extra, the power adapter is not in the box, and the better detection needs a subscription.",
 storage="microSD (up to 512 GB), or an SMB NAS", live="Yes", alerts="Yes",
 ai="Free: on-device motion and human detection",
 history="Yes, on the card",
 paywalled="Nothing essential. Aqara's HomeGuardian plan adds face, vehicle, pet and package detection and cloud history",
 sub_text="None needed. The camera records to a card; HomeGuardian is optional",
 ha_text="Streams to Home Assistant over RTSP, which is local; Aqara names RTSP rather than an official Home Assistant integration.",
 wifi="2.4 GHz Wi-Fi 6",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["aqara_g100","sandisk_card"],
 rec_src="aqara_g100", history_src="aqara_g100", ha_src="aqara_g100", plan_src="aqara_g100",
 unverified=""),
dict(cat="cameras", id="aqara-g5pro", brand="Aqara", model="Camera Hub G5 Pro (Wi-Fi 32GB)", rec="yes", power=["wired"], ha=1,
 price=169.99, price_note="Aqara UK Shop sale price (RRP £199.99)", price_src="aqara_g5pro",
 extra=0, extra_note="32 GB storage built in", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A local hub camera: 2.6K, 32 GB on board, and Zigbee, Thread and Matter built in",
 catch="Only 2.6K, and the 32 GB cannot be expanded without a NAS.",
 storage="32 GB built in; no card slot, and a NAS can hold more", live="Yes", alerts="Yes",
 ai="Free: on-device face, person, vehicle, animal and package detection",
 history="Yes, 24–28 hours of event recording on the 32 GB, or a NAS",
 paywalled="Aqara cloud storage with HomeGuardian; the camera records locally without it",
 sub_text="None needed. Aqara's cloud storage is optional",
 ha_text="Aqara publishes RTSP support for Home Assistant and HomeKit; the stream is local, and the hub can also bridge Zigbee and Thread devices.",
 wifi="Dual-band 2.4/5 GHz (Wi-Fi 5)",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=1,ha=1),
 src=["aqara_g5pro"],
 rec_src="aqara_g5pro", history_src="aqara_g5pro", ha_src="aqara_g5pro", plan_src="aqara_g5pro", unverified=""),
dict(cat="cameras", id="aqara-g350", brand="Aqara", model="Camera Hub G350 Select", rec="yes", power=["wired"], ha=1,
 price=125.99, price_note="Aqara UK Shop sale price, on back-order (RRP £139.99)", price_src="aqara_g350",
 extra=CARD, extra_note="+ SanDisk 64 GB microSD card", extra_src="sandisk_card", free_records=True,
 sub=None, sub_name="No plan needed",
 best="A room with a lot to cover: 4K wide plus a 2.5K zoom lens on a 360° mount",
 catch="Indoor only, and the card is extra.",
 storage="microSD (up to 512 GB); card not included", live="Yes", alerts="Yes",
 ai="Free: on-device person, pet, face and sound detection",
 history="Yes, event clips on the card; 24/7 recording with a card",
 paywalled="Aqara cloud storage with HomeGuardian; the camera records locally without it",
 sub_text="None needed. Aqara's cloud storage is optional",
 ha_text="Aqara says Home Assistant integration is streaming only over RTSP; the camera's AI and pan-tilt controls stay in Aqara's app.",
 wifi="Dual-band 2.4/5 GHz (Wi-Fi 6)",
 score=dict(rec=2,live=1,alerts=1,ai=1,storage=0,ha=1),
 src=["aqara_g350","sandisk_card"],
 rec_src="aqara_g350", history_src="aqara_g350", ha_src="aqara_g350", plan_src="aqara_g350", unverified=""),
dict(cat="cameras", id="ring-outpro", brand="Ring", model="Outdoor Camera 4K Pro (plug-in)", rec="no", power=["wired"], ha=0,
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
dict(cat="cameras", id="ring-outplus", brand="Ring", model="Outdoor Camera Plus (plug-in)", rec="no", power=["wired"], ha=0,
 price=89.99, price_note="Ring UK", price_src="ring_plus",
 extra=0, extra_note="", free_records=False,
 sub=4.99, sub_name="Ring Solo",
 best="Ring's live view and alerts for £90, if you never want the footage",
 catch="Saves no video at all without the £4.99-a-month plan, and the picture is 2K rather than 4K.",
 storage="None. Recording is cloud-only.", live="Yes", alerts="Yes",
 ai="Paid (person, package and vehicle alerts on Ring's plans)",
 history="None", paywalled="All recording and playback (up to 180 days) and smart alerts",
 sub_text="Ring Solo £4.99/month or £49.99/year (1 device). Multi £7.99, Pro £15.99",
 ha_text="Official integration, but it goes through Ring's cloud. No local-only option.",
 wifi="Dual-band 2.4/5 GHz (Wi-Fi 6)",
 score=dict(rec=0,live=1,alerts=1,ai=0,storage=0,ha=0),
 src=["ring_plus","ring_plans","ha_ring"],
 rec_src="ring_plus", history_src="ring_plus", ha_src="ha_ring", plan_src="ring_plans", unverified=""),
dict(cat="cameras", id="blink-out4", brand="Blink", model="Outdoor 4", rec="kit", power=["battery"], ha=0,
 price=69.99, price_note="Amazon UK, includes a Sync Module Core (which has no local storage)", price_src="amz_blink_cam", buy="amz_blink_cam",
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
dict(cat="cameras", id="blink-out2k", brand="Blink", model="Outdoor 2K+", rec="kit", power=["battery"], ha=0,
 price=89.99, price_note="Amazon UK, includes a Sync Module Core (which has no local storage)", price_src="amz_blink_2kp", buy="amz_blink_2kp", price_check=True,
 extra=round(39.99 + STICK, 2), extra_note="+ Sync Module 2 £39.99 + SanDisk 64 GB USB stick",
 extra_src="sandisk_stick", kit_src="amz_sm2", kit_label="Sync Module 2", kit_price=39.99, free_records=True,
 sub=2.50, sub_name="Blink Basic",
 best="A 2K picture from Amazon's cameras, if you will add the module anyway",
 catch="Records nothing until you add a Sync Module 2 and a USB stick, and Blink's two-year battery figure is at 1080p.",
 storage="Through a Sync Module 2 and a USB stick (1–256 GB), both sold separately; neither the camera nor the Sync Module Core in the box holds a clip",
 live="Capped at 5 minutes", alerts="Yes", ai="Paid (person and vehicle detection)",
 history="None without a Sync Module 2",
 paywalled="Cloud clips, person/vehicle detection, 90-minute live view, AI descriptions",
 sub_text="Blink Basic £2.50/month (£24.99/year); Plus £8/month; Basic AI £5.49/month",
 ha_text="Official integration, but it goes through Blink's cloud and has no live view.",
 wifi="2.4 GHz only",
 score=dict(rec=1,live=0,alerts=1,ai=0,storage=0,ha=0),
 src=["amz_blink_2kp","blink_2kp_specs","amz_sm2","blink_storage","blink_plans","blink_sm2","blink_liveview","ha_blink","sandisk_stick"],
 rec_src="blink_storage", history_src="blink_storage", ha_src="ha_blink", plan_src="blink_plans", unverified=""),
dict(cat="cameras", id="blink-mini4k", brand="Blink", model="Mini 4K+", rec="kit", power=["wired"], ha=0,
 power_note="Plug-in only; outdoor use needs Blink's weather-resistant power adapter, sold separately.",
 price=69.99, price_note="Amazon UK, 1 camera", price_src="amz_blink_mini4k", buy="amz_blink_mini4k", price_check=True,
 extra=round(39.99 + STICK, 2), extra_note="+ Sync Module 2 £39.99 + SanDisk 64 GB USB stick",
 extra_src="sandisk_stick", kit_src="amz_sm2", kit_label="Sync Module 2", kit_price=39.99, free_records=True,
 sub=2.50, sub_name="Blink Basic",
 best="Blink's sharpest picture, for a socket near a window or door",
 catch="Records nothing until you add a Sync Module 2 and a USB stick, outdoor use needs a separate adapter, and live view stops at 5 minutes.",
 storage="Only through a Sync Module 2 + USB stick (1–256 GB); the camera has no storage",
 live="Capped at 5 minutes", alerts="Yes", ai="Paid (person and vehicle detection)",
 history="None without a Sync Module 2",
 paywalled="Cloud clips, person/vehicle detection, 90-minute live view, AI descriptions",
 sub_text="Blink Basic £2.50/month (£24.99/year); Plus £8/month; Basic AI £5.49/month",
 ha_text="Official integration, but it goes through Blink's cloud and has no live view.",
 wifi="Dual-band 2.4/5 GHz (Wi-Fi 6)",
 score=dict(rec=1,live=0,alerts=1,ai=0,storage=0,ha=0),
 src=["amz_blink_mini4k","blink_mini4k_specs","amz_sm2","blink_storage","blink_plans","blink_sm2","blink_liveview","ha_blink","sandisk_stick"],
 rec_src="blink_storage", history_src="blink_storage", ha_src="ha_blink", plan_src="blink_plans", unverified=""),
# A ring has no recording and no recorder, so its sums are the price and, where
# the vendor charges one, the membership. `free_records` is the same decision
# as before: does the product give its data with no plan? `power` buckets the
# vendor's battery figure, and `wifi` carries the phones it works with.
dict(cat="rings", id="oura-5", brand="Oura", model="Ring 5", rec="brief", power=["nine"], ha=1,
 offers=[
  dict(shop="Oura", src="oura_store5", price=399.00, pay=PAY_RETAIL,
        note="Silver; the gold and rose finishes are £499"),
  dict(shop="Argos", src="argos_oura5", price=399.00, pay=PAY_RETAIL, note="Silver, size 8"),
  dict(shop="Currys", src="currys_oura5", price=399.00, pay=PAY_RETAIL, note="Silver, size 8"),
 ],
 extra=0, extra_note="", free_records=False,
 sub=5.99, sub_name="Oura Membership",
 best="The current Oura, if the newest sensors are worth the membership to you",
 catch="Only three daily scores work without the £5.99 membership, it costs more than the Ring 4, and Oura's sizing differs from its other rings.",
 storage="Oura's cloud. Oura lets you download your data from the Membership Hub even without a plan.",
 live="No. 24/7 heart rate is part of the membership.",
 alerts="No. Wellness alerts are part of the membership.",
 ai="No. Only the three daily scores are free. Sleep stages, HRV, SpO2 and temperature need the membership.",
 history="Three daily scores only. Sleep stages, HRV, SpO2 and trends need the membership.",
 paywalled="Detailed sleep stages, 24/7 heart rate and HRV, SpO2, temperature, stress, cardiovascular age, VO2 max, women's health, reports and the API",
 sub_text="Oura Membership £5.99/month or £69.99/year after tax. The first month is free",
 ha_text="A community HACS integration brings the ring's data into Home Assistant through Oura's cloud API. Oura blocks API access without an active membership, so the integration needs the plan too.",
 wifi="iPhone and Android",
 power_note="Oura quotes 6 to 9 days, depending on use.",
 score=dict(rec=1,sleep=0,hr=0,spo2=0,extra=0,ha=1),
 src=["oura_store5","argos_oura5","currys_oura5","oura_membership","oura_free","ha_oura"],
 rec_src="oura_free", history_src="oura_free", ha_src="ha_oura", plan_src="oura_membership",
 nosub_say="£399 buys the ring. Without the membership only three daily scores work.", unverified=""),
dict(cat="rings", id="oura-4", brand="Oura", model="Ring 4", rec="brief", power=["eight"], ha=1,
 offers=[
  dict(shop="Argos", src="argos_oura4", price=244.00, pay=PAY_RETAIL, note="Silver, size 6"),
  dict(shop="Amazon UK", src="amz_oura4", price=244.00, pay=PAY_AMAZON,
        note="Silver, size 9; other sizes and finishes differ"),
 ],
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
 src=["amz_oura4","argos_oura4","oura_membership","oura_free","ha_oura"],
 rec_src="oura_free", history_src="oura_free", ha_src="ha_oura", plan_src="oura_membership",
 nosub_say="£244 buys the ring. Without the membership only three daily scores work.", unverified=""),
dict(cat="rings", id="ultra-air", brand="Ultrahuman", model="Ring AIR", rec="yes", power=["six"], ha=1,
 offers=[
  dict(shop="Argos", src="argos_ultra", price=329.00, pay=PAY_RETAIL, note="Aster Black, size 9"),
  dict(shop="Amazon UK", src="amz_ultra", price=329.00, pay=PAY_AMAZON, note="as listed"),
 ],
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
 wifi="iPhone (iOS 15+) and Android (6+)",
 score=dict(rec=2,sleep=1,hr=1,spo2=0,extra=1,ha=1),
 src=["amz_ultra","argos_ultra","uh_ring","uh_nosub","uh_faq","ha_ultra"],
 rec_src="uh_nosub", history_src="uh_ring", ha_src="ha_ultra", plan_src="uh_nosub",
 nosub_say="No subscription. The ring and its data are the whole cost.",
 unverified=""),
dict(cat="rings", id="ultra-pro", brand="Ultrahuman", model="Ring PRO", rec="yes", power=["fifteen"], ha=0,
 price=429.00, price_note="Ultrahuman UK, Bionic Gold with sizing kit", price_src="ultra_pro",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="The most capable Ultrahuman: a 15-day ring and a charger that stores a year of data",
 catch="AFib detection is a £49/year add-on, it costs £100 more than the Ring AIR, and Home Assistant support for the PRO is undocumented.",
 storage="Ultrahuman's cloud, plus up to 250 days on the ring and a year in the PRO charger.",
 live="Yes, in the app.", alerts="Yes, recovery and movement nudges.",
 ai="Free: sleep stages, HRV, SpO2, skin temperature, stress, recovery, cycle and Ultra Age insights. AFib detection is a paid PowerPlug.",
 history="Yes, full history in the app.",
 paywalled="Nothing needed for the core data. AFib Detection is a £49/year PowerPlug; Cycle & Ovulation Pro is £29.99/year",
 sub_text="No subscription. The ring's data is free in the app. Ultrahuman Max is an optional extra",
 plan_say="No subscription. The ring's data is free in the app. Ultrahuman Max is an optional extra.",
 ha_text="No official integration. The community Ultrahuman HACS integration documents Ring AIR, and Ultrahuman does not confirm it works with the PRO.",
 wifi="iPhone and Android",
 power_note="Ultrahuman quotes up to 15 days on the ring, and up to 45 days with the PRO charger.",
 score=dict(rec=2,sleep=1,hr=1,spo2=1,extra=1,ha=0),
 src=["ultra_pro","uh_pro","uh_nosub","ha_ultra"],
 rec_src="uh_nosub", history_src="uh_pro", ha_src="ha_ultra", plan_src="uh_nosub",
 nosub_say="No subscription. The ring and its data are the whole cost.",
 unverified=""),
dict(cat="rings", id="rc-2", brand="RingConn", model="Gen 2", rec="yes", power=["twelve"], ha=0,
 offers=[
  dict(shop="Argos", src="argos_rc2", price=259.00, pay=PAY_RETAIL,
        note="Matte Black, size 7"),
  dict(shop="Amazon UK", src="amz_rc2", price=259.00, pay=PAY_AMAZON, note="as listed"),
  dict(shop="Currys", src="currys_rc2", price=259.00, pay=PAY_RETAIL,
        note="Matte Black, size 7"),
 ],
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="The best value RingConn: 12 days, sleep-apnea insights and no subscription",
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
 src=["amz_rc2","argos_rc2","currys_rc2","rc2_product","rc_nosub","ha_index"],
 rec_src="rc_nosub", history_src="rc2_product", ha_src="ha_index", plan_src="rc_nosub",
 nosub_say="No subscription. The ring and its data are the whole cost.", unverified=""),
dict(cat="rings", id="rc-2-air", brand="RingConn", model="Gen 2 Air", rec="yes", power=["ten"], ha=0,
 price=179.00, price_note="Amazon UK", price_src="amz_rc2a", buy="amz_rc2a", price_check=True,
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="A RingConn without the sleep-apnea, vascular or vibration extras",
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
 price=309.00, price_note="Amazon UK", price_src="amz_rc3", buy="amz_rc3", price_check=True,
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
 offers=[
  dict(shop="Currys", src="currys_samsung", price=150.97, pay=PAY_RETAIL,
        note="Titanium Gold, size 14; every other size is £399"),
  dict(shop="Amazon UK", src="amz_samsung", price=399.00, pay=PAY_AMAZON,
        note="Titanium Black, size 7"),
 ],
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
 src=["amz_samsung","currys_samsung","samsung_support","ha_index"],
 rec_src="amz_samsung", history_src="samsung_support", ha_src="ha_index", plan_src="amz_samsung",
 nosub_say="No subscription. The ring and its data are the whole cost.", unverified=""),
dict(cat="rings", id="amazfit-helio", brand="Amazfit", model="Helio Ring", rec="yes", power=["four"], ha=0,
 price=149.90, price_note="Amazfit UK sale price, RRP £269", price_src="amazfit_uk",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="The cheapest smart ring, with no subscription for the basics",
 catch="Only three sizes, and Aura's advanced sleep coaching is a paid extra.",
 storage="Zepp's cloud. The phone app holds the history.",
 live="Yes, in Zepp.",
 alerts="Yes, through Zepp notifications.",
 ai="Free: sleep stages, resting heart rate, HRV, SpO2, temperature, stress and readiness.",
 history="Yes, in Zepp.",
 paywalled="Nothing for the core data. Zepp Aura's advanced sleep reports and unlimited AI assistant are optional paid extras",
 sub_text="No subscription for the ring's data. Zepp Aura is free for Helio Ring users on a trial, with premium plans priced in dollars on Amazfit's UK page", plan_say="No subscription for the ring's data. Zepp Aura is an optional paid extra.",
 ha_text="No official integration. A community Zepp bridge exists for watches, but it is not confirmed for this ring.",
 wifi="iPhone and Android (minimum versions not stated)",
 score=dict(rec=2,sleep=1,hr=1,spo2=1,extra=1,ha=0),
 src=["amazfit_uk","amazfit_aura","ha_zepp"],
 rec_src="amazfit_uk", history_src="amazfit_uk", ha_src="ha_zepp", plan_src="amazfit_uk",
 nosub_say="No subscription for the ring's data. Zepp Aura is optional.",
 unverified=""),
# ---------- pet trackers ----------
# A "no subscription" tracker is one of three things, and the row says which:
# data included with the price, a plan that is required, or a Bluetooth tag with
# no GPS at all. The monthly plan is the basis of the with-plan sum, so a yearly
# plan that is cheaper is named in the method rather than quietly used.
dict(cat="pet-trackers", id="pitpat-gps", brand="PitPat", model="Dog GPS Tracker", rec="yes", power=["included"], ha=1,
 price=149.00, price_note="PitPat UK", price_src="pitpat_product",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No PitPat plan",
 best="A dog owner who wants tracking and saved walks without any monthly fee",
 catch="The dearest tracker here, it has no geofencing, and the optional LIFE plan adds Video Vet and loss replacement.",
 storage="PitPat's specification says up to 6 weeks; its product page says several days",
 live="About every 10 seconds once live tracking is started",
 alerts="None. PitPat says it does not offer geofencing",
 ai="Walks are saved in the app without LIFE; PitPat's own comparison ticks saved walks for tracker-only and LIFE",
 history="Live tracking and saved walks, with no plan",
 paywalled="Video Vet and loss replacement are the LIFE extras; tracking and saved walks are not",
 sub_text="None needed. Optional PitPat LIFE is £3.99/month for Video Vet and loss replacement",
 ha_text="PitPat's FAQ says the tracker can be used on cats, though it is sold for dogs. 30 g and 60 × 34 × 18 mm.",
 wifi="iOS and Android app; no web or tablet access",
 score=dict(rec=2,gps=1,live=1,history=1,area=0,ha=1),
 src=["pitpat_product","pitpat_spec","pitpat_life","pitpat_terms","pitpat_faqs"],
 rec_src="pitpat_terms", history_src="pitpat_life", ha_src="pitpat_faqs", plan_src="pitpat_life", unverified=""),
dict(cat="pet-trackers", id="pawva-x01-plus", brand="PAWVA", model="X01+", rec="yes", power=["fixed"], ha=0,
 price=77.99, price_note="PAWVA UK", price_src="pawva_x01",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No PAWVA plan",
 best="The cheapest way to get GPS tracking with no monthly fee",
 catch="PAWVA's pages disagree on the SIM term: five years in its bundle FAQ, ten on the X01+ page.",
 storage="Up to 5 days with 10-minute Smart Interval updates",
 live="Every 30 seconds or less in Precision mode; every 10 minutes in battery saver",
 alerts="Geofencing and escape alerts included",
 ai="Historical tracks and playback, with no retention period published",
 history="Location and history with no plan, for the included SIM term",
 paywalled="Nothing for tracking; the length of the data term is the promise to watch",
 sub_text="None needed. The X01+ page advertises 10-year connectivity; PAWVA's bundle FAQ says the X01+ has a five-year prepaid SIM",
 ha_text="Sold for dogs. PAWVA gives no X01+ weight or cat claim; the 82 g figure on its bundle page is for the X01.",
 wifi="iOS and Android app",
 score=dict(rec=2,gps=1,live=1,history=1,area=1,ha=0),
 src=["pawva_x01","pawva_x05","pawva_bundle","pawva_home","ofcom_3g"],
 rec_src="pawva_x01", history_src="pawva_home", ha_src="pawva_x01", plan_src="pawva_bundle",
 unverified=""),
dict(cat="pet-trackers", id="tractive-dog-6", brand="Tractive", model="DOG 6", rec="no", power=["plan"], ha=0,
 price=59.00, price_note="Tractive UK", price_src="tractive_dog6",
 extra=0, extra_note="", free_records=False, sub=13.50, sub_name="Tractive Basic, monthly",
 best="The fastest live updates, if you will pay for a plan",
 catch="Nothing works without a plan, Basic covers one country, and the 14-day battery needs Power Saving Zones.",
 storage="Up to 14 days with Power Saving Zones; up to 6 days without",
 live="Every 2 to 3 seconds in LIVE Tracking; every 2 to 60 minutes otherwise",
 alerts="Virtual fences and escape alerts, included with the plan",
 ai="24 hours of history on Basic; 365 days on Premium",
 history="Nothing without a plan. Basic keeps 24 hours of history",
 paywalled="Tracking itself. Premium adds 365-day history, family sharing and 175+ countries",
 sub_text="Basic £13.50/month, or £7/month billed yearly (£84 a year), £4.50/month over two years or £4/month over five. Premium adds 365-day history and more countries",
 ha_text="Dogs above 4 kg; Tractive sells the separate CAT 6 Mini for cats. 39 g and 71 × 29 × 17 mm.",
 wifi="iOS 17+ and Android 10+ app; no web app published",
 score=dict(rec=0,gps=1,live=1,history=0,area=0,ha=0),
 src=["tractive_dog6","tractive_plans","tractive_premium","tractive_app"],
 rec_src="tractive_dog6", history_src="tractive_premium", ha_src="tractive_dog6", plan_src="tractive_plans", unverified=""),
dict(cat="pet-trackers", id="tractive-cat-6-mini", brand="Tractive", model="CAT 6 Mini", rec="no", power=["plan"], ha=2,
 price=59.00, price_note="Tractive UK", price_src="tractive_cat6",
 extra=0, extra_note="", free_records=False, sub=13.50, sub_name="Tractive Basic, monthly",
 best="The best cat tracker if you will pay for a plan",
 catch="Nothing works without a plan, and the 7-day battery falls to 4 days without Power Saving Zones.",
 storage="Up to 7 days with Power Saving Zones; up to 4 days without",
 live="Every 2 to 3 seconds in LIVE Tracking; every 2 to 60 minutes otherwise",
 alerts="Virtual fences and escape alerts, included with the plan",
 ai="24 hours of history on Basic; 365 days on Premium",
 history="Nothing without a plan. Basic keeps 24 hours of history",
 paywalled="Tracking itself. Premium adds 365-day history and 175+ countries",
 sub_text="Basic £13.50/month, or £7/month billed yearly (£84 a year), £4.50/month over two years or £4/month over five. Premium adds 365-day history and more countries",
 ha_text="Cats from 3 to 8 kg, with a neck of 19 to 22.9 cm. 32 g including the collar.",
 wifi="iOS 17+ and Android 10+ app; no web app published",
 score=dict(rec=0,gps=1,live=1,history=0,area=0,ha=2),
 src=["tractive_cat6","tractive_plans","tractive_premium","tractive_app"],
 rec_src="tractive_cat6", history_src="tractive_premium", ha_src="tractive_cat6", plan_src="tractive_plans", unverified=""),
dict(cat="pet-trackers", id="weenect-xt", brand="Weenect", model="XT", rec="no", power=["plan"], ha=0,
 price=44.99, price_note="Weenect UK", price_src="weenect_xt",
 extra=0, extra_note="", free_records=False, sub=13.00, sub_name="Weenect monthly",
 best="The fastest live updates and the longest plan history",
 catch="A plan is required, the charger is not included, and at 54 g it is the heaviest tracker here.",
 storage="Up to 3 weeks with power-saving areas; about 7 days of continuous tracking",
 live="Every second in live mode; every 30 seconds to 60 minutes otherwise",
 alerts="Safety zones and escape alerts, included with the subscription",
 ai="30 days of history, included with every plan",
 history="Nothing without a plan. Every plan keeps 30 days of history",
 paywalled="Tracking itself. The plan includes live tracking and 30 days of history",
 sub_text="£13/month, or £80 a year (£6.67/month), £110 for two years (£4.59/month) or £220 for five (£3.67/month)",
 ha_text="Sold for dogs of any size; Weenect's XT page does not state cat suitability. 54 g and 82 × 35 × 22 mm.",
 wifi="iOS 15+, Android 6+ and a web app",
 score=dict(rec=0,gps=1,live=1,history=0,area=0,ha=0),
 src=["weenect_xt","weenect_subs","weenect_support","weenect_coverage"],
 rec_src="weenect_xt", history_src="weenect_subs", ha_src="weenect_xt", plan_src="weenect_support",
 unverified=""),
dict(cat="pet-trackers", id="pawfit-3", brand="Pawfit", model="Pawfit 3", rec="no", power=["plan"], ha=1,
 price=54.99, price_note="Amazon UK, list price; Pawfit's own sale was £46.74", price_src="amz_pawfit",
 extra=0, extra_note="", free_records=False, sub=9.99, sub_name="Pawfit Basic, monthly",
 best="A cheaper plan for a dog or a larger cat",
 catch="A plan is required, Basic keeps only 24 hours of history, and the 5-second updates are FIND mode only.",
 storage="Up to 8 days",
 live="Every 5 seconds in FIND mode; about every 1 to 2 minutes when moving",
 alerts="24/7 Safety Zone alerts, included with the plan",
 ai="24 hours of location history on Basic",
 history="Nothing without a plan. Basic keeps 24 hours of history",
 paywalled="Tracking itself. Premium adds six-hour walks, Ordnance Survey maps and longer history",
 sub_text="Basic £9.99/month, £71.88/year or £95.76 for two years. Premium £83.88/year, £119.76 for two years or £143.64 for three",
 ha_text="Dogs and cats over 3.5 kg. 27 g and 48 × 33 × 14 mm.",
 wifi="iOS and Android app",
 score=dict(rec=0,gps=1,live=1,history=0,area=0,ha=1),
 src=["pawfit_3","pawfit_plans","pawfit_compare","amz_pawfit"],
 rec_src="pawfit_3", history_src="pawfit_3", ha_src="pawfit_compare", plan_src="pawfit_plans", unverified=""),
dict(cat="pet-trackers", id="apple-airtag-2", brand="Apple", model="AirTag (2nd generation)", rec="tag", power=["tag"], ha=2,
 price=29.00, price_note="Apple UK, one pack", price_src="apple_airtag_buy",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No Apple plan",
 best="A cat that stays close to other people's phones",
 catch="Not a GPS tracker: it only reports when a nearby Find My device hears it, needs an iPhone, and has no history or safe zones.",
 storage="More than a year on a replaceable CR2032 battery",
 live="No fixed interval. It reports when a nearby Find My device hears it",
 alerts="No safe-zone or escape alerts",
 ai="No route history; Apple says location data is not stored on the AirTag",
 history="Location checks through Find My, whenever a nearby Apple device hears it",
 paywalled="Nothing. There is no subscription",
 sub_text="None. It uses the Find My network, with no data plan",
 ha_text="11.8 g and 32 mm across, but it needs a collar holder, which Apple does not sell. Android phones cannot locate it.",
 wifi="Find My on iPhone and iPad; Android only receives unwanted-tracking alerts",
 score=dict(rec=1,gps=0,live=0,history=0,area=0,ha=2),
 src=["apple_airtag","apple_airtag_buy"],
 rec_src="apple_airtag", history_src="apple_airtag", ha_src="apple_airtag", plan_src="apple_airtag", unverified=""),
# ---------- baby monitors ----------
# The split is the connection, not the price: a local radio monitor sends
# nothing outside the house, a hybrid adds an optional app, and a Wi-Fi monitor
# has no parent unit at all. The free tier is what the no-plan sum buys.
dict(cat="baby-monitors", id="vtech-vm4263", brand="VTech", model="VM4263", rec="yes", power=["radio"], ha=2,
 price=59.99, price_note="Mamas & Papas sale (was £69.99); Argos £70", price_src="mamas_vm4263",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="A parent unit-only monitor on a budget",
 catch="Local only: no phone viewing or recording, and it cannot take a second camera.",
 storage="Nowhere. The camera talks only to the parent unit",
 live="3.5-inch colour screen, infrared night vision",
 alerts="Sound and VOX alerts; room temperature shown",
 ai="None",
 history="Live view and alerts, with no plan or account",
 paywalled="Nothing",
 sub_text="None. No app, no account and no subscription",
 ha_text="No account and no app. The parent unit is the only screen.",
 wifi="Yes. The camera uses its own radio link, not Wi-Fi",
 score=dict(rec=2,local=1,video=1,alerts=1,record=0,ha=2),
 src=["vtech_vm4263","mamas_vm4263","argos_vm4263"],
 rec_src="vtech_vm4263", history_src="argos_vm4263", ha_src="argos_vm4263", plan_src="vtech_vm4263", unverified=""),
dict(cat="baby-monitors", id="philips-scd881", brand="Philips", model="Avent SCD881/05", rec="yes", power=["radio"], ha=2,
 price=109.99, price_note="Currys, Coral Cream; the /26 is the same monitor with an EU plug", price_src="currys_scd881",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="A private local monitor with a bigger screen",
 catch="A 2.8-inch screen, no app or recording, and Currys is the only UK shop found with the /05 in stock.",
 storage="Nowhere. A private 2.4 GHz link to the parent unit",
 live="2.8-inch colour screen, infrared night vision",
 alerts="Sound and VOX alerts, temperature alert",
 ai="None",
 history="Live view and alerts, with no plan or account",
 paywalled="Nothing",
 sub_text="None. No app, no account and no subscription",
 ha_text="No account and no app.",
 wifi="Yes. The parent unit pairs directly with the camera",
 score=dict(rec=2,local=1,video=1,alerts=1,record=0,ha=2),
 src=["philips_scd881","currys_scd881"],
 rec_src="philips_scd881", history_src="philips_scd881", ha_src="philips_scd881", plan_src="philips_scd881", unverified=""),
dict(cat="baby-monitors", id="philips-scd951", brand="Philips", model="Avent Connected SCD951/26", rec="yes", power=["hybrid"], ha=1,
 price=157.99, price_note="Amazon UK; Currys £213.99; Philips £219.99", price_src="amz_scd951",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="A parent unit at home and an app when you are out",
 catch="Remote viewing needs Wi-Fi and an account, the parent unit pairs only with the camera in the box, and nothing is recorded.",
 storage="Nowhere. Live video only, on the parent unit or in the app",
 live="4.3-inch colour screen, infrared night vision",
 alerts="Sound, motion and temperature alerts",
 ai="None",
 history="Live view and alerts on the parent unit, with no plan",
 paywalled="Nothing for live viewing. Remote viewing needs the app and a Wi-Fi connection",
 sub_text="None listed. Philips sells no plan for the SCD951",
 ha_text="The parent unit needs no account; the app does for remote viewing.",
 wifi="Yes. Philips says it sets up with or without Wi-Fi, and the parent unit uses a direct link",
 score=dict(rec=2,local=1,video=1,alerts=1,record=0,ha=1),
 src=["philips_scd951","amz_scd951","currys_scd951","philips_spec","philips_pairs","philips_manual"],
 rec_src="philips_scd951", history_src="philips_spec", ha_src="philips_spec", plan_src="philips_scd951",
 unverified=""),
dict(cat="baby-monitors", id="eufy-c10", brand="eufy", model="Baby Monitor C10", rec="yes", power=["hybrid"], ha=1,
 price=114.99, price_note="eufy UK", price_src="eufy_c10",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No subscription",
 best="A local screen with a card slot for recording",
 catch="The microSD card is not included, the camera is mains-only, and remote viewing needs the app.",
 storage="A microSD card in the camera, up to 128 GB, or the local parent unit",
 live="4.5-inch screen, 2K camera, infrared night vision",
 alerts="Motion, cry, sound and temperature alerts",
 ai="Cry detection; no breathing or movement sensing",
 history="Live view, alerts and card recording, with no plan",
 paywalled="Nothing. Recordings stay on the card",
 sub_text="None. eufy sells no subscription for the C10",
 ha_text="The parent unit works without an account; the app does for remote viewing.",
 wifi="Yes. The parent unit works with Wi-Fi off",
 score=dict(rec=2,local=1,video=1,alerts=1,record=1,ha=1),
 src=["eufy_c10"],
 rec_src="eufy_c10", history_src="eufy_c10", ha_src="eufy_c10", plan_src="eufy_c10", unverified=""),
dict(cat="baby-monitors", id="nanit-pro", brand="Nanit", model="Pro with wall mount", rec="part", power=["wifi"], ha=0,
 price=299.00, price_note="Nanit UK, Pro with wall mount", price_src="nanit_pro",
 extra=0, extra_note="", free_records=True, sub=10.00, sub_name="Nanit Memories",
 best="Sleep trends and breathing motion, if you will pay for the extras",
 catch="No parent screen, everything runs through the app and Nanit's servers, and history and sleep analytics need a plan.",
 storage="Nanit's cloud; the camera has no local storage",
 live="Phone or tablet app only, 1080p, infrared night vision",
 alerts="Sound and motion alerts free",
 ai="Breathing motion with the Breathing Wear band, sold separately",
 history="Live view, sound and motion alerts, temperature and humidity, with no plan",
 paywalled="Video history, sleep analytics and milestones. Sleep is under £10/month after three months free; Memories is £10/month or £120/year",
 sub_text="Sleep under £10/month after three free months; Memories £10/month or £120/year; Milestones £25/month or £300/year",
 ha_text="The app needs a Nanit account and an internet connection. There is no parent unit.",
 wifi="No. Live view needs Wi-Fi and the app",
 score=dict(rec=1,local=0,video=1,alerts=1,record=0,ha=0),
 src=["nanit_pro","nanit_memberships","nanit_breathing"],
 rec_src="nanit_pro", history_src="nanit_pro", ha_src="nanit_pro", plan_src="nanit_memberships",
 unverified=""),
dict(cat="baby-monitors", id="owlet-dream-sock", brand="Owlet", model="Dream Sock", rec="yes", power=["wifi"], ha=0,
 price=299.99, price_note="Owlet UK", price_src="owlet_sock",
 extra=0, extra_note="", free_records=True, sub=None, sub_name="No Owlet plan in the UK",
 best="Pulse and oxygen readings for a sleeping baby",
 catch="No video, the sock has to be worn, live readings need Wi-Fi, and Owlet360 is not sold in the UK.",
 storage="Owlet's cloud for the app; the base station holds the alert",
 live="No camera. Pulse rate and oxygen saturation in the app",
 alerts="Low-oxygen and pulse-rate alerts, free",
 ai="Sleep and waking trends; Owlet360 adds more",
 history="Live readings and alerts with no plan",
 paywalled="Nothing in the UK. Owlet360 is sold only in the US and South Africa, and live readings and alerts stay free",
 sub_text="Owlet360 is not sold in the UK; Owlet's support page lists the US and South Africa, though its UK page still points to the app. Live readings and alerts stay free",
 ha_text="The app needs an Owlet account and Wi-Fi for live readings; the base station alerts without it.",
 wifi="Partly. The base station alerts without Wi-Fi; the app needs it",
 score=dict(rec=2,local=1,video=0,alerts=1,record=0,ha=0),
 src=["owlet_sock","owlet_360","owlet_support"],
 rec_src="owlet_sock", history_src="owlet_sock", ha_src="owlet_sock", plan_src="owlet_support",
 unverified=""),
]

# A row's Amazon price and buy links carry the tag, so a new Amazon row is
# tagged without anyone remembering to. An Amazon page cited for a sundry
# stays a plain citation.
for _r in ROWS:
    _keys = [o["src"] for o in _r.get("offers", ())] + [_r.get("price_src"), _r.get("buy")]
    for _key in _keys:
        if _key:
            _name, _url = S[_key]
            S[_key] = (_name, amazon_tagged(_url))
for _key, _merchant in AWIN_MERCHANTS.items():
    _name, _url = S[_key]
    S[_key] = (_name, awin_tagged(_url, _merchant))

# The pages behind a paid link, read off the data rather than guessed from the
# address: an Awin click carries no Amazon tag, and a bot-generated regex over
# the URL is exactly how a paid link that is not Amazon went unmarked.
SPONSORED = frozenset(
    url for _, url in S.values()
    if url.startswith(AWIN_CLICK) or ("tag=" in url and "amazon.co.uk" in url)
)

# ---------- each row's verdict and its plain words ----------
# Authored beside the rows and attached to them below, so a row carries its own
# verdict and sentences by the time anything reads it.
VERDICT = {
    "canon-pixma-g3590": "best",
    "epson-et-2951": "fast",
    "brother-dcp-j1200w": "retail", "hp-envy-6520e": "avoid",
    "reo-poe": "best", "reo-wifi": "wired", "reo-batt": "easy", "reo-batt2": "batt",
    "tapo-d235": "easy", "ring": "avoid", "ring-4kpro": "avoid",
    "ring-wpro": "avoid", "ring-elite": "avoid",
    "blink": "avoid", "arlo": "avoid", "arlo-fhd": "avoid",
    "reo-rlc820a": "best", "reo-argus4": "batt", "reo-e1out": "ptz", "reo-altas": "continuous",
 "reo-arguspt": "ptz",
    "tapo-c660": "solar", "tapo-c675d": "dual",
    "aqara-g3": "indoor", "aqara-e1": "value", "aqara-g5pro": "hub", "aqara-g350": "pan",
    "ring-outpro": "avoid", "ring-outplus": "avoid", "blink-out4": "avoid", "blink-out2k": "avoid", "blink-mini4k": "avoid",
    "rc-3": "best", "rc-2": "value",
    "ultra-air": "ha", "ultra-pro": "premium", "samsung-ring": "galaxy", "amazfit-helio": "budget",
    # Both Oura rows keep the warning: the Ring 4 has the same 2/8 and the same
    # £5.99 wall, and a reader scanning the table should not read the cheaper
    # row as the one that works without paying.
    "oura-5": "avoid", "oura-4": "avoid",

    "pitpat-gps": "best", "pawva-x01-plus": "value",
    "tractive-dog-6": "avoid", "tractive-cat-6-mini": "cat",
    "weenect-xt": "live", "pawfit-3": "budget", "apple-airtag-2": "tag",
    "vtech-vm4263": "budget", "philips-scd881": "local",
    "philips-scd951": "hybrid", "eufy-c10": "best",
    "nanit-pro": "avoid", "owlet-dream-sock": "health",
}
PLAIN = {
    "epson-et-2951": ("Plugs into the mains.",
                      "The bottles in the box are the ink supply for the period, and refills come from Epson bottles."),
    "canon-pixma-g3590": ("Plugs into the mains.",
                          "The four bottles in the box are the ink supply for the period, and refills come from Canon GI-51 bottles."),
    "canon-pixma-ts6550i": ("Plugs into the mains.",
                            "Starter cartridges only. PG-595 and CL-586 cartridges from any shop keep it printing without a plan."),
    "brother-dcp-j1310dw": ("Plugs into the mains.",
                            "Starter cartridges only. LC521 cartridges from any shop keep it printing without a plan."),
    "brother-dcp-j1200w": ("Plugs into the mains.",
                           "In-box inks only. LC424 cartridges from any shop keep it printing without a plan."),
    "canon-pixma-g3570": ("Plugs into the mains.",
                          "The four bottles in the box are the ink supply for the period, and refills come from Canon GI-51 bottles."),
    "hp-envy-6530e": ("Plugs into the mains.",
                      "Setup cartridges only. HP 308 packs are the retail supply, and the printer is set to original HP ink."),
    "hp-envy-6520e": ("Plugs into the mains.",
                      "Setup cartridges only. HP 308 packs are the retail supply, and the printer is set to original HP ink."),
    "ring": ("Runs on the battery, or you can wire it to your existing chime.",
             "None. The doorbell has no storage of its own and no hub to hold the footage."),
    "nest": ("Runs on the battery, or you can wire it to your existing chime.",
             "None. The doorbell has no storage of its own and no hub to hold the footage."),
    "eufy-e340": ("Runs on the battery, or you can wire it to your existing chime.",
                  "8 GB is built into the doorbell, so it records on its own. The optional HomeBase S380 (16 GB, expandable) holds more."),
    "eufy-c31": ("Runs on its removable battery, or you can wire it to your existing doorbell wiring (24/7 recording needs the wiring, with the old chime bypassed).",
                 "A microSD card (up to 128 GB, not included) in the doorbell. The optional HomeBase S380 holds more."),
    "reo-wifi": ("Wired to your existing doorbell chime.",
                 "A microSD card in the doorbell (up to 256 GB), or a Reolink NVR. It also streams over RTSP and ONVIF, so other apps can pull the video."),
    "reo-poe": ("Powered by an Ethernet cable (PoE): one cable carries both the power and the video, so there is no separate power supply to run.",
                "A microSD card in the doorbell, or a Reolink NVR. It also streams over RTSP and ONVIF, so other apps can pull the video."),
    "reo-batt": ("Runs on the battery, or you can wire it to your existing chime.",
                 "A microSD card in the doorbell, or a Reolink Home Hub indoors (up to 1 TB)."),
    "reo-batt2": ("Runs on its battery, and 8–24 VAC doorbell wiring keeps it topped up.",
                  "A microSD card (up to 512 GB) in the doorbell, or a Reolink Home Hub or NVR."),
    "arlo-fhd": ("Battery only, though you can wire it to an existing chime for trickle charging.",
                 "Only an Arlo SmartHub or Base Station records it locally."),
    "tapo-d235": ("Battery, or hardwired to improve your existing chime (24/7 recording needs the wiring).",
                  "A microSD card (up to 512 GB) inside the doorbell, so the card comes out with the doorbell if it is stolen."),
    "tapo-d260": ("Battery, or hardwired to your existing chime for 24/7 recording.",
                  "A microSD card (up to 512 GB) inside the doorbell, so the card comes out with the doorbell if it is stolen."),
    "ring-4kpro": ("Runs on Ring's Quick Release Ultra battery pack, which Ring says is its fastest charging.",
                   "None. The doorbell has no storage of its own and no hub to hold the footage."),
    "ring-wpro": ("Hardwired to your existing doorbell circuit, or plugged into a socket with Ring's plug-in adaptor. There is no battery version.",
                  "None. The doorbell has no storage of its own and no hub to hold the footage."),
    "ring-elite": ("Powered by an Ethernet cable (PoE+): one cable carries both the power and the video, so there is no battery and no Wi-Fi.",
                   "None. The doorbell has no storage of its own and no hub to hold the footage."),
    "eufy-s4": ("Wired to the doorbell wiring you already have, with the Chime 2 plugged into a socket indoors.",
                "4 GB is built into the doorbell, so it records on its own with no card."),
    "aqara-g410": ("Runs on six AA batteries, or you can wire it to an existing chime.",
                   "A microSD card (up to 512 GB) in the indoor chime hub that comes in the box."),
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
    "aqara-g100": ("Plugged into the mains over USB-C.",
                   "A microSD card (up to 512 GB), or an SMB NAS."),
    "ring-outpro": ("Plugged into a standard socket.",
                    "None. The camera has no storage of its own."),
    "blink-out4": ("Runs on two AA lithium batteries.",
                   "Recording needs a Sync Module 2 and a USB stick (1–256 GB)."),
    "blink-out2k": ("Runs on two AA lithium batteries, which Blink says last up to two years at 1080p.",
                    "Recording needs a Sync Module 2 and a USB stick (1–256 GB); the Sync Module Core in the box cannot store a clip."),
    "tapo-c675d": ("Runs on its rechargeable battery and the solar panel in the box.",
                   "A microSD card (up to 512 GB) in the camera."),
    "aqara-g5pro": ("Plugged into the mains over USB-C.",
                    "32 GB is built into the camera; it has no card slot, and a NAS can hold more."),
    "aqara-g350": ("Plugged into the mains over USB-C.",
                   "A microSD card (up to 512 GB) in the camera."),
    "reo-altas": ("Runs on its rechargeable battery and the solar panel in the box.",
                  "A microSD card (up to 512 GB) in the camera, or a Reolink Home Hub."),
    "reo-arguspt": ("Runs on its rechargeable battery and the 3W solar panel in the box.",
                    "A microSD card (up to 512 GB) in the camera, or a Reolink Home Hub."),
    "ring-outplus": ("Plugged into a standard socket.",
                     "None. The camera has no storage of its own."),
    "blink-mini4k": ("Plugged into the mains; outdoor use needs Blink's weather-resistant power adapter, sold separately.",
                     "Recording needs a Sync Module 2 and a USB stick (1–256 GB)."),
    "ultra-pro": ("A rechargeable ring battery that Ultrahuman quotes at up to 15 days, plus up to 45 days in the PRO charger.",
                  "Ultrahuman's cloud holds the history, and the app shows it on the phone."),
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
    "oura-5": ("A rechargeable ring battery Oura quotes at 6 to 9 days depending on use.",
               "Oura's cloud holds the history, and the phone app shows it."),
    "amazfit-helio": ("A rechargeable ring battery that Amazfit's UK page does not put a figure on. Retailer spec sheets say about four days.",
                      "Zepp's cloud holds the history, and the phone app shows it."),

    "pitpat-gps": ("A GPS tracker with a built-in SIM; PitPat pays for the data.",
                   "A rechargeable tracker that PitPat says lasts several days, or up to six weeks in its specification."),
    "pawva-x01-plus": ("A GPS tracker with a built-in SIM; the data is included for the term.",
                       "A rechargeable tracker that PAWVA says lasts up to five days on its 10-minute interval."),
    "tractive-dog-6": ("A GPS tracker with a built-in SIM, which works only while the plan is active.",
                       "A rechargeable tracker that lasts up to 14 days with Power Saving Zones, or six days without."),
    "tractive-cat-6-mini": ("A GPS tracker with a built-in SIM, which works only while the plan is active.",
                            "A rechargeable tracker that lasts up to 7 days with Power Saving Zones, or four days without."),
    "weenect-xt": ("A GPS tracker with a built-in multi-network SIM, which works only while the plan is active.",
                   "A rechargeable tracker that lasts up to three weeks with power-saving areas, or about seven days of continuous tracking."),
    "pawfit-3": ("A GPS tracker with a built-in SIM, which works only while the plan is active.",
                 "A rechargeable tracker that Pawfit says lasts up to eight days."),
    "apple-airtag-2": ("A Bluetooth tag with no GPS and no SIM; nearby Apple devices relay its location.",
                       "A replaceable CR2032 battery that Apple says lasts more than a year."),
    "vtech-vm4263": ("A local radio monitor with no Wi-Fi, app or account.",
                     "The video stays between the camera and the parent unit; nothing is recorded."),
    "philips-scd881": ("A private 2.4 GHz radio link between the camera and the parent unit.",
                       "The video stays between the camera and the parent unit; nothing is recorded."),
    "philips-scd951": ("A hybrid: the parent unit works directly, and the app adds remote viewing over Wi-Fi.",
                       "Video is live only, to the parent unit; remote viewing goes through Philips's app."),
    "eufy-c10": ("A hybrid: the parent unit works directly, and the app adds remote viewing over Wi-Fi.",
                 "A microSD card in the camera, up to 128 GB and not included; the parent unit is local."),
    "nanit-pro": ("A Wi-Fi camera with no parent unit; the app is the only screen.",
                  "Nanit's cloud. The camera has no local storage."),
    "owlet-dream-sock": ("A sock and base station that send readings to Owlet's cloud; no camera or video.",
                         "Owlet's cloud for the app; the base station holds the alert if the Wi-Fi drops."),
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
    "kit_price", "nosub_say", "plan_say", "buy", "buy_label", "price_check",
    "offers",
)
DERIVED_ROW_KEYS = (
    "score_total", "nosub3", "sub3", "keep3", "maths_free", "maths_sub",
    "plan_region", "keep_basis", "keep_note", "verdict", "plain",
    "offer_at", "offer_conflict",
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
        # A row that lists shops is only as good as the winner's citation: every
        # offer has to resolve to its own page, a price, and a rank, or the
        # rule silently compares a figure with no source behind it.
        if r.get("offers"):
            shops = []
            if r.get("offer_conflict"):
                problems.append(
                    f"{rid}: names a price beside its offers; the offers are the price"
                )
            for offer in r["offers"]:
                missing_offer = [k for k in ("shop", "src", "price", "pay") if k not in offer]
                if missing_offer:
                    problems.append(f"{rid}: an offer is missing {', '.join(missing_offer)}")
                    continue
                shops.append(offer["shop"])
                if offer["src"] not in sources:
                    problems.append(
                        f"{rid}: the offer at {offer['shop']} cites {offer['src']!r}, "
                        "which is not in the source register"
                    )
                elif offer["src"] not in r.get("src", []):
                    problems.append(
                        f"{rid}: the offer at {offer['shop']} cites {offer['src']!r}, "
                        "which is not in the row's src list"
                    )
                if not isinstance(offer["price"], (int, float)) or offer["price"] <= 0:
                    problems.append(f"{rid}: the offer at {offer['shop']} has no price")
                if not isinstance(offer["pay"], int) or isinstance(offer["pay"], bool):
                    problems.append(f"{rid}: the offer at {offer['shop']} has no pay rank")
                if not str(offer.get("note", "")).strip():
                    problems.append(
                        f"{rid}: the offer at {offer['shop']} names no configuration, "
                        "so its price cannot be compared with another shop's"
                    )
            if len(set(shops)) != len(shops):
                problems.append(f"{rid}: lists the same shop twice in its offers")
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
        # A row that lists its shops has no price of its own: the offers are the
        # price, so an authored one would be a second figure to keep in step
        # with the winner. The conflict is recorded while the authored key is
        # still visible; `row_problems()` names it.
        offers = r.get("offers") or ()
        r["offer_conflict"] = bool(
            offers and {"price", "price_src", "price_note"} & set(r)
        )
        if offers:
            won, shown = offer_winner(offers), offer_shown(offers)
            if won["pay"] == PAY_AMAZON:
                # Amazon may win the link but never the figure: the price shown
                # is another UK shop's at the same price, or "Check price".
                r["buy"] = won["src"]
                if shown is won:
                    r["price_check"] = True
            r["price"], r["price_src"] = shown["price"], shown["src"]
            r["price_note"] = (
                f'{shown["shop"]}, {shown["note"]}' if shown.get("note") else shown["shop"]
            )
            r["offer_at"] = shown["shop"]
        else:
            r["offer_at"] = ""
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
        # A row that buys nothing extra has no sum to show: "£309.00 = £309.00"
        # is arithmetic the reader did not ask for and reads like a mistake.
        # A "Check price" row names no price, so its sums name no total either.
        chk = r.get("price_check")
        m_free = "Check price" if chk else f"{money(r['price'])}"
        if r["extra"]:
            m_free += f" + {money(r['extra'])} ({r['extra_note'].lstrip('+ ')})"
            m_free += "" if chk else f" = {money(r['nosub3'])}"
        if not r["free_records"]:
            m_free += cat["labels"]["maths_no_route"] if r["rec"] == "no" else cat["labels"]["maths_brief"]
        m_sub = (
            f"{'Check price' if chk else money(r['price'])} + {months} × {money(r['sub'])} ({r['sub_name']})"
            + ("" if chk else f" = {money(r['sub3'])}")
            if r["sub3"] is not None
            else cat.get("no_plan_note", "No subscription offered or needed")
        )
        r["maths_free"], r["maths_sub"] = m_free, m_sub
    # The slider's ends are the data's own: a row priced below a typed-in floor
    # would disappear from the default view of the page it was added to, and a
    # ceiling off the handle's 5-step grid would snap the dearest row out of
    # range just as quietly.
    prices = [r["price"] for r in rows if not r.get("price_check")]
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
