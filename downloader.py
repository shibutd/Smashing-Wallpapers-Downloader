import os
import re
import calendar
import click
import requests
from bs4 import BeautifulSoup
# import wget


class Month:

    def __init__(self, month):
        # assert self.is_valid(month), 'Month is not valid'
        self._month = month

    @property
    def number(self):
        if Month.is_valid(self._month):
            return (int(self._month) if self._month.isdigit()
                    else list(calendar.month_name).index(
                        self._month.lower().capitalize()))

    @property
    def name(self):
        if Month.is_valid(self._month):
            return (self._month.lower().capitalize()
                    if not self._month.isdigit()
                    else calendar.month_name[int(self._month)])

    @staticmethod
    def is_valid(month):
        if (month.isdigit() and 1 <= int(month) <= 12) or \
                (month.isalpha() and month.lower().capitalize()
                    in list(calendar.month_name)):
            return True
        else:
            return False


class ImageDownloader:

    def __init__(self, resolution):
        # assert self.resolution_is_valid(resolution), 'Resolution is not valid'
        self.resolution = resolution

    @staticmethod
    def resolution_is_valid(resolution):
        match = re.search('^\d{3,4}x\d{3,4}$', resolution)
        if not match:
            return False
        return True

    def get_url(self, url, month_number, month_name, year):
        month_number = str(range(1, 13)[month_number - 2])
        converted_month_number = month_number if len(month_number) == 2 \
            else '0' + str(month_number)

        url = 'https://{}/{}/{}/desktop-wallpaper-calendars-{}-{}/'.format(
            url, str(year), converted_month_number,
            month_name.lower(), str(year)
        )
        return url

    def make_request(self, url, **kwargs):
        try:
            response = requests.get(url, **kwargs)
            response.raise_for_status()
        except requests.Timeout:
            print('Connection timed out')
            return None
        except requests.HTTPError as err:
            print(f'Error {err.response.status_code}')
            return None
        except requests.RequestException:
            print('Unable to establish connection')
            return None
        else:
            return response

    def get_image_links(self, content):
        soup = BeautifulSoup(content, 'lxml')
        image_links = []

        for link in soup.find_all('a'):
            if link.text == self.resolution:
                image_links.append(link.get('href'))
        return image_links

    def download_image(self, storage_path, link):
        response = self.make_request(link, timeout=5, stream=True)
        if not response:
            return False
        # wget.download(link, out=storage_path)
        image_name = link[link.rfind('/') + 1:]
        with open(os.path.join(
                storage_path,
                image_name), 'wb') as image_file:

            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    image_file.write(chunk)
        return True


@click.command()
@click.option('-r', '--resolution',
              help='Resolution, example: 1920x1080', required=True)
@click.option('-m', '--month',
              help='Month, number or text format, example: 12 or December',
              required=True)
@click.option('-y', '--year', type=click.IntRange(2011, 2020),
              help='Year between 2011 and 2020', required=True)
def main(resolution, month, year):
    if not Month.is_valid(month):
        print('Month is not valid')
    elif not ImageDownloader.resolution_is_valid(resolution):
        print('Resolution is not valid')
    else:
        month_obj = Month(month)
        image_downloader = ImageDownloader(resolution)

    url = image_downloader.get_url(URL, month_obj.number, month_obj.name, year)

    print('Trying to establish connection...')

    response = image_downloader.make_request(url, timeout=5)
    if not response:
        return

    image_links = image_downloader.get_image_links(response.content)
    if not image_links:
        print('Unable to download images with given parameters')
        return

    print('Connection established, start downloading...')

    storage_path = os.path.join(
        BASE_DIR,
        f'Smashing_wallpaper_{month_obj.name}_{str(year)}'
    )
    os.makedirs(storage_path, exist_ok=True)

    downloaded_image_count = 0
    for link in image_links:
        if image_downloader.download_image(storage_path, link):
            downloaded_image_count += 1

    if downloaded_image_count:
        print(f'\nDownloaded {downloaded_image_count} images')
    else:
        print('Undefined issues occurred while attempting to download images')


if __name__ == '__main__':
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    URL = 'www.smashingmagazine.com'
    main()
