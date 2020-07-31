import os
import re
import time
import requests

from pprint import pprint # DEBUG
from typing import Any, Dict, List, Union

from .config import Config
from .model import Snapshot


class DataHub:
    def __init__(self, config: Config, limit: int = None) -> List[Dict]:
        self.max_iterations = 1000
        self.max_downloaded = limit
        self.snapshots: List[Snapshot] = None
        self.config = config

    def search(self, params: Dict[str, Any]) -> List[Snapshot]:
        assert self.config.has_credentials # TODO: return []
        if self.config.verbose:
            print("\nStarting a new search...")

        snapshots: List[Snapshot] = []
        total_items: int = None
        for i in range(self.max_iterations):
            try:
                r = requests.get(
                    url = f"https://scihub.copernicus.eu/dhus/search",
                    params = OpenSearchAPI.get_api_params(params),
                    auth=(self.config.username, self.config.password)
                )
            except Exception as ex:  # TODO: specify type
                if self.config.verbose:
                    print(type(ex).__name__, ex.args)
                    print("No connection, taking a timeout...")
                time.sleep(1)
                continue

            try:
                items = r.json()['feed']['entry']
                if not total_items:
                    total_items = int(
                        r.json()['feed']['opensearch:totalResults']
                    )
                # print(f"DEBUG: === response ===")
                # pprint(r.json()) # DEBUG
            except KeyError:
                if self.config.verbose:
                    print("No more results...")
                break

            if isinstance(items, list):
                for item in items:
                    snapshots.append(self.compose_snapshot(item))
            elif isinstance(items, dict):
                snapshots.append(self.compose_snapshot(items))
            else:
                raise ValueError(f"bad feed entry type {type(items)}")

            if self.config.verbose:
                print(f"{i:5d}: {len(items)} records out of",
                      f"{total_items} fetched")
            params['start'] += 100
            if len(snapshots) >= self.max_downloaded:
                break
        self.snapshots = snapshots

        return self.snapshots

    def compose_snapshot(self, response: Dict[str, Any]) -> Snapshot:
        cloud_coverage = None
        # print(f"DEBUG: {type(response)}")
        # print(f"DEBUG: {response.keys()}")
        if 'double' in response:
            doubles = response['double']
            if isinstance(doubles, dict):
                doubles = [doubles]
            cloud_coverage = self.get_param(doubles, 'cloudcoverpercentage')

        return Snapshot.Schema().load(dict(
            uuid=response['id'],
            link=response['link'][0]['href'],
            icon=self.get_param(response['link'], 'icon'),
            size=self.get_param(response['str'], 'size'),
            title=response['title'],
            polygon=self.get_param(response['str'], 'footprint'),
            begin_position=self.get_param(response['date'], 'beginposition'),
            end_position=self.get_param(response['date'], 'endposition'),
            ingestion_date=self.get_param(response['date'], 'ingestiondate'),
            cloud_coverage=cloud_coverage,
            instrument=self.get_param(response['str'], 'instrumentshortname'),
        ))

    def get_param(self, fields: List[Dict[str, Any]], param_name: str) -> Any:
        for field in fields:
            if field.get('name') == param_name:
                return field.get('content')
            if field.get('rel') == param_name:
                return field.get('href')

        return None

    def _download(self, source: str, chunk_size=524288, index=None) -> str:
        def progress(percent: int) -> int:
            if self.config.verbose:
                if percent == 100:
                    print(percent, '- done.')
                elif percent % 10 == 0:
                    print(percent, end='', flush=True)
                elif percent % 2 == 0:
                    print('.', end='', flush=True)
            return percent

        filename: str = None

        try:
            #print(f"DEBUG: _download.source = {source}")
            assert self.config.output, "Can't download with no output!"
            if not os.path.exists(self.config.output):
                os.makedirs(self.config.output)

            r = requests.get(source, auth=(self.config.username,
                                           self.config.password),
                             stream=True)
            r.raise_for_status()
            d = r.headers['content-disposition']

            filename = re.findall('filename="(.+)"', d)[0]
            filesize = int(re.findall('/(.+)', r.headers['content-range'])[0])
            #print(f"DEBUG: filename = '{filename}', filesize = {filesize}")

            downloaded = 1
            completed = 0

            if self.config.verbose:
                if type(index) is int:
                    prefix = f"\n{index:3d} "
                else:
                    prefix = f"\n"
                print(f"{prefix}{filename}")

            target = os.path.join(self.config.output, filename)
            if os.path.exists(target) and os.stat(target).st_size == filesize:
                if self.config.verbose:
                    print(f"File already exists. Skipping...")
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
            if self.config.verbose:
                print(f"\n{type(ex).__name__}", ex.args)
                print(ex)
            filename = None

        return filename

    Sources = Union[int, List[int], str, List[str], Snapshot, List[Snapshot]]
    def download(self, sources: Sources) -> List[str]:
        files = []

        if not isinstance(self.snapshots, List):
            self.search(self.config.search)

        if isinstance(sources, List):
            for i, source in enumerate(sources):
                if isinstance(source, Snapshot):
                    source = source.download_link
                elif isinstance(source, int):
                    if source < len(self):
                        i = source
                        source = self[i]
                    else:
                        continue
                files.append(self._download(source, index=i))
        else:
            source = sources
            if isinstance(source, int):
                if source < len(self):
                    source = self[source].download_link
                    files.append(self._download(source, index=sources))
            else:
                if isinstance(source, Snapshot):
                    source = source.link
                files.append(self._download(source))

        return files

    def download_all(self) -> List[str]:
        return self.download(self.snapshots)

    def __len__(self) -> int:
        return len(self.snapshots) if isinstance(self.snapshots, List) else 0

    def __getitem__(self, i: int) -> Snapshot:
        return self.snapshots[i] if isinstance(self.snapshoots, List) else None


class OpenSearchAPI:
    query_param_names = {
        'platformname',
        'beginposition',
        'endposition',
        'ingestiondate',
        'collection',
        'filename',
        'footprint',
        'orbitnumber',
        'lastorbitnumber',
        'relativeorbitnumber',
        'lastrelativeorbitnumber',
        'orbitdirection',
        'polarisationmode',
        'producttype',
        'sensoroperationalmode',
        'swathidentifier',
        'cloudcoverpercentage',
        'timeliness',
        # Treat specially (not a part of Copernicus Search API)
        'filenames'
    }

    @staticmethod
    def compose_query_params(params: Dict[str, Any]) -> str:
        return ' OR '.join(f"filename:{str(v)}" for v in params['filenames']) \
               if 'filenames' in params else \
               ' AND '.join(f"{k}:{str(v)}" for k, v in params.items())

    def get_api_params(params: Dict[str, Any]) -> Dict[str, Any]:
        query_params = {}
        request_params = {
            'rows': 100,
            'format': 'json'
        }
        for k, v in params.items():
            if k.lower() in OpenSearchAPI.query_param_names:
                query_params[k] = v
            else:
                request_params[k] = v

        request_params['q'] = OpenSearchAPI.compose_query_params(query_params)
        #print(f"DEBUG: request params = {request_params}")

        return request_params
