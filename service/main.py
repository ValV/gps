import sys

import os
import zipfile
import tempfile
import sched, time
import numpy as np

from b3w import B3W
from glob import glob
from osgeo import gdal
from shutil import rmtree
from subprocess import Popen, PIPE, STDOUT
from typing import Any, List, Tuple, Set

from sentinel import Config
from sentinel import DataHub
from sentinel import Polygons
from utils import get_environment, print_snapshots, remove


# Main loop period (seconds)
INTERVAL: int = 10#0


def check_in_aws(s3: B3W, prefix: str, depth: int = 1) -> Set[str]:
    objects: Set[str] = set() #List[str] = []
    try:
        for s3o in s3.ls(prefix):
            if prefix:
                s3o = s3o.replace(prefix.strip('/'), '').strip('/')
            if not s3o:
                continue
            objects.add('/'.join(s3o.split('/')[:depth]))
    except Exception as e:
        #TODO: debug and handle different kinds of exceptions
        raise e

    return objects


def get_from_aws(s3: B3W, prefix: str,
        path: str = '/dev/shm/gps/input'
    ) -> List[str]:
    files: List[str] = []
    try:
        #objects = s3.ls(prefix)
        #print(f"DEBUG: objects = {objects}")
        extensions = ('.geojson', '.shp', '.shx', '.dbf', '.prj', '.cpg')
        for s3o in s3.ls(prefix):
            #print(f"DEBUG: get_from_aws s3o = {s3o}")
            if prefix:
                filename = s3o.replace(prefix.strip('/'), '').strip('/')
            else:
                filename = s3o
            if not filename.endswith(extensions):
                continue
            #filename = os.path.join(path, *filename.lstrip('/').split('/'))
            filename = os.path.join(path, *filename.split('/'))
            #print(f"DEBUG: {s3o} -> {filename}")
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            s3.get(s3o, filename)
            files.append(filename)
    except Exception as e:
        #TODO: debug and handle different kinds of exceptions
        raise e

    return files


def put_to_aws(s3: B3W, prefix: str,
        path: str = '/dev/shm/gps/output'
    ) -> List[str]:
    objects: List[str] = []
    try:
        path = os.path.normpath(path)
        for filename in glob(os.path.join(path, '**'),  recursive=True):
            if not os.path.isfile(filename):
                continue
            s3o = os.path.relpath(filename, path)
            if prefix:
                s3o = '/'.join([prefix.strip('/'), *s3o.split(os.path.sep)])
            else:
                s3o = '/'.join([*s3o.split(os.path.sep)])
            #print(f"DEBUG: '{filename}' -> '{s3o}'")
            s3.put(filename, s3o, force=True)
    except Exception as e:
        #TODO: debug and handle different kinds of exceptions
        raise e

    return objects


def remove_from_aws(s3: B3W, prefix: str) -> List[str]:
    # TODO: remove this function (DEBUG only)
    objects: List[str] = []
    try:
        #objects = s3.ls(prefix)
        #print(f"DEBUG: objects to remove = {objects}")
        for s3o in s3.ls(prefix):
            s3._B3W__s3r.Object(s3._B3W__bucket_name, s3o).delete()
            print(f"DEBUG: removed S3 object '{s3o}'")
            objects.append(s3o)
    except Exception as e:
        print(f"Error removing S3 object:\n{e}")

    return objects


