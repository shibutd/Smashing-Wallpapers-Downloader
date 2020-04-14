import unittest
from unittest import mock
from click.testing import CliRunner
import requests
from downloader import main, Month, ImageDownloader


class MissingInputTests(unittest.TestCase):
    runner = CliRunner()

    def test_only_resolution_input(self):
        '''Test if we can't launch program with only resolution input'''
        test_cases = ['-r 64x64', '-r 1280x1024', '--resolution 1920x1080']
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='1')
                self.assertIn('Error', result.output)
                self.assertIn("Missing option '-m' / '--month'",
                              result.output)
                self.assertEqual(2, result.exit_code)

    def test_only_month_input(self):
        '''Test if we can't launch program with only month input'''
        test_cases = ['-m may', '-m 5', '--month December']
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='1')
                self.assertIn('Error', result.output)
                self.assertIn("Missing option '-r' / '--resolution'",
                              result.output)
                self.assertEqual(2, result.exit_code)

    def test_only_year_input(self):
        '''Test if we can't launch program with only year input'''
        test_cases = ['-y 2013', '--year 2019']
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='1')
                self.assertIn('Error', result.output)
                self.assertIn("Missing option '-r' / '--resolution'",
                              result.output)
                self.assertEqual(2, result.exit_code)


class InvalidInputTests(unittest.TestCase):
    runner = CliRunner()

    def test_invalid_resolution_input(self):
        '''Test if we can't launch program with invalid resolution input'''
        test_cases = [
            '-r 64x64 -m May -y 2019',
            '-r abcde -m May -y 2019',
            '-r 1920x1080x -m May -y 2019',
            '-r 19820x1080 -m May -y 2019',
        ]
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='3')
                self.assertIn("Resolution value is not valid",
                              result.output)
                self.assertEqual(0, result.exit_code)

    def test_invalid_month_input(self):
        '''Test if we can't launch program with invalid month input'''
        test_cases = [
            '-r 1280x1024 -m 0 -y 2019',
            '-r 1280x1024 -m 13 -y 2019',
            '-r 1280x1024 -m Semteber -y 2019',
            '-r 1280x1024 -m December_ -y 2019',
        ]
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='3')
                self.assertIn("Month value is not valid",
                              result.output)
                self.assertEqual(0, result.exit_code)

    def test_invalid_year_input(self):
        '''Test if we can't launch program with invalid year input'''
        test_cases = [
            '-r 1280x1024 -m May -y 12',
            '-r 1280x1024 -m May -y 2056',
            '-r 1280x1024 -m May -y abcde',
            '-r 1280x1024 -m May -y 2019x',
        ]
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='3')
                self.assertIn('Error', result.output)
                self.assertIn("Invalid value for '-y' / '--year'",
                              result.output)
                self.assertEqual(2, result.exit_code)


class MonthClassTests(unittest.TestCase):
    def test_month_valid_value(self):
        '''Test if we can create Month object with valid input'''
        test_cases = [
            ('may', 5, 'May'),
            ('5', 5, 'May'),
            ('octOBeR', 10, 'October'),
            ('DECEMBER', 12, 'December')
        ]
        for value, exp_number, exp_name in test_cases:
            with self.subTest(x=value):
                month = Month(value)
                self.assertEqual(month.validate_input(value), value)
                self.assertEqual(month.number, exp_number)
                self.assertEqual(month.name, exp_name)

    def test_month_invalid_value(self):
        '''Test if we can't create Month object with invalid input'''
        test_cases = ['', '0', '13', 'Octob_er', 'Decemberex']
        for value in test_cases:
            with self.subTest(x=value):
                self.assertRaises(ValueError, Month, value)


