import logging
import re
import time
from urllib.parse import urlparse,urljoin
import urllib3
from bs4 import BeautifulSoup
import requests
from requests.models import HTTPError


class FetchWeb():


    urllib3.disable_warnings()
    logging.basicConfig(filename='FetchWeb.log',
                        level=logging.DEBUG,
                        filemode='w',
                        format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    def __init__(self,search_text,deep) -> None:
        self.search_text=search_text
        self.deep=deep
        self.checked_links=[]

    
    def link_excute(self,link):
        try:
            time.sleep(5)
            result=requests.get(link,verify=False,timeout=10)
            if result.status_code==200 and 'text'in result.headers['Content-Type']:
                return result

        except requests.ConnectionError as e:
             logging.error(f'Error retrieving {link} | Message: {e}')
             return None 
        except requests.ConnectTimeout as e:
            logging.error(f'Error retrieving {link} as Timeout')
            return None
        except requests.RequestException as e:
            logging.error(f'Error retrieving {link} | Message: {e}')
            return None
        except requests.ReadTimeout as e:
            logging.error(f'Error retrieving {link} | Message: {e}')
            return None
        except requests.Timeout as e:
            logging.error(f'Error retrieving {link} | Message: {e}')
            return None  
        except HTTPError as e:
            # Need to check its an 404, 503, 500, 403 etc.
            status_code = e.response.status_code
            logging.error(f'Error retrieving {link} as status code:{status_code}')
            if status_code!=200:
                return None



# %
    def getStart(self):

        links=[]
        base_url=f"https://www.google.com/search?q={self.search_text}"

        result=self.link_excute(base_url)

        if result==None:
            return []

        
        result_page=BeautifulSoup(result.text,'html.parser')

        for element in result_page.find_all('a'):
            link=element.get('href')

            if not link:
                continue
            if 'http' in link:
                pre_link=link.split('q=')
                if len(pre_link)>1:
                    correct_link=pre_link[1]
                    if correct_link.startswith('http'):
                        to_link=correct_link.split('&')[0]
                        ready_link=self.link_excute(to_link)
                        if ready_link:
                            links.append(to_link)
            
        
        self.process_links(links)
# %

    def process_links(self,links):
        logging.info(f'Count Of visting the links: {len(self.checked_links)}')
        pages_links=[]

        if len(self.checked_links)>self.deep:
            return None

        if links==None:
            logging.error('No Any link gather from google!')
            return []
        
        for link in links:
            result=self.link_excute(link)

            if result==None:
                logging.error(f'Not excute the {link} response')
                return []

            else:
                if link in self.checked_links:
                    continue

                page=BeautifulSoup(result.text,'html.parser')

                self.save_text(page)

                self.checked_links.append(link)
                parsed_source=urlparse(link)

                for element in page.find_all('a'):
                    page_link=element.get('href')
                    if not page_link:
                        continue
                    if page_link.startswith('#'):
                        continue
                    if page_link.startswith('mailto:'):
                        continue

                    if not page_link.startswith('http'):
                        netloc=parsed_source.netloc
                        schema=parsed_source.scheme
                        path=urljoin(parsed_source.path,page_link)
                        page_link=f'{schema}://{netloc}{path}'
                    if parsed_source.netloc not in page_link:
                        continue

                    pages_links.append(page_link)
                    logging.info(f'add child of {page_link} from parent page to process')

        self.process_links(pages_links)


# %
    def save_text(self,page):
        target_text=self.search_text
        f=open(f'contens_{target_text}.txt','a')
        for element in page.find_all(text=re.compile(target_text,flags=re.IGNORECASE)):
            data=[element.get_text()]
            f.writelines(data)
            f.write('\n')
        f.close()