def sync_with_aws(
        s3: B3W, prefix: str, data_hub: DataHub,
        snapshot: Any, path: str = '/dev/shm/gps/data'
    ) -> str:
    filename: str = None
    try:
        data_hub.config.output = os.path.join(path, snapshot.uuid)
        os.makedirs(data_hub.config.output, exist_ok=True)
        objects = s3.ls('/'.join([prefix, snapshot.uuid]))
        print(f"DEBUG: S3 objects = {objects}")
        #if len(objects) > 0:
        for s3o in objects:
            #s3o = s3o.replace(prefix, '').lstrip('/')
            if s3o.strip('/').endswith(snapshot.uuid):
                continue
            filename = os.path.join(path, s3o.replace(prefix, '').lstrip('/'))
            print(f"DEBUG: syncing '{s3o}' -> '{filename}'")
            s3.get(s3o, filename)
            break
        if not filename:
            data_hub.download(snapshot)
            #print(f"DEBUG: data_hub.config.output = {data_hub.config.output}")
            for filename in glob(os.path.join(data_hub.config.output, '*')):
            #print(f"DEBUG: filename = {filename}")
            #if len(filename) < 1:
            #    raise FileNotFoundError(f"failed to download {snapshot.uuid}!")
            #else:
            #    filename = filename[0]
                s3o = filename.replace(path, '').lstrip(os.path.sep)
                # TODO: check filename against snapshot.uuid
                s3o = '/'.join([prefix, s3o])
                print(f"DEBUG: syncing '{filename}' -> '{s3o}'")
                s3.put(filename, s3o)
                break
            if not filename:
                print(f"failed to download {snapshot.uuid}!")
        data_hub.config.output = None # TODO: devise something smart
    except FileNotFoundError as e:
        print(f"Failure: {e}")
    except Exception as e:
        #TODO: debug and handle different kinds of exceptions
        raise e

    return filename


def set_debug_aws() -> None:
    s3_id, s3_key, s3_bucket, s3_input, s3_output, s3_sync = get_environment()
    path_input, path_output = ('/dev/shm/gps/input', '/dev/shm/gps/output')
    path_data = '/dev/shm/gps/data'
    #print(f"DEBUG:\n\t{'S3_ID'.ljust(16)}{s3_id}"
    #      f"\n\t{'S3_KEY'.ljust(16)}{s3_key}"
    #      f"\n\t{'S3_BUCKET'.ljust(16)}{s3_bucket}"
    #      f"\n\t{'S3_INPUT'.ljust(16)}{s3_input}"
    #      f"\n\t{'S3_OUTPUT'.ljust(16)}{s3_output}"
    #      f"\n\t{'S3_SYNC'.ljust(16)}{s3_sync}")
    s3 = B3W(s3_bucket, s3_id, s3_key)
    # DEBUG: put test data to S3
    remove_from_aws(s3, s3_input + '/test')
    remove_from_aws(s3, s3_output + '/test')
    for filename in glob(os.path.join('data', '*')):
        #s3.put('data/geotiff.xml', '/'.join([s3_input, 'test', 'geotiff.xml']))
        s3o = '/'.join([s3_input, 'test', os.path.basename(filename)])
        s3.put(filename, s3o)
        print(f"DEBUG: '{filename}' -> '{s3o}'")
    #print(s3.ls(s3_input))
    #sys.exit(0)

    return None


