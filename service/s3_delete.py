import os
import argparse

from b3w import B3W
from typing import Any, List, Tuple, Set


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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GPS S3 config set removal')
    parser.add_argument('name', nargs='+',
                        help='GPS set name to remove')
    parser.add_argument('-i', '--input', action='store_true',
                        help='delete only input config set (without -a)')
    parser.add_argument('-a', '--all', action='store_true',
                        help='delete input and output sets (overrides -i)')

    args = parser.parse_args()

    s3_id, s3_key, s3_bucket, s3_input, s3_output, s3_sync = get_environment()
    s3 = B3W(s3_bucket, s3_id, s3_key)

    # raise Exception(f"Argparse: name = {args.name}, input = {args.input}, all = {args.all}")
    if args.input or args.all:
        print(f"Removing input: {args.name}...")
        for name in args.name:
            remove_from_aws(s3, s3_input + f"/{name}")
    if not args.input or args.all:
        print(f"Removing output: {args.name}...")
        for name in args.name:
            remove_from_aws(s3, s3_output + f"/{name}")
