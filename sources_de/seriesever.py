# -*- coding: utf-8 -*-

'''
    Exodus Add-on
    Copyright (C) 2016 Viper4k

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import re, urllib, urlparse, json, base64

from resources.lib.modules import cleantitle
from resources.lib.modules import client

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['seriesever.net']
        self.base_link = 'http://seriesever.net'
        self.search_link = 'service/search?q=%s'
        self.part_link = 'service/get_video_part'

    def tvshow(self, imdb, tvdb, tvshowtitle, year):
        try:
            url = self.__search(tvshowtitle)
            if not url:
                title = cleantitle.local(tvshowtitle, imdb, 'de-DE')
                url = self.__search(title)
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url == None:
                return

            return url + '/staffel-%s-episode-%s.html' % (season, episode)
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if url == None:
                return sources

            hostDict = [(i.rsplit('.', 1)[0], i) for i in hostDict]
            hostDict = [i[0] for i in hostDict]

            query = urlparse.urljoin(self.base_link, url)

            r = client.request(query, mobile=True)

            id = re.compile('var\s*video_id\s*=\s*"(\d+)"').findall(r)[0]

            p = client.parseDOM(r, 'a', attrs={'class': 'changePart'}, ret='data-part')
            p = p[0] if p and len(p) == 1 else '720p'

            query = urlparse.urljoin(self.base_link, self.part_link)

            r = urllib.urlencode({'video_id': id, 'part_name': p, 'page': '0'})
            r = client.request(query, mobile=True, headers={'X-Requested-With': 'XMLHttpRequest'}, post=r)

            r = json.loads(r)
            r = r.get('part', {})

            s = r.get('source', '')
            url = r.get('code', '')

            if s == 'url' and 'http' not in url:
                url = self.__decode_hash(url)
            elif s == 'other':
                url = client.parseDOM(url, 'iframe', ret='src')[0]
                if '/old/seframer.php' in url: url = self.__get_old_url(url)

            quli = 'HD' if p in ['1080p', '720p', 'HD'] else 'SD'

            host = re.findall('([\w]+[.][\w]+)$', urlparse.urlparse(url.strip().lower()).netloc)[0]
            if not host in hostDict: Exception()

            sources.append(
                {'source': host, 'quality': quli,
                 'provider': 'SERIESEVER',
                 'language': 'de',
                 'url': url, 'direct': False,
                 'debridonly': False})

            return sources
        except:
            return sources

    def resolve(self, url):
        return url

    def __search(self, title):
        try:
            query = self.search_link % (urllib.quote_plus(title))
            query = urlparse.urljoin(self.base_link, query)

            t = cleantitle.get(title)

            r = {'X-Requested-With': 'XMLHttpRequest'}
            r = client.request(query, headers=r)

            if r and r.startswith('{'): '[%s]' % r

            r = json.loads(r)
            r = [(i['url'], i['name']) for i in r if 'name' in i and 'url' in i]
            r = [i[0] for i in r if cleantitle.get(i[1]) == t][0]

            url = re.findall('(?://.+?|)(/.+).html?', r)[0]
            url = client.replaceHTMLCodes(url)
            url = url.encode('utf-8')
            url = url.replace('serien/', '')
            return url
        except:
            return

    def __decode_hash(self, hash):
        hash = hash.replace("!BeF", "R")
        hash = hash.replace("@jkp", "Ax")
        try: return base64.b64decode(hash)
        except: return

    def __get_old_url(self, url):
        try:
            r = client.request(url, mobile=True)
            url = re.findall('url="(.*?)"', r)

            if len(url) == 0:
                url = client.parseDOM(r, 'iframe', ret='src')[0]
                if "play/se.php" in url:
                    r = client.request(url, mobile=True)
                    return self.__decode_hash(re.findall('link:"(.*?)"', r)[0])
            else:
                return url[0]
        except:
            return


