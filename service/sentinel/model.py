import os
import json
import yaml
import marshmallow as mm

from datetime import datetime
from dataclasses import dataclass
from typing import Tuple

from shapely import wkt
from shapely.geometry import GeometryCollection, Polygon, shape


@dataclass
class Filters:
    radar = {
            'platformname': 'Sentinel-1',
            'producttype': 'SLC'
        }

    rgb = {
            'platformname': 'Sentinel-2',
#            'platformname': 'Sentinel-3',
#            'instrument': 'OLCI'
            'producttype': 'S2MSI2A'
        }

    sentinel3 = {
            'platformname': 'Sentinel-3',
        }


@dataclass
class Polygons:
    nevelsky: str = ("POLYGON((141.67555267676036 52.15998703210121,"
                              "141.6694176527095 52.13979595813396,"
                              "141.62926113164943 52.10623800358442,"
                              "141.61866427192524 52.07162631995021,"
                              "141.63985799137362 52.050366243640866,"
                              "141.6437620975878 52.017084208283705,"
                              "141.664398087577 51.9830903950878,"
                              "141.65658987514863 51.939788199965136,"
                              "141.64543528596525 51.90676797069267,"
                              "141.61197151841517 51.891625580419,"
                              "141.62535702543522 51.868213665039946,"
                              "141.6967463962087 51.84892410896782,"
                              "141.73467199943215 51.84272213812437,"
                              "141.7737130615739 51.812389089816804,"
                              "141.82056233614398 51.815837055901056,"
                              "141.69451547837204 51.89713249466507,"
                              "141.7023236908004 51.97690692810261,"
                              "141.6632826286586 52.08053882442343,"
                              "141.72240195133043 52.15861843506971,"
                              "141.67555267676036 52.15998703210121,"
                              "141.67555267676036 52.15998703210121))")

    test_square: str = ("POLYGON((-0.9679549811646666 0.6491622938252988,"
                                 "-0.7939433899042641 0.6491622938252988,"
                                 "-0.7939433899042641 0.6654287044202363,"
                                 "-0.9679549811646666 0.6654287044202363,"
                                 "-0.9679549811646666 0.6491622938252988))")

    greenland: str = ("POLYGON((-43.9223103683942 82.76033684330872,"
                               "-37.33664091453907 82.76033684330872,"
                               "-37.33664091453907 83.47811422282976,"
                               "-43.9223103683942 83.47811422282976,"
                               "-43.9223103683942 82.76033684330872))")

    greenland_west: str = ("POLYGON((-19.391137836351195 79.0731524320617,"
                                    "-19.23051175211083 79.0731524320617,"
                                    "-19.23051175211083 79.10187111848902,"
                                    "-19.391137836351195 79.10187111848902,"
                                    "-19.391137836351195 79.0731524320617))")

    @classmethod
    def read_geojson(self, filename: str) -> Tuple[str, dict]:
        try:
            with open(filename) as geojson:
                features = json.load(geojson)['features']

            geometry = GeometryCollection([
                shape(feature['geometry']).buffer(0)
                for feature in features
            ])
            properties = features[0]['properties']

            return str(geometry[0]), properties
        except IndexError:
            raise ValueError(f"Cannot find polygon in {file_path}")

        return None


# Serialization support
class PolygonField(mm.fields.Field):
    def _serialize(self, value: Polygon, *args, **kwargs) -> str:
        if value is None:
            return None

        return str(value)

    def _deserialize(self, value: str, *args, **kwargs) -> Polygon:
        if not isinstance(value, (str, bytes)):
            raise self.make_error("invalid")

        return wkt.loads(value)


@dataclass
class Snapshot:
    uuid: str
    link: str
    icon: str
    size: str
    title: str
    polygon: Polygon
    begin_position: datetime
    end_position: datetime
    ingestion_date: datetime
    cloud_coverage: float
    instrument: str

    class Schema(mm.Schema):
        uuid = mm.fields.Str()
        link = mm.fields.Str()
        icon = mm.fields.Str()
        size = mm.fields.Str()
        title = mm.fields.Str()
        polygon = PolygonField()
        begin_position = mm.fields.AwareDateTime()
        end_position = mm.fields.AwareDateTime()
        ingestion_date = mm.fields.AwareDateTime()
        cloud_coverage = mm.fields.Float(allow_none=True)
        instrument = mm.fields.Str()

        @mm.post_load
        def make_object(self, data, **kwargs):
            return Snapshot(**data)

    def __str__(self):
        return json.dumps(self.Schema().dump(self), indent=2)
