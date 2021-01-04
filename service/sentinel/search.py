import os
import re
import math
import time
import requests

from pprint import pprint # DEBUG
from json.decoder import JSONDecodeError
from typing import Any, Dict, List, Union

from .config import Config
from .model import Snapshot


class DataHub:
    def __init__(self, config: Config, limit: int = None,
            chunk_size: int = 45, url: str = None) -> List[Dict]:
        self.max_iterations = limit # 1000
        self.max_downloaded = limit
        self.snapshots: List[Snapshot] = None
        self.chunk_size = chunk_size
        self.config = config
        if not url:
            self.url = f"https://scihub.copernicus.eu/dhus/search"
        else:
            self.url = url

    def search(self, params: Dict[str, Any], area=None) -> List[Snapshot]:
        if not self.config.has_credentials:
            print(f"No credentials!")
            return []

        # Check search area WKT to be either POINT or POLYGON
        # (another WKT geometries are not supported by Copernicus API)
        if type(area) is str and area:
            wkt_split = area.split(maxsplit=1)
            try:
                assert len(wkt_split) == 2
                if wkt_split[0].lower() == 'polygon':
                    params['footprint'] = f"\"Intersects({area})\""
                elif wkt_split[0].lower() == 'point':
                    params['footprint'] = f"\"Intersects{wkt_split[1]}\""
                else:
                    raise ValueError
            except:
                print(f"WARNING: area WKT must be of type 'POINT' or 'POLYGON'")

        if self.config.verbose:
            print("\nStarting a new search...")

        snapshots: List[Snapshot] = []

        # Create 'filenames' list
        if 'filenames' in params and type(params['filenames']) is list:
            filenames = params['filenames']
        else:
            filenames = []
        # if filenames:
            # print(f"Splitting 'filenames' by {self.chunk_size} items...")
            # params['rows'] = self.chunk_size

        # Create 'filenames' generator from the list
        filenames = self._split(filenames)
        try:
            params['filenames'] = next(filenames)
        except StopIteration:
            # Start with zero generator from empty list
            params['filenames'] = []
        total_items = 0 # for page splitting
        total_found = 0 # for chunk splitting
        digits = math.ceil(math.log10(max(self.max_iterations,
                                          len(params['filenames'])))) + 1
        for i in range(self.max_iterations):
            #
            # Get response (retry by max_iterations, break by error)
            #
            try:
                params_ = OpenSearchAPI.get_api_params(params)
                r = requests.get(
                    url = self.url,
                    params = params_,
                    auth=(self.config.username, self.config.password)
                )
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if self.config.verbose:
                    print(type(e).__name__, '\n'.join(e.args))
                break
            except requests.exceptions.RequestException as e:
                if self.config.verbose:
                    print(type(e).__name__, '\n'.join(e.args))
                    print("No connection, taking a timeout...")
                time.sleep(2)
                continue

            #
            # Parse response (must be JSON format)
            #
            try:
                items = r.json()['feed']['entry']
                if not total_items:
                    total_items = int(
                        r.json()['feed']['opensearch:totalResults']
                    )

                # Fill 'snapshots' with search results
                if isinstance(items, list):
                    for item in items:
                        snapshots.append(self.compose_snapshot(item))
                elif isinstance(items, dict):
                    snapshots.append(self.compose_snapshot(items))
                else:
                    raise ValueError(f"bad feed entry type {type(items)}")

                if self.config.verbose:
                    # TODO: check params['start'] or total_found must be 0
                    print(f"{(params['start'] + total_found):+{digits}d}:",
                          f"{len(items)} records out of",
                          f"{total_items} fetched")

                # Either increment page start index or get next chunk
                if params['filenames']:
                    try:
                        total_found += len(items)
                        params['filenames'] = next(filenames)
                        params['start'] = 0 # TODO: check use cases
                    except StopIteration:
                        raise KeyError # FIXME: do better stop signalling
                else:
                    params['start'] += params['rows']

                if len(snapshots) >= self.max_downloaded:
                    break
            except KeyError:
                if self.config.verbose:
                    print("No more results...")
                break
            except JSONDecodeError:
                if self.config.verbose:
                    print(f"Bad JSON response:")
                    pprint(r.text)
                break
            except ValueError as e:
                print(f"ERROR: {e}\n")
                break

        self.snapshots = snapshots

        return self.snapshots

    def _split(self, source: List[Any]):
        items = self.chunk_size
        for i in range(0, len(source), items):
            yield source[i:i + items]

    def compose_snapshot(self, response: Dict[str, Any]) -> Snapshot:
        cloud_coverage = None
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

    request_param_names = {
            'start',
            'rows',
            'orderby'
    }

    @staticmethod
    def compose_query_params(params: Dict[str, Any]) -> str:
        return ' OR '.join(f"filename:{str(v)}" for v in params['filenames']) \
               if 'filenames' in params and type(params['filenames']) is list \
               and params['filenames'] else \
               ' AND '.join(f"{k}:{str(v)}" for k, v in params.items())

    def get_api_params(params: Dict[str, Any]) -> Dict[str, Any]:
        query_params = {}
        request_params = {
            'rows': 100,
            'format': 'json' # request for response as JSON format
        }
        for k, v in params.items():
            key = k.lower()
            if key in OpenSearchAPI.query_param_names:
                query_params[k] = v
            elif key in OpenSearchAPI.request_param_names:
                request_params[k] = v
            else:
                pass # TODO: log bad param names
        request_params['q'] = OpenSearchAPI.compose_query_params(query_params)

        return request_params
