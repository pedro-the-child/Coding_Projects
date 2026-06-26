import scrapy 

class GenovaShortSpider(scrapy.Spider):
    name = "genova_short"
    allowed_domains = ["comune.genova.it", "www.comune.genova.it"]
    start_urls = [ "https://www.comune.genova.it/amministrazione/politici"]

    def parse(self, response):
        for legislator in response.css("div.card.py-3.px-4.h-100.rounded.shadow-sm.border.border-light"):
            yield {
                'name': legislator.css("span.field.field--name-title.field--type-string.field--label-hidden::text").get(),
                'role' : legislator.css("div.mb-1::text").get(),
                'url' : legislator.css("a.chatbot-noindex.read-more.gap-1.bottom-0.mb-3.start-0.ms-4::attr(href)").get(),
            }