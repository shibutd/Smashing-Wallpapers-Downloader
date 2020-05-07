import os
import re
import typing
import calendar
import asyncio
import click
import requests
from bs4 import BeautifulSoup
import aiohttp
import aiofiles


class Month:
    '''Class to represent month.'''

    def __init__(self, month):
        self._month = self.validate_input(month)

    @staticmethod
    def validate_input(value: str) -> str:
        '''Make sure user input month is valid'''
        if value.isdigit() and 1 <= int(value) <= 12 or \
                (value.isalpha() and value.lower().capitalize()
                    in list(calendar.month_name)):
            return str(value)
        raise ValueError('Month value is not valid', value)

    @property
    def number(self) -> int:
        '''Return month number: 1, 2, 3, ..., 12'''
        if self._month.isdigit():
            return int(self._month)
        else:
            month_name = self._month.lower().capitalize()
            return list(calendar.month_name).index(month_name)

    @property
    def name(self) -> str:
        '''Return month name: January, February, ..., December'''
        if not self._month.isdigit():
            return self._month.lower().capitalize()
        else:
            return calendar.month_name[int(self._month)]


class ImageDownloader:
    '''Class to represent downloader for images.'''

    def __init__(self, resolution):
        self.resolution = self.validate_input(resolution)

    @staticmethod
    def validate_input(value: str) -> str:
        '''Make sure user input resolution is valid'''
        match = re.search('^\d{3,4}x\d{3,4}$', value)
        if match:
            return value
        raise ValueError('Resolution value is not valid', value)

    def get_url(self, url: str, month_number: int, month_name: str, year: int) -> str:
        '''Create and returns url of required form for further request'''
        # Convert month number. Value for request must have value
        # (month_number - 1) and form: '01', '02',.. '12'
        month_number_str = str(range(1, 13)[month_number - 2])
        if len(month_number_str) == 2:
            converted_month_number = month_number_str
        else:
            converted_month_number = '0{}'.format(month_number_str)
        year_category = (year - 1) if converted_month_number == '12' else year

        url = 'https://{0}/{1}/{2}/desktop-wallpaper-calendars-{3}-{4}/'.format(
            url,
            str(year_category),
            converted_month_number,
            month_name.lower(),
            str(year)
        )
        return url

    def create_directory(self, basic_directory: str, month_name: str, year: int) -> str:
        '''Create directory to store downloaded files'''
        storage_path = os.path.join(
            basic_directory,
            'Smashing_wallpaper_{0}_{1}'.format(month_name, str(year))
        )
        try:
            os.makedirs(storage_path, exist_ok=True)
        except OSError as err:
            raise Exception(
                'Unable to create directory for downloading files: {}'.format(err))
        else:
            return storage_path

    def fetch_content(self, url: str, **kwargs) -> bytes:
        '''Make HTTP GET request to given url and return response content'''
        try:
            response = requests.get(url, **kwargs)
            response.raise_for_status()
        except requests.Timeout:
            raise Exception('Connection timed out')
        except requests.HTTPError:
            raise Exception('Error {}'.format(response.status_code))
        except requests.RequestException:
            raise Exception('Unable to establish connection')
        else:
            return response.content

    def get_image_links(self, content: bytes) -> typing.List[str]:
        '''Parse page for links with required resolution and returns list of links'''
        soup = BeautifulSoup(content, 'lxml')
        image_links = []

        for link in soup.find_all('a'):
            if link.text == self.resolution:
                image_links.append(link.get('href'))
        return image_links

    async def download_image(self, session: aiohttp.ClientSession,
                             semaphore: asyncio.Semaphore,
                             storage_path: str, link: str) -> bool:
        '''Download image from given link'''
        try:
            async with semaphore:
                async with session.get(link) as response:
                    response.raise_for_status()
                    image_name = link[link.rfind('/') + 1:]
                    async with aiofiles.open(
                        os.path.join(storage_path, image_name),
                        mode='wb'
                    ) as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            await f.write(chunk)
        except Exception:
            return False
        else:
            return True

    async def download_all(self, storage_path: str, links: typing.List[str]) -> int:
        '''Download images from given list of links, return number of downloaded images'''
        downloaded_image_count = 0
        semaphore = asyncio.Semaphore(5)
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(self.download_image(
                session, semaphore, storage_path, link)) for link in links]
            for res in asyncio.as_completed(tasks):
                result = await res
                if result:
                    downloaded_image_count += 1
        return downloaded_image_count


@click.command()
@click.option('-r', '--resolution',
              help='Resolution, example: 1920x1080', required=True)
@click.option('-m', '--month',
              help='Month, number or text format, example: 12 or December',
              required=True)
@click.option('-y', '--year', type=click.IntRange(2011, 2020),
              help='Year between 2011 and 2020', required=True)
def main(resolution, month, year):
    '''Program for downloading files from 'www.smashingmagazine.com"'''
    # Validating values given to Month and ImangeDownloader
    try:
        month_obj = Month(month)
        image_downloader = ImageDownloader(resolution)
    except ValueError as err:
        message, value = err.args
        print('{0}: {1}'.format(message, value))
        return

    print('Trying to establish connection...')

    # Getting url link in expected format
    url = image_downloader.get_url(URL, month_obj.number, month_obj.name, year)

    # Making GET request, createing storage directory for images,
    # parsing html page for image links with given parameters
    try:
        content = image_downloader.fetch_content(url, timeout=5)
        storage_path = image_downloader.create_directory(
            BASE_DIR, month_obj.name, year)
    except Exception as err:
        print(err)
        return
    else:
        image_links = image_downloader.get_image_links(content)
        if not image_links:
            print('Unable to download images with given parameters.')
            return

    print('Connection established, start downloading...')

    # Asynchronously downloading images
    downloaded_image_count = asyncio.run(
        image_downloader.download_all(storage_path, image_links))

    if downloaded_image_count:
        print('\nDownload complete. Downloaded {} images.'.format(downloaded_image_count))
    else:
        print('Undefined issues occurred while attempting to download images.')


if __name__ == '__main__':
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    URL = 'www.smashingmagazine.com'
    main()
