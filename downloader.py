import os
import re
import calendar
import click
import requests
from bs4 import BeautifulSoup
# import wget


class Month:
    '''Class to represent month.

    Methods
        validate_input(value: str)
            Makes sure user input month is valid

        number()
            Returns month number: 1, 2, 3, ..., 12

        name()
            Returns month name: January, February, ..., December
    '''

    def __init__(self, month):
        self._month = self.validate_input(month)

    def validate_input(self, value):
        if value.isdigit() and 1 <= int(value) <= 12 or \
                (value.isalpha() and value.lower().capitalize()
                    in list(calendar.month_name)):
            return value
        raise ValueError('Month value is not valid', value)

    @property
    def number(self):
        if self._month.isdigit():
            return int(self._month)
        else:
            month_name = self._month.lower().capitalize()
            return list(calendar.month_name).index(month_name)

    @property
    def name(self):
        if not self._month.isdigit():
            return self._month.lower().capitalize()
        else:
            return calendar.month_name[int(self._month)]


class ImageDownloader:
    '''Class to represent downloader for images.

    Methods
        validate_input(value: str)
            Makes sure user input resolution is valid

        get_url(url:str, month_number:int, month_name, year)
            Creates url of required form for further request

        make_request(url:str)
            Makes HTTP GET request to given url

        get_image_links(content: bytes)
            Parses page for links with required resolution

        create_directory(basic_directory:str, month_name:str, year:int)
            Creates directory to store downloaded files

        download_image(storage_path:str, link:str)
            Makes request to given link, than downloads image from link
    '''

    def __init__(self, resolution):
        self.resolution = self.validate_input(resolution)

    def validate_input(self, value):
        match = re.search('^\d{3,4}x\d{3,4}$', value)
        if match:
            return value
        raise ValueError('Resolution value is not valid', value)

    def get_url(self, url, month_number, month_name, year):
        # Convert month number. Value for request must have value
        # (month_number - 2) and form: '01', '02',.. '12'
        month_number_str = str(range(1, 13)[month_number - 2])
        if len(month_number_str) == 2:
            converted_month_number = month_number_str
        else:
            converted_month_number = '0{}'.format(month_number_str)

        url = 'https://{0}/{1}/{2}/desktop-wallpaper-calendars-{3}-{1}/'.format(
            url,
            str(year),
            converted_month_number,
            month_name.lower(),
            # str(year)
        )
        return url

    def make_request(self, url, **kwargs):
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
            return response

    def get_image_links(self, content):
        soup = BeautifulSoup(content, 'lxml')
        image_links = []

        for link in soup.find_all('a'):
            if link.text == self.resolution:
                image_links.append(link.get('href'))
        return image_links

    def create_directory(self, basic_directory, month_name, year):
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

    def download_image(self, storage_path, link):
        try:
            response = self.make_request(link, timeout=5, stream=True)
        except Exception:
            return False
        # wget.download(link, out=storage_path)
        image_name = link[link.rfind('/') + 1:]
        with open(os.path.join(storage_path, image_name), 'wb') as image_file:
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
    try:
        month_obj = Month(month)
        image_downloader = ImageDownloader(resolution)
    except ValueError as err:
        message, value = err.args
        print('{0}: {1}'.format(message, value))
        return

    url = image_downloader.get_url(URL, month_obj.number, month_obj.name, year)

    print('Trying to establish connection...')

    try:
        response = image_downloader.make_request(url, timeout=5)
    except Exception as err:
        print(err)
        return

    image_links = image_downloader.get_image_links(response.content)
    if not image_links:
        print('Unable to download images with given parameters')
        return

    try:
        storage_path = image_downloader.create_directory(
            BASE_DIR, month_obj.name, year)
    except Exception as err:
        print(err)
        return

    print('Connection established, start downloading...')

    downloaded_image_count = 0
    for link in image_links:
        if image_downloader.download_image(storage_path, link):
            downloaded_image_count += 1

    if downloaded_image_count:
        print('\nDownloaded {} images'.format(downloaded_image_count))
    else:
        print('Undefined issues occurred while attempting to download images')


if __name__ == '__main__':
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    URL = 'www.smashingmagazine.com'
    main()
