import unittest
from unittest import mock
from click.testing import CliRunner
from downloader import main, Month, ImageDownloader


class TestMissingInput(unittest.TestCase):
    runner = CliRunner()
    # def setUP(self):
    #     self.runner = CliRunner()
    #     return self.runner

    def test_only_resolution_input(self):
        test_cases = ['-r 64x64', '-r 1280x1024', '--resolution 1920x1080']
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='1')
                self.assertIn("Error: Missing option '-m' / '--month'",
                              result.output)
                self.assertEqual(2, result.exit_code)

    def test_only_month_input(self):
        test_cases = ['-m may', '-m 5', '--month December']
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='1')
                self.assertIn("Error: Missing option '-r' / '--resolution'",
                              result.output)
                self.assertEqual(2, result.exit_code)

    def test_only_year_input(self):
        test_cases = ['-y 2013', '--year 2019']
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='1')
                self.assertIn("Error: Missing option '-r' / '--resolution'",
                              result.output)
                self.assertEqual(2, result.exit_code)


class TestInvalidInput(unittest.TestCase):
    runner = CliRunner()

    def test_invalid_resolution_input(self):
        test_cases = [
            '-r 64x64 -m May -y 2019',
            '-r abcde -m May -y 2019',
            '-r 1920x1080x -m May -y 2019',
            '-r 19820x1080 -m May -y 2019',
        ]
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='3')
                self.assertIn("Resolution is not valid",
                              result.output)
                self.assertEqual(1, result.exit_code)

    def test_invalid_month_input(self):
        test_cases = [
            '-r 1280x1024 -m 0 -y 2019',
            '-r 1280x1024 -m 13 -y 2019',
            '-r 1280x1024 -m Semteber -y 2019',
            '-r 1280x1024 -m December_ -y 2019',
        ]
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='3')
                self.assertIn("Month is not valid",
                              result.output)
                self.assertEqual(1, result.exit_code)

    def test_invalid_year_input(self):
        test_cases = [
            '-r 1280x1024 -m May -y 12',
            '-r 1280x1024 -m May -y 2056',
            '-r 1280x1024 -m May -y abcde',
            '-r 1280x1024 -m May -y 2019x',
        ]
        for x in test_cases:
            with self.subTest(x=x):
                result = self.runner.invoke(main, x.split(), input='3')
                self.assertIn("Error: Invalid value for '-y' / '--year'",
                              result.output)
                self.assertEqual(2, result.exit_code)


class TestMonthClass(unittest.TestCase):
    def test_month_valid_value(self):
        test_cases = [
            ('may', 5, 'May'),
            ('5', 5, 'May'),
            ('octOBeR', 10, 'October'),
            ('DECEMBER', 12, 'December')
        ]
        for x, exp_number, exp_name in test_cases:
            with self.subTest(x=x):
                month = Month(x)
                self.assertEqual(month._month, x)
                self.assertTrue(Month.is_valid(x))
                self.assertEqual(month.number, exp_number)
                self.assertEqual(month.name, exp_name)

    def test_month_invalid_value(self):
        test_cases = ['0', '13', 'Octob_er', 'Decemberex']
        for x in test_cases:
            with self.subTest(x=x):
                month = Month(x)
                self.assertEqual(month._month, x)
                self.assertFalse(Month.is_valid(x))
                self.assertEqual(month.number, None)
                self.assertEqual(month.name, None)


class ImageDownloaderClass(unittest.TestCase):
    base_resolution = '640x480'

    def test_resolution_valid_value(self):
        test_cases = ['640x480', '1280x1024', '1920x1080']
        for x in test_cases:
            with self.subTest(x=x):
                image_downloader = ImageDownloader(x)
                self.assertEqual(image_downloader.resolution, x)
                self.assertTrue(ImageDownloader.resolution_is_valid(x))

    def test_resolution_invalid_value(self):
        test_cases = ['', '64x48', '1280x1024-25', '1920xx1080', '15360x8640']
        for x in test_cases:
            with self.subTest(x=x):
                image_downloader = ImageDownloader(x)
                self.assertEqual(image_downloader.resolution, x)
                self.assertFalse(ImageDownloader.resolution_is_valid(x))

    def test_getting_url(self):
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
        class MockResponse:
            def __init__(self, content, status_code):
                self.content = content
                self.status_code = status_code

            def raise_for_status(self):
                return self.status_code

        if args[0] == 'http://someurl.com/test':
            return MockResponse('some_data', 200)
        elif args[0] == 'http://someotherurl.com/anothertest':
            return MockResponse('other_data', 200)

        return MockResponse(None, 404)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_making_request(self, mock_get):
        image_downloader = ImageDownloader(self.base_resolution)

        resp = image_downloader.make_request('http://someurl.com/test')
        self.assertEqual(resp.content, 'some_data')
        self.assertEqual(resp.status_code, 200)

        resp = image_downloader.make_request('http://someotherurl.com/anothertest')
        self.assertEqual(resp.content, 'other_data')
        self.assertEqual(resp.status_code, 200)

        resp = image_downloader.make_request('http://nonexistenturl.com/cantfindme')
        self.assertIsNone(resp.content)
        self.assertEqual(resp.status_code, 404)

    def test_getting_image_links(self):
        response_content = '''
        <a href=http://files.smashingmagazine.com/wallpapers/may-19/hello-spring/cal\
/may-19-hello-spring-cal-800x480.png title="Hello Spring! - 800x480">800x480</a>,\
<a href=http://files.smashingmagazine.com/wallpapers/may-19/hello-spring/nocal\
/may-19-hello-spring-nocal-800x480.png title="Hello Spring! - 800x480">800x480</a>,\
<a href=http://files.smashingmagazine.com/wallpapers/may-19/hello-spring/nocal\
/may-19-hello-spring-nocal-1024x768.png title="Hello Spring! - 1024x768">1024x768</a>'''
        test_cases = [
            (
                '800x480',
                [
                    'http://files.smashingmagazine.com/wallpapers/may-19/hello-spring/cal/may-19-hello-spring-cal-800x480.png',
                    'http://files.smashingmagazine.com/wallpapers/may-19/hello-spring/nocal/may-19-hello-spring-nocal-800x480.png'
                ]
            ),
            (
                '1024x768',
                ['http://files.smashingmagazine.com/wallpapers/may-19/hello-spring/nocal/may-19-hello-spring-nocal-1024x768.png']
            )
        ]
        for resolution, exp_output in test_cases:
            with self.subTest(x=resolution):
                self.assertEqual(
                    ImageDownloader(resolution).get_image_links(response_content),
                    exp_output
                )


if __name__ == '__main__':
    unittest.main()
