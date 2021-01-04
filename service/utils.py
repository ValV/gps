import os, errno

from typing import List, Tuple


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


def print_snapshots(snapshots: List):
    print('\n'.join([f"{i:2d}\t{snapshot.begin_position}"
                     f"\t{snapshot.link}"
                     f"\n\t{snapshot.uuid}"
                     f"\n\t{snapshot.title}"
          for i, snapshot in enumerate(snapshots)
    ]))
    return None
