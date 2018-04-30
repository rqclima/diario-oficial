from dateparser import parse
import datetime as dt

import scrapy

from gazette.items import Gazette

class PrCuritibaSpider(scrapy.Spider):
    MUNICIPALITY_ID = '4106902'
    name = 'pr_curitiba'
    allowed_domains = ['legisladocexterno.curitiba.pr.gov.br']
    start_urls = ['http://legisladocexterno.curitiba.pr.gov.br/DiarioConsultaExterna_Pesquisa.aspx']


    def parse(self, response):
        """
        The Curitiba website is a statefull page, so we can't just build the
        request from zero, we have to resend the viewstate with every request.
        @url http://legisladocexterno.curitiba.pr.gov.br/DiarioConsultaExterna_Pesquisa.aspx
        @returns requests 1
        """
        todays_date = dt.date.today()
        current_year = todays_date.year
        current_month = todays_date.month
        yield self.scrap_year(response, 2015)

    def scrap_year(self, response, year):
        return scrapy.FormRequest.from_response(
            response,
            formdata={
                'ctl00$cphMasterPrincipal$ddlGrAno': str(year)
            },
            callback=self.parse_year
        )


    def parse_year(self, response):
        for i in range(12):
            yield self.scrap_month(response, i)

    def scrap_month(self, response, month):
        return scrapy.FormRequest.from_response(
            response,
            formdata={
                'ctl00_cphMasterPrincipal_TabContainer1_ClientState' : '{{"ActiveTabIndex":{},"TabState":[true,true,true,true,true,true,true,true,true,true,true,true]}}'.format(month)
            },
            callback=self.parse_month,
        )

    def parse_month(self, response):
        #Count how many pages and iterate
        page_count = len(response.css(".grid_Pager:nth-child(1) table td").extract())
        for page_number in range(1,page_count + 1):
            yield scrapy.FormRequest.from_response(
                response,
                formdata={
                    '__EVENTARGUMENT' : 'Page${}'.format(page_number),
                    '__EVENTTARGET' : 'ctl00$cphMasterPrincipal$gdvGrid2'
                },
                callback=self.parse_page,
            )

    def parse_page(self, response):
        #for each link
        current_year = response.css(".caixa_formulario option:checked ::attr(value)").extract_first()
        current_month = response.css(".ajax__tab_active a span ::text").extract()
        current_page = response.css(".grid_Pager span ::text").extract_first()
        pdf_date = response.css("td:nth-child(2) span").extract_first()

        print('For year {0} - Month {1} - {2}th page - date is {3}'.format(current_year, current_month, current_page, pdf_date))
        dummy_gazette = Gazette(
            date = dt.date.today(),
            file_urls=["www.example.com"],
            is_extra_edition= False,
            municipality_id=self.MUNICIPALITY_ID,
            power='executive_legislature',
            scraped_at=dt.datetime.utcnow()
        )
        return []
