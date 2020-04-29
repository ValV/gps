import os
import re
import requests

from .config import Config

def download(source: str, config: Config, chunk_size=524288, index=None) -> str:
    def progress(percent: int) -> int:
        if config.verbose:
            if percent == 100:
                print(percent, '- done.')
            elif percent % 10 == 0:
                print(percent, end='', flush=True)
            elif percent % 2 == 0:
                print('.', end='', flush=True)
        return percent

    filename: str = None
    try:
        assert config.output, ('Will not download: no path / disabled.')
        if not os.path.exists(config.output):
            os.makedirs(config.output)

        r = requests.get(source, auth=(config.username, config.password),
                         stream=True)
        r.raise_for_status()
        d = r.headers['content-disposition']

        filename = re.findall('filename="(.+)"', d)[0]
        filesize = int(re.findall('/(.+)', r.headers['content-range'])[0])

        downloaded = 1
        completed = 0

        prefix = '\n{0:3d} '.format(index) if type(index) is int else '\n'
        print(f'{prefix}{filename}')

        target = os.path.join(config.output, filename)
        if os.path.exists(target) and os.stat(target).st_size == filesize:
            print(f'File already exists. Skipping...')
            return filename
        with open(target, 'wb') as f:
            progress(0)
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = int(downloaded / filesize * 100)
                    if percent > completed:
                        completed = progress(percent)
            f.flush()
    except Exception as ex:
        print(f'\n{type(ex).__name__}', ex.args)
        print(ex)
        filename = None

    return filename
