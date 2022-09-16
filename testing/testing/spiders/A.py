import scrapy
import re
import requests
from bs4 import BeautifulSoup
from lxml import etree

from ..items import ShopItem


class ASpider(scrapy.Spider):
    name = 'A'
    # allowed_domains = ['xxx.www']
    # start_urls = ['https://www.nastygal.com/whats-new']# 爬取的页面
    Realm_name = "https://www.nastygal.com"  # 网站域名

    def start_requests(self):
        Url = "https://www.nastygal.com/whats-new"  # 爬取的页面
        resp = requests.get(url=Url).text  # 包含部分数据的网页
        html = etree.HTML(resp)
        all_sum = str(html.xpath('//*[@id="product-grid"]/div[2]/div/div[1]/span/span[2]/text()')[0])  # 获得数据总数
        Url = Url + "?start=0&sz={}".format(all_sum.replace(",", ""))  # 这个网页可以通过构造get请求获取全部数据
        yield scrapy.Request(url=Url, callback=self.parse)

    def parse(self, response):
        # r = response.xpath('//*[@id="product-grid"]/div[2]/div/div[1]/span/span[2]/text()')
        # for each in response.xpath("//li[@class='item']")
        sections = response.xpath('//*[@id="product-grid"]/div[2]/section')
        for section in sections:
            item = ShopItem()

            name = str(section.xpath("./div[2]/div[1]/h3/a/text()").extract_first()).replace("\n", "")  # 商品名

            url = str(section.xpath("./div[2]/div[1]/h3/a/@href").extract_first()).replace("\n", "")  # url
            if url.startswith("/"):
                url = self.Realm_name + url  # 拼凑url

                # print(url)

            try:
                current_price = str(section.xpath("./div[2]//div[2]/div/span[4]/text()").extract_first()).replace("\n", "")  # 现价

            except:
                current_price = str(section.xpath("./div[2]/div[1]/div[2]/div/span/text()").extract_first()).replace("\n", "")  # 其他情况(只有现价)

            try:
                original_price = str(section.xpath("./div[2]//div[2]/div/span[2]/text()").extract_first()).replace("\n", "")  # 原价

            except:
                original_price = current_price  # 没有原价的情况

            img = "https:" + str(section.xpath("./div[2]/div[1]/div[1]/a/picture[1]/img/@src").extract_first()).replace("\n", "")  # img
            item['name'] = name
            item['original_price'] = original_price
            item['current_price'] = current_price
            item['image'] = img
            item['url'] = url
            # print(url)

            yield scrapy.Request(url=url, callback=self.parse_detail, meta={"item": item, "url": url})

    def parse_detail(self, response):
        # print(response)
        # print(response.xpath('//*[@id="maincontent"]/div/div/div[2]/main/div[5]/div/p/text()').extract_first()) # 网页复制的xpath用不了
        #  详情页我用xpath解析不了，我只好用bs4替代
        url = response.meta["url"]
        # print(url)
        Detail_page1 = requests.get(url=url).text
        page = BeautifulSoup(Detail_page1, "html.parser")  # 换用bs4解析

        try:

            detail_cat = str(page.findAll("span", attrs={"itemprop": "name"})[3]).split(">")[1].split("<")[0]  # 商品类
            # print(detail_cat)

        except:
            # print(url)
            # print("问题在这")
            # print("此商品没有分类")  # Home / Satin Bow Hair Clip 像这样的
            detail_cat = "none"

        small_detail = page.find("div", attrs={"class": "b-product_details-content"})  # 商品描述在这个div里

        fabrics = small_detail.find("p", attrs={"class": "b-product_details-composition"})  # 面料

        cloth_id = small_detail.find("span", attrs={"data-tau": "b-product_details-id"})  # 服装编号SKU

        obj = re.compile(r"<p>(?P<haha>.*?)</p>", re.S)  # 主要内容在p标签内，我用正则表达式提取方便点

        try:
            result = obj.finditer(str(small_detail))
            for i in result:
                p = i.group("haha")  # 拿到内容
        except:
            print(url)
            # print(p)

        need_list = p.split("\n")  # 切割内容

        detail = ""
        for i in need_list:
            detail = detail + ',' + i.replace("<br/>", "").replace("<li>", "").replace("<ul>", "").replace("</ul>",
                                                                                                           "").replace(
                "</li>",
                "")
            # 去除多余标签
        if fabrics is None:
            description = detail.lstrip(',') + ',' + "SKU:" + str(cloth_id).split(">")[1].split("<")[0]

        else:
            description = detail.lstrip(',') + ',' + str(fabrics).split(">")[1].split("<")[0] + ',' + "SKU:" + \
                          str(cloth_id).split(">")[1].split("<")[0]
        # print(description)

        item = response.meta["item"]

        item['detail_cat'] = detail_cat

        item['description'] = description

        print(item)

        yield item  # 返回引擎



