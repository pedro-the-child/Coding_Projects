import scrapy
from urllib.parse import urljoin

class GenovaComuneSpider(scrapy.Spider):
    name = "genova_comune"
    allowed_domains = ["comune.genova.it", "www.comune.genova.it"]
    start_urls = [
        "https://www.comune.genova.it/amministrazione/politici/consigliere-comunale",
        # Fallback if layout changes:
        # "https://www.comune.genova.it/amministrazione/organi-di-governo/consiglio-comunale",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "AUTOTHROTTLE_MAX_DELAY": 10.0,
        "DOWNLOAD_DELAY": 0.25,
        "FEEDS": {"genova_councillors.jsonl": {"format": "jsonlines", "overwrite": True}},
    }

    def parse(self, response):
        # Councillor cards are typically in div.views-row; safe XPath fallback if layout differs.
        cards = response.css("div.views-row")
        if not cards:
            cards = response.xpath("//main//section//*[.//a[contains(., 'Vai alla pagina')]]")

        for block in cards:
            # Name from heading; skip generic “Contatta il Comune”
            name = (block.css("h2::text, h3::text").get() or "").strip()
            if not name or "contatta il comune" in name.lower():
                name = (block.css("[class*='titl']::text, a[hreflang]::text").get() or "").strip()
            if not name or "contatta il comune" in name.lower():
                continue

            # Prefer explicit “Vai alla pagina” link; fallback to any politician detail link
            detail = block.css("a:contains('Vai alla pagina')::attr(href)").get()
            if not detail:
                detail = block.css("a[href*='/amministrazione/politici/']::attr(href)").get()

            item = {
                "name": name or None,
                "role": None,   # set on detail page (no default fallback)
                "group": None,  # set on detail page
                "email": None,  # set on detail page
                "profile_url": urljoin(response.url, detail) if detail else None,
                "source_url": response.url,
                "detail_source_url": None,
            }

            if item["profile_url"]:
                yield response.follow(item["profile_url"], callback=self.parse_detail, cb_kwargs={"item": item})
            else:
                yield item

        # Pagination
        next_link = response.css(
            "a[rel='next']::attr(href), a.pager__link--next::attr(href), a:contains('Successivo')::attr(href)"
        ).get()
        if next_link:
            yield response.follow(next_link, callback=self.parse)

    def parse_detail(self, response, item):
        # Email
        email = response.css("a[href^='mailto:']::attr(href)").get()
        if email:
            email = email.replace("mailto:", "").strip()

        # Group / party
        group = (response.css("dt:contains('Gruppo') + dd::text, .field--name-field-gruppo *::text").get() or "").strip()
        if not group:
            txt = " ".join(response.css("main *::text").getall())
            if "Gruppo" in txt:
                idx = txt.find("Gruppo")
                group = txt[idx: idx + 140].split("\n")[0].strip()

        # ----- ROLE (no generic fallback) -----
        # Primary: "Tipo di incarico" badge near the right column
        role = (
            response.xpath("normalize-space((//div[.//text()[contains(., 'Tipo di incarico')]]//*[self::a or self::span or self::button][1]/text()))").get()
            # Secondary: common field blocks
            or response.css(".field--name-field-ruolo::text").get()
            or response.xpath("normalize-space(//dt[contains(., 'Ruolo')]/following-sibling::dd[1])").get()
            or response.xpath("normalize-space(//dt[contains(., 'Incarico')]/following-sibling::dd[1])").get()
            or response.xpath("normalize-space(//dt[contains(., 'Carica')]/following-sibling::dd[1])").get()
            or response.xpath("normalize-space(//dt[contains(., 'Funzione')]/following-sibling::dd[1])").get()
            or ""
        ).strip()
        if role:
            role = role.replace("\xa0", " ").strip()
        # If still empty, we leave it as None to clearly see misses
        role = role or None

        item.update({
            "email": email or None,
            "group": group or None,
            "role": role,
            "detail_source_url": response.url,
        })
        yield item