def process_sentinel1(filename, path_output, area, shapes):
    title = os.path.splitext(os.path.basename(filename))[0]
    options_warp = {
            'format': 'GTiff',
            'dstSRS': 'EPSG:32640',
            'creationOptions': ['COMPRESS=DEFLATE'],
            'xRes': 40,
            'yRes': 40
    }
    with tempfile.TemporaryDirectory() as path_temp:
        with zipfile.ZipFile(filename, 'r') as archive:
            archive.extractall(path_temp)
            path_safe = glob(os.path.join(path_temp, f"*.SAFE"))[0]
            dataset = gdal.Open(path_safe, gdal.GA_ReadOnly)
            subsets = dataset.GetSubDatasets()
            datasets = {}
            for i, p in enumerate(['HH', 'HV', 'RGB']):
                print(f"Reading {subsets[i][1]}...")
                datasets[p] = gdal.Open(subsets[i][0], gdal.GA_ReadOnly)
            filenames = []
            name_area = os.path.splitext(os.path.basename(area))[0]
            print(f"Warping polarizations...")
            for name, source in datasets.items():
                #
                # Prepare filenames and paths
                #
                for shape in shapes:
                    if shape:
                        name_shape = os.path.basename(shape)
                        name_shape = os.path.splitext(name_shape)[0]
                        data_prefix = f"{name_area}_{name_shape}"
                        options_cutline = {'cutlineDSName': shape,
                                           'cropToCutline': True}
                    else:
                        data_prefix = f"{name_area}"
                        options_cutline = {}
                    data_output = os.path.join(path_output, data_prefix)
                    if not name in ['RGB', 'INV']:
                        data_output = os.path.join(data_output, name.lower())
                        os.makedirs(data_output, exist_ok=True)
                        print(f"{data_output.replace(path_output, '')}")
                        destination = f"{os.path.join(data_output, title)}.tiff"
                        filenames.append(destination)
                        gdal.Warp(destination, source, **options_warp,
                                  **options_cutline)
                    else:
                        # Basic RGB processing
                        driver_mem = gdal.GetDriverByName('MEM')
                        memoset = driver_mem.CreateCopy('', source, 0)
                        band_hh = memoset.GetRasterBand(1)
                        image_hh = band_hh.ReadAsArray()
                        mask_hh = image_hh == 0
                        image_hh = np.ma.array(image_hh, mask=mask_hh,
                                               dtype=np.float32)
                        del mask_hh
                        band_hv = memoset.GetRasterBand(2)
                        image_hv = band_hv.ReadAsArray()
                        mask_hv = image_hv == 0
                        image_hv = np.ma.array(image_hv, mask=mask_hv,
                                               dtype=np.float32)
                        del mask_hv
                        stats_hh = (image_hh.mean().astype(np.float32),
                                    image_hh.std().astype(np.float32))
                        stats_hv = (image_hv.mean().astype(np.float32),
                                    image_hv.std().astype(np.float32))
                        image_hh = np.ma.tanh(image_hh / (stats_hh[0] + 2 *
                                                          stats_hh[1]))
                        image_hv = np.ma.tanh(image_hv / (stats_hv[0] + 2 *
                                                          stats_hv[1]))
                        image_ratio = image_hh / image_hv
                        stats_ratio = (image_ratio.mean().astype(np.float32),
                                       image_ratio.std().astype(np.float32))
                        image_ratio = image_ratio / image_ratio.max()
                        image_negative = (np.float32(1) -
                                          np.ma.tanh(image_hh / image_hv))
                        # Convert to byte type
                        image_hh = (image_hh * 254 + 1).astype(np.uint8)
                        image_hv = (image_hv * 254 + 1).astype(np.uint8)
                        image_ratio = (image_ratio * 254 + 1).astype(np.uint8)
                        image_negative = (image_negative * 254 + 1)\
                                         .astype(np.uint8)
                        # Write channels to the MEM dataset
                        memoset.AddBand()
                        band_ex = memoset.GetRasterBand(3)
                        band_ex.SetColorInterpretation(gdal.GCI_BlueBand)
                        band_hh.WriteArray(image_hh)
                        band_hh.SetColorInterpretation(gdal.GCI_RedBand)
                        band_hv.WriteArray(image_hv)
                        band_hv.SetColorInterpretation(gdal.GCI_GreenBand)
                        # Create ratio band (HH, HV, HH/HV)
                        band_ex.WriteArray(image_ratio)
                        band_ex.SetMetadata({'POLARISATION': 'HH/HV',
                                             'SWATH': 'EW'})
                        path_ratio = os.path.join(data_output, 'ratio')
                        os.makedirs(path_ratio, exist_ok=True)
                        print(f"{path_ratio.replace(path_output, '')}")
                        destination = f"{os.path.join(path_ratio, title)}.tiff"
                        filenames.append(destination)
                        gdal.Warp(destination, memoset, **options_warp,
                                  outputType=gdal.GDT_Byte, **options_cutline)
                        # Create negative band (HH, HV, 1 - HH/HV)
                        band_ex.WriteArray(image_negative)
                        band_ex.SetMetadata({'POLARISATION': '1 - HH/HV',
                                             'SWATH': 'EW'})
                        path_negative = os.path.join(data_output, 'negative')
                        os.makedirs(path_negative, exist_ok=True)
                        print(f"{path_negative.replace(path_output, '')}")
                        destination = f"{os.path.join(path_negative, title)}.tiff"
                        filenames.append(destination)
                        gdal.Warp(destination, memoset, **options_warp,
                                  outputType=gdal.GDT_Byte, **options_cutline)
    print(f"Done!")
    return filenames