class ImageDownloaderClassTests(unittest.TestCase):
    base_resolution = '640x480'

    def test_resolution_valid_value(self):
        '''Test if we can create ImageDownloader object with valid input'''
        test_cases = ['640x480', '1280x1024', '1920x1080']
        for value in test_cases:
            with self.subTest(x=value):
                image_downloader = ImageDownloader(value)
                self.assertEqual(
                    image_downloader.validate_input(value), value)
                self.assertEqual(image_downloader.resolution, value)

    def test_resolution_invalid_value(self):
        '''Test if we can't create ImageDownloader object with invalid input'''
        test_cases = [
            '',
            '64x48',
            '1280x1024-25',
            '1920xx1080',
            '1920x1080x1080',
            '15360x8640'
        ]
        for value in test_cases:
            with self.subTest(x=value):
                self.assertRaises(ValueError, ImageDownloader, value)

    def test_getting_url(self):
        '''Test if ImageDownloader object can return url in expected format'''
        test_cases = [
            (
                ('abc.com', 5, 'May', 2015),
                'https://abc.com/2015/04/desktop-wallpaper-calendars-may-2015/'
            ),
            (
                ('abc.com', 11, 'November', 2013),
                'https://abc.com/2013/10/desktop-wallpaper-calendars-november-2013/'
            ),
            (
                ('abc.com', 1, 'January', 2019),
                'https://abc.com/2019/12/desktop-wallpaper-calendars-january-2019/'
            )
        ]
        image_downloader = ImageDownloader(self.base_resolution)
        for x, exp_output in test_cases:
            with self.subTest(x=x):
                self.assertEqual(image_downloader.get_url(*x), exp_output)

    def mocked_requests_get(*args, **kwargs):
        '''Mocking for request.get'''
        class MockResponse:
            def __init__(self, content, status_code):
                self.content = content
                self.status_code = status_code

            def raise_for_status(self):
                if self.status_code != 200:
                    raise requests.HTTPError()
                return self.status_code

        if args[0] == 'http://someurl.com/test':
            return MockResponse('some_data', 200)
        elif args[0] == 'http://someotherurl.com/test':
            return MockResponse('other_data', 200)
        elif args[0] == 'http://nonexistenturl.com/test':
            return MockResponse(None, 404)
        elif args[0] == 'http://unabletoconnecturl.com/test':
            raise requests.Timeout()
        raise requests.RequestException()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_making_request(self, mock_get):
        '''Test if ImageDownloader object can make valid request'''
        image_downloader = ImageDownloader(self.base_resolution)

        resp = image_downloader.make_request('http://someurl.com/test')
        self.assertEqual(resp.content, 'some_data')
        self.assertEqual(resp.status_code, 200)

        resp = image_downloader.make_request('http://someotherurl.com/test')
        self.assertEqual(resp.content, 'other_data')
        self.assertEqual(resp.status_code, 200)

        with self.assertRaises(Exception) as err:
            image_downloader.make_request('http://nonexistenturl.com/test')
        self.assertIn('Error', err.exception.args[0])

        with self.assertRaises(Exception) as err:
            image_downloader.make_request('http://unabletoconnecturl.com/test')
        self.assertIn('Connection timed out', err.exception.args)

        with self.assertRaises(Exception) as err:
            image_downloader.make_request('http://otherunknownurl.com/test')
        self.assertIn('Unable to establish connection', err.exception.args)

    def test_getting_image_links(self):
        '''Test if ImageDownloader object can return links from html content'''
        response_content = '''
        <a href=http://files.com/wallpapers/cal/may-19-hello-spring-cal-800x480.png \
title="Hello Spring! - 800x480">800x480</a>,<a href=http://files.com/wallpapers/nocal\
/may-19-hello-spring-nocal-800x480.png title="Hello Spring! - 800x480">800x480</a>,\
<a href=http://files.com/wallpapers/nocal/may-19-hello-spring-nocal-1024x768.png \
title="Hello Spring! - 1024x768">1024x768</a>'''
        test_cases = [
            (
                '800x480',
                [
                    'http://files.com/wallpapers/cal/may-19-hello-spring-cal-800x480.png',
                    'http://files.com/wallpapers/nocal/may-19-hello-spring-nocal-800x480.png'
                ]
            ),
            (
                '1024x768',
                ['http://files.com/wallpapers/nocal/may-19-hello-spring-nocal-1024x768.png']
            )
        ]
        for resolution, exp_output in test_cases:
            with self.subTest(x=resolution):
                self.assertEqual(
                    ImageDownloader(resolution).get_image_links(response_content),
                    exp_output
                )

    @mock.patch('downloader.os')
    def test_creating_directory(self, mock_os):
        '''Test if ImageDownloader object can create directory'''
        base_directory, month, year = '/', 'may', 2015
        directory_name = 'Smashing_wallpaper_{0}_{1}'.format(month, str(year))

        ImageDownloader(self.base_resolution).create_directory(
            base_directory, month, year)

        self.assertTrue(
            mock_os.makedirs.called_with(
                mock_os.path.join(base_directory, directory_name),
                exist_ok=True
            )
        )

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    @mock.patch('downloader.os')
    @mock.patch('__main__.open')
    def test_downloading_image(self, mock_open, mock_os, mocked_requests_get):
        '''Test if ImageDownloader object can download file'''
        pass
        # storage_path = '/'

        # link = 'http://nonexistenturl.com/test'
        # self.assertFalse(
        #     ImageDownloader(self.base_resolution).download_image(storage_path, link))

        # link = 'http://someurl.com/test'
        # ImageDownloader(self.base_resolution).download_image(storage_path, link)

        # self.assertTrue(mock_open.called_with(
        #     mock_os.path.join(storage_path, 'test'), 'wb'))


if __name__ == '__main__':
    unittest.main()
