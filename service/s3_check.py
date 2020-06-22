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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GPS S3 config set removal')
    parser.add_argument('name', nargs='+',
                        help='GPS set name to remove')
    parser.add_argument('-i', '--input', action='store_true',
                        help='delete only input config set (without -a)')
    parser.add_argument('-a', '--all', action='store_true',
                        help='delete input and output sets (overrides -i)')
    parser.add_argument('-d', '--depth', default=1, type=int,
                        help='delete input and output sets (overrides -i)')

    args = parser.parse_args()

    s3_id, s3_key, s3_bucket, s3_input, s3_output, s3_sync = get_environment()
    s3 = B3W(s3_bucket, s3_id, s3_key)

    # raise Exception(f"Argparse: name = {args.name}, input = {args.input}, all = {args.all}, depth = {args.depth}, s3_bucket = {s3_bucket}, s3_input = {s3_input}, s3_output = {s3_output}")
    if args.input or args.all:
        print(f"Checking input: {args.name}...")
        for name in args.name:
            for s3o in check_in_aws(s3, s3_input + f"/{name}", depth=args.depth):
                print(s3o)
    if not args.input or args.all:
        print(f"Checking output: {args.name}...")
        for name in args.name:
            for s3o in check_in_aws(s3, s3_output + f"/{name}", depth=args.depth):
                print(s3o)