def process_sentinel2(filename, path_output, area, shapes):
    title = os.path.splitext(os.path.basename(filename))[0]
    dataset = gdal.Open(filename, gdal.GA_ReadOnly)
    subsets = dataset.GetSubDatasets()
    assert len(subsets) > 0, f"no sub datasets found!"
    dataset = gdal.Open(subsets[0][0], gdal.GA_ReadOnly)
    #print(f"{snapshot.title} -->")
    print(f"Reading {subsets[0][1][:1].lower()}",
          f"{subsets[0][1][1:]}", sep='')
    image = dataset.ReadAsArray()
    if image.ndim < 3:
        image = image[None, ...]
    image = np.moveaxis(image[:3, ...], 0, -1) # CHW -> HWC
    image = image.astype(np.float32)
    print(f"Calculating optimal histogram...")
    clip = image.mean().astype(np.float32) * np.float32(2)
    image = image / clip
    image = np.tanh(image)
    # Apply gamma correction here (TODO)
    image = (image * 254 + 1).round().astype(np.uint8)
    # Apply nodata mask here (TODO)
    image = np.moveaxis(image, -1, 0) # HWC -> CHW
    print(f"Applying histogram...")
    tempset = gdal.GetDriverByName('MEM')\
              .CreateCopy('', dataset, 0)
    for i in range(image.shape[0]):
        band = tempset.GetRasterBand(i + 1)
        band.WriteArray(image[i].astype(np.uint16))
        del band
    print(f"Writing to temporary file...")
    with tempfile.TemporaryDirectory() as path_temp:
        temp = os.path.join(path_temp, 'temp.tiff')
        gdal.Translate(temp, tempset,
                       creationOptions=['COMPRESS=DEFLATE'],
                       format='GTiff', bandList=[1, 2, 3],
                       outputType=gdal.GDT_Byte)
        del tempset
        #
        # Prepare filenames and paths
        #
        filenames = []
        name_area = os.path.splitext(os.path.basename(area))[0]
        for shape in shapes:
            if shape:
                name_shape = os.path.basename(shape)
                name_shape = os.path.splitext(name_shape)[0]
                data_prefix = f"{name_area}_{name_shape}"
                options = {'cutlineDSName': shape,
                           'cropToCutline': True}
            else:
                data_prefix = f"{name_area}"
                options = {}
            data_output = os.path.join(path_output,
                                       #data_name,
                                       data_prefix)
            os.makedirs(data_output, exist_ok=True)
            destination = f"{os.path.join(data_output, title)}.tiff"
            filenames.append(destination)
            gdal.Warp(destination, temp, **options)
    print(f"Done!")
    return filenames


