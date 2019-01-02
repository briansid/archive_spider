# -*- coding: utf-8 -*-
import scrapy, json, re, sys


class ArchiveSpider(scrapy.Spider):
    name = 'archive'
    allowed_domains = ['archive.org']

    def start_requests(self):
        domain = 'gismeteo.ua'
        url = 'https://web.archive.org/cdx/search?url={}/&matchType=prefix&collapse=urlkey&output=json&fl=original,mimetype,timestamp,endtimestamp,groupcount,uniqcount&filter=!statuscode:[45]'.format(domain)
        yield scrapy.Request(url, self.parse_urls, meta = {'domain': domain})

    def parse_urls(self, response):
        j = json.loads(response.text)
        for item in j[1:]:
            meta = response.meta
            meta['site'] = item[0]
            meta['filetype'] = item[1]
            num_captures = item[4]
            meta['first_captured'] = item[2]
            meta['last_captured'] = item[3]
            meta['snapshot'] = item[2]

            if num_captures == '1':
                url = 'https://web.archive.org/web/{}/{}'.format(meta['snapshot'], meta['site'])
                yield scrapy.Request(url, self.parse_snapshot, meta=meta)

            else:
                firstyear = meta['first_captured'][:4]
                lastyear = meta['last_captured'][:4]
                for year in range(int(firstyear), int(lastyear)+1):
                    url = url = 'https://web.archive.org/__wb/calendarcaptures?url={}&selected_year={}'.format(meta['site'], year)
                    scrapy.Request(url, self.parse_year)

    def parse_year(self, response):
        j = json.loads(response.text)
        meta = response.meta
        snapshots = re.findall(str(meta['year']) + r'\d+', response.text)
        for snapshot in snapshots:
            meta['snapshot'] = snapshot
            url = 'https://web.archive.org/web/{}/{}'.format(snapshot, meta['site'])
            yield scrapy.Request(url, self.parse_snapshot, meta=meta)

    def parse_snapshot(self, response):
        meta = response.meta
        # TODO: proper filenames
        site = meta['site'].replace('http://', '').replace('/', '_')
        if meta['filetype'] == 'text/html':
            filename = '{}-{}.html'.format(meta['snapshot'], site.replace('.html', ''))
        else:
            filename = '{}-{}'.format(meta['snapshot'], site)

        with open(filename, 'w') as f:
            f.write(response.text)