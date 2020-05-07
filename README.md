# Smashing Wallpaper Downloader

Cli утилита, которая скачивает с сайта **Smashing Magazine** все обои в требуемом разрешение за указанный месяц-год в текущую директорию пользователя.

```
$ python downloader.py --help
Usage: downloader.py [OPTIONS]

  Program for downloading files from 'www.smashingmagazine.com"

Options:
  -r, --resolution TEXT     Resolution, example: 1920x1080  [required]
  -m, --month TEXT          Month, number or text format, example: 12 or
                            December  [required]

  -y, --year INTEGER RANGE  Year between 2011 and 2020  [required]
  --help                    Show this message and exit.
  ```
  
  Например, чтобы скачать все изображения в разрешении 1920 x 1080 за май 2019 года:
```
$ python downloader.py --resolution=1920x1080 --month=May --year=2019
```