def main(periodic: sched.scheduler) -> None:
    # Set working variables
    s3_id, s3_key, s3_bucket, s3_input, s3_output, s3_sync = get_environment()
    path_input, path_output = ('/dev/shm/gps/input', '/dev/shm/gps/output')
    path_data = '/dev/shm/gps/data'

    #print(f"\n=== Started input processing cycle ===\n")
    s3 = B3W(s3_bucket, s3_id, s3_key)

    # Get input files from S3
    files_input = get_from_aws(s3, s3_input, path_input)
    #print("DEBUG: input files -->")
    #print("\n".join([f"DEBUG: {filename}" for filename in files_input]))
    objects_output = check_in_aws(s3, s3_output, depth=1)
    #print("DEBUG: output sets -->")
    #print("\n".join([f"DEBUG: {name}" for name in objects_output]))
    # DEBUG: list sync objects in S3, remove output test set
    #objects_sync = check_in_aws(s3, s3_sync) # don't uncomment - dangerous!
    #print("DEBUG: sync objects -->")
    #print("\n".join([f"DEBUG: {name}" for name in objects_sync]))

    # Initialize Copernicus Open Data Access Hub search object
    config = Config.load('config.yaml')
    data_hub = DataHub(config, limit=1000)

    # Cycle through all the data input sets: a set may contain multiple
    # input areas and shapes to process. Result will be a snapshot that is
    # cut with each shape (if any)
    for data_input in glob(os.path.join(path_input, '*')):
        if not os.path.isdir(data_input):
            #print(f"DEBUG: '{data_input}' is not a valid data input!")
            #print("TODO: unzip archived input sets...")
            continue
        data_name = os.path.basename(data_input)
        #print(f"DEBUG: 'data_input' basename = {data_name}")
        if data_name in objects_output:
            #print(f"Output set for '{data_input}' already exists. Skipping...")
            continue
        #print(f"DEBUG: input directory --->\n{os.listdir(data_input)}\n")
        areas = glob(os.path.join(data_input, '*.geojson'))
        shapes = glob(os.path.join(data_input, '*.shp'))
        #print(f"DEBUG: shapes = {shapes}")
        if not shapes:
            shapes.append(None)
        for area in areas:
            try:
                print(f"\n=== Processing '{area}' ===\n")
                polygon, properties = Polygons.read_geojson(area)
            except Exception as e:
                print(f"Failed to read '{area}'!\n{str(e)}")
                continue
            #print(f"DEBUG:\n{polygon}")

            # Set config key (search area)
            #print(f"DEBUG: config.search -->\n{config.search}")
            search = config.search.copy()
            search.update(properties)
            #config.search["footprint"] = f"\"Intersects({polygon})\""
            #print(f"DEBUG: config.search -->\n{config.search}")
            #print(f"Config 'search' section:\n{config.search}")

            snapshots = data_hub.search(search, area=polygon)
            snapshots = sorted(snapshots,
                               key=lambda item: item.begin_position)

            print(f"\n=== {len(snapshots)} snapshots found ===\n")
            # print_snapshots(snapshots) # DEBUG
            # break # DEBUG

            print(f"\n=== Processing snapshots and shapes ===\n")
            for index, snapshot in enumerate(snapshots):
                filename = sync_with_aws(s3, s3_sync, data_hub, snapshot,
                                         path_data)
                if not filename:
                    print(f"'\n{snapshot.uuid}' not synced. Skipping...")
                    continue
                else:
                    print(f"\n{index:8d}: {snapshot.title}")
                try:
                    # Process each superposition of an area and a shape
                    #
                    # Process a snapshot
                    #
                    #print(f"DEBUG: search keys = {search.keys()}")
                    path_target = os.path.join(path_output, data_name)
                    #print(f"DEBUG: path_data = '{path_data}'")
                    if search['platformName'] == 'Sentinel-2':
                        filenames = process_sentinel2(filename, path_target,
                                                      area, shapes)
                    elif search['platformName'] == 'Sentinel-1':
                        filenames = process_sentinel1(filename, path_target,
                                                      area, shapes)
                    else:
                        filenames = []
                        print(f"NOT IMPLEMENTED: {snapshot.title}",
                              f"{config.search['platformName']}")
                    #print(f"DEBUG: exporting '{data_prefix}' to S3 -->")
                    # Put processing result (for each output set) to S3
                    result = put_to_aws(s3, s3_output, path_output) # result...
                    for outfile in filenames:
                        remove(outfile) # all files (TODO: file or directory)
                except Exception as e:
                    print(f"FAILED: {e}")
                    raise e
                remove(filename) # remove snapshot
                #break # DEBUG: the first snapshot only
            print(f"\n=== Done snapshots for '{area}' ===\n")
        # Clean up output set (there should remain only logs)
        try:
            rmtree(os.path.join(path_output, data_name)) # data output - prefix
        except FileNotFoundError as e:
            pass
    # Clean up
    for path in (path_data, path_input, path_output):
        try:
            #print(f"DEBUG: removing {path}")
            rmtree(path)
        except FileNotFoundError as e:
            pass

    #print(f"\n=== Completed input processing cycle ===\n")
    periodic.enter(INTERVAL, 1, main, (periodic,))

    return None


if __name__ == '__main__':
    if os.getenv('GPS_DEBUG', '').lower() in ['1', 'y', 'on', 'yes', 'true']:
        set_debug_aws()
    periodic = sched.scheduler(time.time, time.sleep)
    periodic.enter(INTERVAL, 1, main, (periodic,))
    periodic.run()
