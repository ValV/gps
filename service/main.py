import sys

import os, errno
import sched, time

from b3w import B3W
from glob import glob
from shutil import rmtree
from subprocess import Popen, PIPE, STDOUT
from typing import Any, List, Tuple, Set

from sentinel import Config
from sentinel import DataHub
from sentinel import Polygons


# Main loop period (seconds)
INTERVAL: int = 100


def get_environment() -> Tuple[str]:
    # Gather AWS parameters from environment variables
    try:
        s3_id = os.environ['S3_ID']
        s3_key = os.environ['S3_KEY']
        s3_bucket = os.environ['S3_BUCKET']
        s3_input = os.environ['S3_INPUT']
        s3_output = os.environ['S3_OUTPUT']
        s3_sync = os.environ['S3_SYNC']
    except KeyError as e:
        error_message = ("'S3_ID', 'S3_KEY', 'S3_BUCKET', 'S3_INPUT', "
                         "'S3_OUTPUT' and 'S3_SYNC' environment variables "
                         "must be set (see README)!")
        raise AssertionError(error_message)

    return s3_id, s3_key, s3_bucket, s3_input, s3_output, s3_sync


def remove(filename: str) -> None:
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise e
    finally:
        #print(f"DEBUG: removed '{filename}'")
        pass

    return None


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
        for s3o in s3.ls(prefix):
            print(f"DEBUG: get_from_aws s3o = {s3o}")
            if prefix:
                filename = s3o.replace(prefix.strip('/'), '').strip('/')
            else:
                filename = s3o
            if not filename.endswith(('.geojson', '.xml')):
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
        #print(f"DEBUG: S3 objects = {objects}")
        if len(objects) > 0:
            s3o = objects[0].replace(prefix, '').lstrip('/')
            filename = os.path.join(path, s3o)
            #print(f"DEBUG: syncing '{s3o}' -> '{filename}'")
            s3.get(objects[0], filename)
        else:
            data_hub.download(snapshot)
            #print(f"DEBUG: data_hub.config.output = {data_hub.config.output}")
            filename = glob(os.path.join(data_hub.config.output, '*'))
            #print(f"DEBUG: filename = {filename}")
            if len(filename) < 1:
                raise FileNotFoundError(f"failed to download {snapshot.uuid}!")
            else:
                filename = filename[0]
            s3o = filename.replace(path, '')
            s3o = '/'.join([prefix, s3o.lstrip(os.path.sep)])
            #print(f"DEBUG: syncing '{filename}' -> '{s3o}'")
            s3.put(filename, s3o)
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


