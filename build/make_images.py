"""Crop/flatten/resize official product images into self-hosted WebP (thumb 120x160, large 360x480).
Sources are recorded in images.json (also used by build.py)."""
import json, os, io, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
from PIL import Image, ImageChops
RAW=os.path.join(HERE,"img_raw"); OUT=os.path.join(ROOT,"img")  # img_raw/ is a git-ignored download cache
os.makedirs(RAW,exist_ok=True); os.makedirs(OUT,exist_ok=True)
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
# id: (image url, page it appears on, crop box as fractions l,t,r,b or None, trim whitespace?)
IMGS={
 "ring":("https://en-uk.ring.com/cdn/shop/files/1_Slate_Sunray_Front_ad46b95a-0b98-4a7e-8f06-0304b31312eb.jpg?v=1779257638","https://en-uk.ring.com/products/battery-doorbell-2nd-gen",None,True),
 "ring-4kpro":("https://en-uk.ring.com/cdn/shop/files/Bigfoot_Deep_Silver_device_1500x1500_36477aae-8427-473d-bb3c-eefee22faf5e.png?v=1774944640","https://en-uk.ring.com/products/battery-doorbell-pro-2nd-gen",None,True),
 "ring-wpro":("https://cdn.shopify.com/s/files/1/2418/9735/files/Ring_Starlit-WIRED_1500x1500_01.jpg?v=1756798210","https://en-uk.ring.com/products/wired-video-doorbell-pro-3-gen",None,True),
 "ring-elite":("https://cdn.shopify.com/s/files/1/2418/9735/files/Cinco_Deep_Silver_device_1500x1500_5ddceb48-b655-46d5-a7bf-db9a16a8b8d4.png?v=1774944937","https://en-uk.ring.com/products/wired-doorbell-elite-2nd-gen",None,True),
 "nest":("https://lh3.googleusercontent.com/7as7cJnLssK4ejvx-4zNQCRmNoupXijD6fkO4orVEB54bB0SRfQn75qzZNnT4Ud4gqOabRfO-8J0YIBRKkMG9yvK5QWKz2FwRQ=rw-rj-sc0xffffffff","https://store.google.com/gb/product/nest_doorbell_battery?hl=en-GB",None,True),
 "eufy-e340":("https://cdn.shopify.com/s/files/1/0504/1094/6753/files/T8214321-UK-DTC-RI00-ExpertReviews.png?v=1749789318","https://www.eufy.com/uk/products/T8214311",(0.55,0,1,1),True),
 "eufy-c31":("https://cdn.shopify.com/s/files/1/0504/1094/6753/files/E8223111_E8223J11_E8223J11-11_E8223T11_T8223111_T8223111-80__ProductImage_nocopy.png","https://www.eufy.com/uk/products/t8223311",None,True),
 "eufy-s4":("https://cdn.shopify.com/s/files/1/0746/3999/9151/files/T8224311-UK-RI01-1_3f640e8f-e4eb-43db-a928-7a159c249128.png?v=1792403525","https://www.anker.com/uk/products/e82153f1",None,True),
 "reo-wifi":("https://home-cdn.reolink.us/wp-content/uploads/2022/05/170610101652767810.7304.png","https://reolink.com/gb/product/reolink-video-doorbell-wifi/",(0,0,0.5,1),True),
 "reo-poe":("https://home-cdn.reolink.us/wp-content/uploads/2023/07/070730451688715045.0661.png","https://reolink.com/gb/product/reolink-video-doorbell-poe/",(0.5,0,1,1),True),
 "reo-batt":("https://home-cdn.reolink.us/wp-content/uploads/2024/10/doorbell-battery-1pack.png","https://reolink.com/gb/product/reolink-doorbell-battery/",None,True),
 # Both Tapo heroes are 2000px squares with a badge and a phone in them, so
 # the crop keeps the doorbell and cuts the marketing around it.
 "tapo-d235":("https://uk.store.tapo.com/cdn/shop/files/D235-award.jpg?v=1772017345&width=2048","https://uk.store.tapo.com/products/video-doorbell-wired-and-battery-tapo-d235",(0.36,0.03,0.62,0.97),True),
 "tapo-d260":("https://uk.store.tapo.com/cdn/shop/files/D260-4k.jpg?v=1787566661&width=2048","https://uk.store.tapo.com/products/tapo-doorbell-pro-tapo-d260-4k-video-doorbell",(0.26,0.10,0.72,0.98),True),
 "tapo-td21":("https://uk.store.tapo.com/cdn/shop/files/0002290-RedesigntheDoorbellMainImage21.png?v=1776441614&width=2048","https://uk.store.tapo.com/products/battery-video-doorbell-2k-3mp-colour-night-vision-tapo-td21",(0.1,0,0.47,1),True),
 "arlo":("https://www.arlo.com/content/dam/arlo/2024-content/products/essential-wd-2k/en/si-compressed/arlo-2k-wireless-video-doorbell-white.png","https://www.arlo.com/en_gb/doorbells/arlo-2k-wireless-video-doorbell",None,True),
 "arlo-fhd":("https://www.arlo.com/content/dam/arlo/2024-content/products/essential-doorbell-fhd/uk/si-compressed/arlo-hd-wireless-video-doorbell-white.png/jcr:content/renditions/web-default.webp","https://www.arlo.com/en_gb/doorbells/arlo-fhd-wireless-video-doorbell",None,True),
 # The only clean shot of the 2nd Gen is a wide lifestyle photo, so the crop
 # closes in on the doorbell itself.
 "reo-batt2":("https://home-cdn.reolink.us/wp-content/uploads/2026/07/07072047b8da51b303ff3426.jpg.webp","https://reolink.com/gb/product/reolink-video-doorbell-2nd-gen/",(0.34,0.22,0.66,0.80),True),
 "aqara-g4":("https://eu.aqara.com/cdn/shop/files/Aqara-Smart-Video-Doorbell-G4.webp?v=1729063964","https://eu.aqara.com/products/aqara-video-doorbell-g4",(0,0,0.46,1),True),
 # The UK shop's own hero is a photo of the retail boxes, so the doorbell is
 # taken from Aqara's product page instead, cropped past the chime beside it.
 "aqara-g410":("https://eu.aqara.com/cdn/shop/files/Aqara_Smart_Video_Doorbell_G410_1.webp?v=1751957883","https://eu.aqara.com/products/aqara-doorbell-camera-hub-g410",(0,0,0.50,1),True),
 "blink":("https://images.squarespace-cdn.com/content/v1/5e21c06a08d2fc435f20e6c5/feb6535d-c34d-48dd-a015-648dd5786bac/Blink_Battery_Doorbell_2K.png?format=1000w","https://blinkforhome.com/products",(0.30,0.02,0.72,0.98),False),
 # The 2K+ render is the one card on Blink's own devices page, so it is the
 # official picture of the model Blink sells now; the Outdoor 4 has no card left.
 "blink-out2k":("https://images.squarespace-cdn.com/content/v1/5e21c06a08d2fc435f20e6c5/2300b960-b1fa-493f-a919-7aeffe5c547e/2K%2B+Blink+Outdoor+2K%2B.png","https://blinkforhome.com/products",None,True),
 "tapo-c675d":("https://static-product.tp-link.com/tapo-c675d-kit_v1/en/img/17-c675d_kit.png","https://uk.store.tapo.com/products/tapo-c675d-kit-4k-solar-powered-dual-lens-pan-tilt-security-camera-kit",None,True),
 # Aqara's UK page shows the retail box; the EU product page carries the clean
 # white camera render, as it does for the G4 and G410 doorbells.
 "aqara-g5pro":("https://eu.aqara.com/cdn/shop/files/G5-white-wifi.webp?v=1748515993","https://eu.aqara.com/products/aqara-camera-hub-g5-pro",(0.41,0.03,0.88,0.88),True),
 "aqara-g350":("https://www.aqara-shop.co.uk/wp-content/uploads/2026/02/Aqara-G350-cam-1.jpg","https://www.aqara-shop.co.uk/product/aqara-camera-hub-g350-select/",None,True),
 "reo-altas":("https://home-cdn.reolink.us/wp-content/uploads/2024/09/Altas-PT-Ultra-sp.png","https://reolink.com/gb/product/altas-pt-ultra/",None,True),
 "reo-arguspt":("https://home-cdn.reolink.us/wp-content/uploads/2025/03/Argus-PT-Ultra-WiFi-6-White-Solar-Panel-White.png","https://reolink.com/gb/product/argus-pt-ultra/",None,True),
 # The press image shows the white and black cameras; the crop keeps the black
 # one, and the page is Amazon's own newsroom, not a retailer listing.
 "blink-mini4k":("https://assets.aboutamazon.com/5a/57/eb905b304e7b9c625be73fa78310/blinkmini4k-inline-amazonnews-ck101925.jpg","https://www.aboutamazon.com/news/devices/blink-4k-long-range-security-cameras",(0.50,0.25,0.73,0.98),True),
 "ezviz-ep3x":("https://mfs.ezvizlife.com/62d7d264ab031e75591d277638d4c440.png","https://www.ezviz.com/uk/product/ep3x-pro/55935",(0,0,0.255,1),True),
 "ezviz-db2":("https://s3.amazonaws.com/mfs.ezvizlife.com/f6a3b42474eefe13047add4b7b3c89c3.jpg","https://www.ezviz.com/uk/product/db2-pro-kit/42371",(0.28,0.2,0.43,0.79),True),
 "reo-argus4":("https://home-cdn.reolink.us/wp-content/uploads/2024/06/argus-4-pro-whitesolar-panel-2-white.png","https://reolink.com/gb/product/argus-4-pro/",None,True),
 "reo-rlc820a":("https://home-cdn.reolink.us/wp-content/uploads/2023/03/200425471679286347.6671.png","https://reolink.com/gb/product/rlc-820a/",None,True),
 "reo-e1out":("https://home-cdn.reolink.us/wp-content/uploads/2023/05/160805511684224351.237.png","https://reolink.com/gb/product/e1-outdoor-pro/",None,True),
 "tapo-c660":("https://uk.store.tapo.com/cdn/shop/files/Tapo_C660_KIT_Solar-Powered_Pan-Tilt-Zoom_4K_Security_Camera.jpg?v=1760541897&width=2048","https://uk.store.tapo.com/products/tapo-c660-kit-4k-clarity-solar-powered-pan-tilt-battery-security-camera-kit",None,True),
 "eufy-s340":("https://cdn.shopify.com/s/files/1/0746/3999/9151/files/T8170-DTC.png?v=1788149525","https://www.anker.com/uk/products/t81703w1",None,True),
 "eufy-e30":("https://cdn.shopify.com/s/files/1/0746/3999/9151/files/Frame_2147226768.png?v=1788149693","https://www.anker.com/uk/products/t8417221",None,True),
 "aqara-g3":("https://eu.aqara.com/cdn/shop/files/G3_1.webp","https://eu.aqara.com/products/aqara-2k-security-indoor-camera-hub-g3",None,True),
 "aqara-e1":("https://eu.aqara.com/cdn/shop/files/aqara-Camera_E1.webp?v=1774333578","https://eu.aqara.com/products/aqara-2k-indoor-security-camera-e1",None,True),
 "aqara-g100":("https://eu.aqara.com/cdn/shop/files/aqara-camera-g100-1.webp?v=1773400773","https://eu.aqara.com/products/aqara-camera-g100",(0,0,0.50,1),True),
 "ring-outpro":("https://en-uk.ring.com/cdn/shop/files/Ring_GROUPER_White-Plugin_1500x1500_01.jpg?v=1757078401","https://en-uk.ring.com/products/stick-up-cam-pro-plug-in",None,True),
 "ring-outplus":("https://en-uk.ring.com/cdn/shop/files/Ring_OCP-White-Plug_in_1500x1500_01.jpg?v=1756448906","https://en-uk.ring.com/products/outdoor-cam-plus-plugin",None,True),
 # The Oura render sits on a studio gradient with the finish swatches below
 # it, so it is cropped rather than trimmed against white.
 "oura-4":("https://ourahealth.imgix.net/blue-sky/pop/gen4/finishes-carousel-slide-silver.png?ixlib=js-3.8.0&auto=format&fit=crop&fm=png&ar=2%3A1&crop=focalpoint&fp-x=0.5&fp-y=0.51&fp-z=1.15&q=70&w=1920&s=2e1d3272a6ead1f907787a0fde071870","https://ouraring.com/store/rings/oura-ring-4",(0.30,0.10,0.66,0.82),False),
 # Ring 5's studio shot sits on a warm background like the Ring 4 render, so it
 # is cropped to portrait rather than trimmed against white, which would have
 # framed it in a white border.
 "oura-5":("https://ourahealth.imgix.net/cooper-pdp/or5-silver-alt.png?ixlib=js-3.8.0&auto=format&fit=max&fm=png&q=70&w=640&s=c1abb1ce6418079507b352bab9ce96da","https://ouraring.com/store/rings/oura-ring-5/silver",(0.22,0.04,0.78,0.96),False),
 "ultra-air":("https://public-web-assets.uh-static.com/web_v2/illustrations/ring-air-front.png","https://www.ultrahuman.com/ring/",None,True),
 "ultra-pro":("https://public-web-assets.uh-static.com/web_v2/ring-pro/buy-v2/carousel-v4/desktop/bionic-gold/1.png","https://www.ultrahuman.com/gb/ring-pro/buy",(0.25,0.0,0.82,1.0),True),
 "rc-2":("https://ringconn.com/cdn/shop/files/RingConn_Smart_Ring_Gen_2-Royal_Gold.png?v=1780302336&width=1200","https://ringconn.com/products/ringconn-gen-2",None,True),
 "rc-2-air":("https://ringconn.com/cdn/shop/files/ringconn_gen_2_air_1.png?v=1780302386&width=600","https://ringconn.com/products/ringconn-gen-2-air",None,True),
 "rc-3":("https://ringconn.com/cdn/shop/files/1a_9e4056a6-6b65-41d1-804e-03aaa2818425.webp?v=1780302453&width=600","https://ringconn.com/products/ringconn-gen-3",None,True),
 "samsung-ring":("https://images.samsung.com/is/image/samsung/p6pim/uk/2407/gallery/uk-galaxy-ring-q500-sm-q500nzkaeub-542183975?$720_576_JPG$","https://www.samsung.com/uk/rings/galaxy-ring/galaxy-ring-titanium-black-size-10-sm-q500nzkaeub/",None,True),
 "amazfit-helio":("https://uk.amazfit.com/cdn/shop/files/Helioring_1024x1024.jpg?v=1716446501","https://uk.amazfit.com/products/amazfit-helio-ring",None,True),
 # HP's hero carries a "3 months Instant Ink free" banner across the paper tray,
 # so the crop ends above it. Epson's hero shows the bottles and its own
 # "3 years of ink included" sheet, which is the product as sold.
 "hp-envy-6530e":("https://www.hp.com/gb-en/shop/media/catalog/product/1/_/1_cus_7.jpg?store=gb-en&image-type=image&auto=avif&quality=100&format=pjpg&type=image-product&width=960&fit=bounds","https://www.hp.com/gb-en/shop/products/printers/hp-envy-6530e-all-in-one-printer-714p1b-687",(0,0,1,0.74),True),
 # HP's UK product page for the 6520e is broken, and its UK listing never
 # paints the card's photo, so the render comes from HP's own Swiss store page
 # for the same printer, which serves the official product image.
 "hp-envy-6520e":("https://www.hp.com/ch-en/shop/media/catalog/product/h/p/hp-envy-6520e_ch_en_cus.jpg?store=ch-en&image-type=image&auto=avif&quality=100&format=pjpg&type=image-product&width=960&fit=bounds","https://www.hp.com/ch-en/shop/products/printers/hp-envy-6520e-all-in-one-printer-714n9b-629",(0,0.16,1,0.575),True),
 "brother-dcp-j1310dw":("https://bie-p-001-delivery.sitecorecontenthub.cloud/api/public/content/98871d9064814cafa79e5ab3787bc5e4?v=066db67b","https://store.brother.co.uk/devices/inkjet/dcpj/dcpj1310dw",None,True),
 "brother-dcp-j1200w":("https://bie-p-001-delivery.sitecorecontenthub.cloud/api/public/content/cb802603181d4e91ba36aa693c7d811e?v=36a52d24","https://store.brother.co.uk/devices/inkjet/dcpj/dcpj1200w",None,True),
 "epson-et-2951":("https://i8.amplience.net/i/epsonemear/a23212-productpicture-hires-en-int-ecotank_et2950_01_main_2000x2000px","https://www.epson.co.uk/en_GB/products/printers/inkjet/consumer/ecotank-et-2951-a4-multifunction-wi-fi-ink-tank-printer,-with-up-to-3-years-of-ink-included/p/52035",None,True),
 "canon-pixma-g3590":("https://i1.adis.ws/i/canon/6706C008_PIXMA-G3590_02?w=1200","https://www.canon.co.uk/store/canon-pixma-g3590-3-in-1-refillable-megatank-inkjet-printer/6706C008/",None,True),
 "canon-pixma-g3570":("https://i1.adis.ws/i/canon/5805C008_PIXMA-G3570-BK_02?w=1200","https://www.canon.co.uk/store/canon-pixma-g3570-wireless-colour-3-in-1-refillable-megatank-printer-black/5805C008/",None,True),
 # Canon's render includes its PIXMA Print Plan sheet, the same treatment as
 # Epson's "3 years of ink included" sheet.
 "canon-pixma-ts6550i":("https://i1.adis.ws/i/canon/7179C008_PIXMA-TS6550i_000?w=1200","https://www.canon.co.uk/store/canon-pixma-ts6550i-wireless-colour-3-in-1-inkjet-photo-printer/7179C008/",None,True),
}
PLACEHOLDER={
 "hik":"Hikvision's own product page for the DS-KB6003-WIP has been removed (discontinued); only a text datasheet remains, so no reliable official image.",
 "blink-out4":"Blink's own devices page no longer lists the Outdoor 4, so the only official image left is the Amazon UK listing, which does not license a self-hosted copy.",
}
def flat(im):
    im=im.convert("RGBA"); bg=Image.new("RGBA",im.size,(255,255,255,255)); bg.alpha_composite(im); return bg.convert("RGB")
