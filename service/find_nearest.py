import json
import datetime
from itertools import product

from sentinel import Config
from sentinel import DataHub
from sentinel import Filters
from sentinel import Polygons


def find_nearest() -> None:
    config = Config.load('config.yaml')
    data_hub = DataHub(config, limit=1000)

    params = config.search
    params['footprint'] = f"\"Intersects({Polygons.greenland_west})\""
    params['cloudCoverPercentage'] = "[0 TO 50]"
    params.update(Filters.rgb)
    snapshots_rgb = data_hub.search(params)
    if not snapshots_rgb:
        print("No RGB data found!")
        return None

    params = config.search
    params['footprint'] = f"\"Intersects({polygons.greenland_west})\""
    params.update(Filters.radar)
    snapshots_radar = data_hub.search(params)
    if not snapshots_radar:
        print("No radar data found!")
        return None

    nearest = min(
        product(snapshots_rgb, snapshots_radar),
        key=lambda t: abs(t[0].begin_position - t[1].begin_position)
    )

    print("\n=== Min time difference ===")
    print(abs(nearest[0].begin_position - nearest[1].begin_position))
    print(f"\n{nearest[0]}\n{nearest[1]}")

    return None

if __name__ == '__main__':
    find_nearest()