def main(periodic: sched.scheduler) -> None:
    # Set working variables
    s3_id, s3_key, s3_bucket, s3_input, s3_output, s3_sync = get_environment()
    path_input, path_output = ('/dev/shm/gps/input', '/dev/shm/gps/output')
    path_data = '/dev/shm/gps/data'

    print(f"\n=== Started input processing cycle ===\n")
    s3 = B3W(s3_bucket, s3_id, s3_key)

    # Get input files from S3
    files_input = get_from_aws(s3, s3_input, path_input)
    print("DEBUG: input files -->")
    print("\n".join([f"DEBUG: {filename}" for filename in files_input]))
    objects_output = check_in_aws(s3, s3_output, depth=1)
    print("DEBUG: output sets -->")
    print("\n".join([f"DEBUG: {name}" for name in objects_output]))
    # DEBUG: list sync objects in S3, remove output test set
    #objects_sync = check_in_aws(s3, s3_sync) # don't uncomment - dangerous!
    #print("DEBUG: sync objects -->")
    #print("\n".join([f"DEBUG: {name}" for name in objects_sync]))

    # Initialize Copernicus Open Data Access Hub search object
    config = Config.load('config.yaml')
    data_hub = DataHub(config, limit=1000000)

    # Cycle through all the data input sets: a set may contain multiple
    # input areas and graphs to process. Result will be a superposition
    # of an area and a graph
    for data_input in glob(os.path.join(path_input, '*')):
        if not os.path.isdir(data_input):
            #print(f"DEBUG: '{data_input}' is not a valid data input!")
            print("TODO: unzip archived input sets...")
            continue
        data_name = os.path.basename(data_input)
        #print(f"DEBUG: 'data_input' basename = {data_name}")
        if data_name in objects_output:
            print(f"Output set for '{data_input}' already exists. Skipping...")
            continue
        areas = glob(os.path.join(data_input, '*.geojson'))
        graphs = glob(os.path.join(data_input, '*.xml'))
        for area in areas:
            try:
                polygon, properties = Polygons.read_geojson(area)
            except Exception as e:
                print(f"Failed to read '{area}'!\n{str(e)}")
                continue
            #print(f"DEBUG:\n{polygon}")

            # Set config key (search area)
            #print(f"DEBUG: config.search -->\n{config.search}")
            config.search.update(properties)
            config.search["footprint"] = f"\"Intersects({polygon})\""
            #print(f"DEBUG: config.search -->\n{config.search}")
            #print(f"Config 'search' section:\n{config.search}")

            snapshots = data_hub.search(config.search)
            snapshots = sorted(snapshots,
                               key=lambda item: item.begin_position)

            print(f"\n=== {len(snapshots)} snapshots found ===\n")
            #print('\n'.join([f"{i:2d}\t{snapshot.begin_position}"
            #                 f"\t{snapshot.link}"
            #                 f"\n\t{snapshot.uuid}"
            #                 f"\n\t{snapshot.title}"
            #      for i, snapshot in enumerate(snapshots)
            #]))

            print(f"\n=== Processing snapshots with graphs ===\n")
            #print(f"Destination: {config.output or 'disabled'}.")
            #if config.output:
            #    for i, snapshot in enumerate(snapshots):
            #        download(snapshot.download_link, config, index=(i + 1))
            for index, snapshot in enumerate(snapshots):
                filename = sync_with_aws(s3, s3_sync, data_hub, snapshot,
                                         path_data)
                if not filename:
                    print(f"'{snapshot.uuid}' not synced. Skipping...")
                    continue
                for graph in graphs:
                    # Process each superposition of an area and a graph
                    name_graph = os.path.splitext(os.path.basename(graph))[0]
                    name_area = os.path.splitext(os.path.basename(area))[0]
                    data_prefix = f"{name_area}_{name_graph}"
                    data_output = os.path.join(path_output, data_name,
                                               data_prefix)
                    os.makedirs(data_output, exist_ok=True)
                    #print(f"DEBUG: path_data = '{path_data}'")
                    #print(f"DEBUG: data_output = '{data_output}'")
                    filelog = os.path.join(data_output, data_prefix + '.log')
                    #remove(filelog)
                    #print(f"DEBUG: processing '{filename}'...")
                    fileout = os.path.join(data_output, snapshot.title)
                    command = ["gpt", f"{graph}", "-e", f"-Pinput={filename}",
                               f"-Poutput={fileout}"]
                    args = {'stdout': PIPE, 'stderr': STDOUT, 'bufsize': 1}
                    #print(f"DEBUG: command = {command}\n\targs = {args}")
                    with Popen(command, **args) as process, \
                         open(filelog, 'ab') as logfile:
                        cmdline = f"\n{index:5d}: {' '.join(command)}\n\n"
                        print(cmdline, end='')
                        logfile.write(bytes(cmdline, 'UTF-8'))
                        for line in process.stdout:
                            sys.stdout.buffer.write(line)
                            logfile.write(line)
                    # Put processing result (for each output set) to S3
                    #print(f"DEBUG: exporting '{data_prefix}' to S3 -->")
                    result = put_to_aws(s3, s3_output, path_output)
                    for outfile in glob(f"{fileout}*"):
                        remove(outfile)
                remove(filename) # remove snapshot
                #break # DEBUG: the first snapshot only
            print(f"\n=== Done snapshots for '{area}' ===\n")
        # Clean up output set (there should remain only logs)
        try:
            rmtree(os.path.join(path_output, data_name))
        except FileNotFoundError as e:
            pass
    # Clean up
    for path in (path_data, path_input, path_output):
        try:
            #print(f"DEBUG: removing {path}")
            rmtree(path)
        except FileNotFoundError as e:
            pass

    print(f"\n=== Completed input processing cycle ===\n")
    periodic.enter(INTERVAL, 1, main, (periodic,))

    return None


if __name__ == '__main__':
    if os.getenv('GPS_DEBUG', '').lower() in ['1', 'y', 'on', 'yes', 'true']:
        set_debug_aws()
    periodic = sched.scheduler(time.time, time.sleep)
    periodic.enter(INTERVAL, 1, main, (periodic,))
    periodic.run()