def trim(im):
    diff=ImageChops.difference(im,Image.new("RGB",im.size,(255,255,255))).convert("L").point(lambda v:255 if v>18 else 0)
    bb=diff.getbbox(); return im.crop(bb) if bb else im
def fit(im,W,H,pad):
    c=Image.new("RGB",(W,H),(255,255,255)); im=im.copy(); im.thumbnail((W-2*pad,H-2*pad),Image.LANCZOS)
    c.paste(im,((W-im.width)//2,(H-im.height)//2)); return c
meta={}
for k,(u,page,box,tr) in IMGS.items():
    p=f"{RAW}/{k}.bin"
    if not os.path.exists(p):
        open(p,"wb").write(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30).read())
    im=flat(Image.open(p))
    if box: w,h=im.size; im=im.crop((int(box[0]*w),int(box[1]*h),int(box[2]*w),int(box[3]*h)))
    if tr: im=trim(im)
    for suf,(W,H,pad) in {"sm":(120,160,8),"lg":(360,480,22)}.items():
        fit(im,W,H,pad if tr else 0 if suf=="sm" else 0).save(f"{OUT}/{k}-{suf}.webp","WEBP",quality=80,method=6)
    meta[k]={"src":u,"page":page,"cropped":bool(box)}
for k,why in PLACEHOLDER.items(): meta[k]={"placeholder":True,"why":why}
json.dump(meta,open(os.path.join(HERE,"images.json"),"w"),indent=1)
L=["# Product image sources","","Every photo is the manufacturer's own product image, downloaded once, cropped to the product where the original showed extra items (phone, chime, award badge), flattened onto white and saved as WebP (`-sm` 120×160 for table rows, `-lg` 360×480 for details). Nothing is hotlinked.","","| File | Original image | Found on |","|---|---|---|"]
for k,v in meta.items():
    if v.get("placeholder"): L.append(f"| — ({k}) | None: neutral placeholder used | {v['why']} |")
    else: L.append(f"| `img/{k}-sm.webp`, `img/{k}-lg.webp` | {v['src']}{' (cropped)' if v['cropped'] else ''} | {v['page']} |")
open(os.path.join(ROOT,"IMAGE_SOURCES.md"),"w").write("\n".join(L)+"\n")
print("done",len(IMGS))
