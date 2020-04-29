# Snapshot tool for Copernicus hub

Provides a quick API to search and download snapshots that overlap the provided geographical region within the smallest time difference.

## Details

Project structure is shown below:

```
.
├── Dockerfile
├── README.md
├── docker-compose.yaml
├── requirements.txt
└── service
    ├── config.yaml
    ├── find_nearest.py
    ├── main.py
    ├── opensearch.api
    ├── sample.geojson
    └── sentinel
        ├── __init__.py
        ├── config.py
        ├── model.py
        └── search.py
```

## Configuration

By now all the configuration is done via `config.yaml` file. Example configuration:

```yaml
credentials:
    username: ololo
    password: ololo!11
accounts:
    - ololo: ololo!11
search:
    start: 0
    platrormName: Sentinel-1
    productType: GRD
    polarisationMode: HV+HH
    sensorOperationalMode: EW
    beginPosition: "[2019-11-15T00:00:00.000Z TO 2019-11-30T23:59:59.999Z]"
download:
    enable: true
    path: snapshots
verbose: true
```

> Geographical regions are configured via separate file - `sample.geojson`, see [Regions section](#regions).

Config file has 3 main sections:

* `credentials` - where `username` and `password` must be real credentials at Copernicus hub;
* `search` - search parameters for Copernicus [OpenSearch API](https://scihub.copernicus.eu/userguide/OpenSearchAPI);
* `download` - snapshot downloading options, where `path` is the target output directory (local, may not exist).

> For more details on search parameters refer to [Search section](#search).

Auxiliary parameters:

* `accounts` - a list of additional accounts (TODO);
* `verbose` - control verbosity (may be useful if the tool is not run interactively).

### Search

Supported Copernicus Open Access Hub search parameters:

* platformName;
* beginPosition;
* endPosition;
* ingestionDate;
* collection;
* filename;
* footprint;
* orbitNumber;
* lastOrbitNumber;
* relativeOrbitNumber;
* lastRelativeOrbitNumber;
* orbitDirection;
* polarisationMode;
* productType;
* sensorOperationalMode;
* swathIdentifier;
* cloudCoverPercentage;
* timeliness.

> TODO: details (file `opensearch.api`).

### Regions

Geograpical regions (areas) that overlap snapshots are provided via `sample.geojson`. Minimal example:

```
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -21.181640624999996,
              75.6504309974655
            ],
            [
              38.408203125,
              75.6504309974655
            ],
            [
              38.408203125,
              82.20230156949353
            ],
            [
              -21.181640624999996,
              82.20230156949353
            ],
            [
              -21.181640624999996,
              75.6504309974655
            ]
          ]
        ]
      }
    }
  ]
}
```

> TODO: add polygons to config file as well.

## Dependencies

Several additional libraries are being used by this tool:

* `dataclasses` - support for data calsses for the application's model;
* `marshmallow` - data serialization;
* `pyyaml` - reading YAML configuration (human-readable superset of JSON);
* `requests` - deals with HTTP-requests (every lazy ass must use it instead of urllib);
* `shapely[vectorized]` - support for geographical regions.

All the dependencies may be installed either via system tools (such as _Debian APT_ or _Pacman_), or via _Python Package Index_. Not all the dependencies can be installed via system tools, but all of them may be installed via _PyPI_:

```shell
pip3 install -r requirements.txt
```

> On some distributions `pip3` is just a `pip`.

# Exmaple

After the correct date and region are provided to the tool, one can start searching/downloading by invoking from command from tool's root directory:

```shell
python3 main.py
```

> On some distributions `python3` is just a `python`.

## Sample output:

Standard output for the command above:

```
Starting a new search...
0: 36 records out of 36 fetched
No more results...

=== 36 snapshots found ===
2019-11-15 03:32:29.029000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('54c2d4d2-840f-4884-9cbb-42e8c0cf3667')/$value
2019-11-15 03:33:29.032000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('dcd18013-82f5-4696-810c-6039b4cf412a')/$value
2019-11-16 02:35:50.603000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('f804c5c4-b09a-4c3c-a050-5b5e2ab22660')/$value
2019-11-16 03:23:25.040000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('0d2e73e7-6869-4491-b352-b133204e5101')/$value
2019-11-16 03:24:25.041000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('84981316-a678-4381-b457-31d6ffa9fdb5')/$value
2019-11-17 03:16:00.031000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('3d838de9-848e-44e4-947e-d56717534cde')/$value
2019-11-17 03:17:00.030000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('d09f8692-2f78-424c-afac-5f109b785de9')/$value
2019-11-18 03:57:09.448000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('fa635714-6f16-413b-b651-1f01bb6bbd99')/$value
2019-11-19 02:59:34.058000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('69ff1826-92b0-4b79-904a-750d0a71580c')/$value
2019-11-19 03:00:34.058000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('4cc83428-c3ae-427f-a5ed-ef7362d07c6c')/$value
2019-11-19 03:48:56.377000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('aa4ef49e-93dc-4177-ab1e-4b44f942af1f')/$value
2019-11-20 02:50:45.311000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('66d617f3-bebd-4ce3-b91c-399e103a2331')/$value
2019-11-20 02:51:45.311000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('2cdfac4f-c98b-4200-be3c-83c99ae930af')/$value
2019-11-20 03:40:40.411000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('03b894be-0ee4-4e11-ae00-60b98f2cff72')/$value
2019-11-20 03:41:40.410000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('7397953b-90cb-4102-aaae-a32cff07d7d8')/$value
2019-11-21 02:44:04.783000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('c8e73c5e-baf1-4a80-9b64-a422006fd5e6')/$value
2019-11-21 03:31:36.493000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('e53229a1-99fd-4782-90a8-7afdd3c99ac8')/$value
2019-11-21 03:32:36.489000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('c7e6dd6c-7a1b-47cc-9b6d-e45318370eb5')/$value
2019-11-22 02:34:25.403000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('4559ef56-5815-4518-89be-c8d92457566e')/$value
2019-11-22 02:35:25.403000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('e7299415-3e3f-4401-a4ab-fd7ee444f34d')/$value
2019-11-22 03:24:14.222000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('09850758-57d0-44f9-ae4a-28fabc4bf330')/$value
2019-11-22 03:25:14.221000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('82241702-e782-48dd-ab2f-43a2f391e7c5')/$value
2019-11-23 03:15:16.588000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('f410b656-1cad-4cad-8778-fc8ff4e7ad32')/$value
2019-11-23 03:16:16.589000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('8b935b76-070f-48c6-b58e-36e75248015e')/$value
2019-11-25 03:48:54.652000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('263bc0e3-5a0f-4f48-b685-8f049ca33d82')/$value
2019-11-25 03:49:54.652000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('409a88a1-a0e9-4fd8-a847-76c51ac6334e')/$value
2019-11-26 02:52:19.265000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('a43e53fa-67ce-40c1-8aac-0f1a9bc370fa')/$value
2019-11-26 03:39:47.788000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('0775d1e6-6940-426f-a78a-1f42a25ef36b')/$value
2019-11-26 03:40:47.790000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('ec7a473f-2b20-4a51-afbb-58f43eff480b')/$value
2019-11-27 03:32:28.653000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('73c0ffc7-5bfd-4590-aba2-0327693c7571')/$value
2019-11-27 03:33:28.651000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('a6fc1785-8cd2-45e8-815d-f531e6cf8d16')/$value
2019-11-28 02:35:50.208000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('1b17014f-c489-473b-b138-a94a7abe22dd')/$value
2019-11-29 02:26:13.465000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('b4ad7be8-95a7-4ca2-bab9-686228cb5145')/$value
2019-11-29 02:27:13.465000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('8d1ca79a-d5e1-41e2-9e09-2caf0738e8fe')/$value
2019-11-29 03:15:59.614000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('77f21c29-2fd2-4e3c-9dc0-b6d98489cd11')/$value
2019-11-29 03:16:59.614000+00:00	https://scihub.copernicus.eu/dhus/odata/v1/Products('49686744-c972-4058-8ca1-6691e6576390')/$value

=== Downloading  snapshots ===
Destination: snapshots.

  1 S1A_EW_GRDM_1SDH_20191115T033229_20191115T033329_029916_0369D2_86AC.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

  2 S1A_EW_GRDM_1SDH_20191115T033329_20191115T033429_029916_0369D2_F7FE.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

  3 S1A_EW_GRDM_1SDH_20191116T023550_20191116T023649_029930_036A4F_79D5.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

  4 S1B_EW_GRDM_1SDH_20191116T032325_20191116T032425_018947_023BCE_4BC3.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

  5 S1B_EW_GRDM_1SDH_20191116T032425_20191116T032525_018947_023BCE_A132.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

  6 S1A_EW_GRDM_1SDH_20191117T031600_20191117T031700_029945_036ADD_E4C5.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

  7 S1A_EW_GRDM_1SDH_20191117T031700_20191117T031800_029945_036ADD_32F2.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

  8 S1A_EW_GRDM_1SDH_20191118T035709_20191118T035809_029960_036B5C_DEF6.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

  9 S1A_EW_GRDM_1SDH_20191119T025934_20191119T030034_029974_036BCB_E5D1.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 10 S1A_EW_GRDM_1SDH_20191119T030034_20191119T030132_029974_036BCB_DE0B.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 11 S1B_EW_GRDM_1SDH_20191119T034856_20191119T034959_018991_023D4D_298F.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 12 S1B_EW_GRDM_1SDH_20191120T025045_20191120T025145_019005_023DCE_3167.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 13 S1B_EW_GRDM_1SDH_20191120T025145_20191120T025227_019005_023DCE_4793.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 14 S1A_EW_GRDM_1SDH_20191120T034040_20191120T034140_029989_036C5A_4A23.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 15 S1A_EW_GRDM_1SDH_20191120T034140_20191120T034240_029989_036C5A_8C9A.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 16 S1A_EW_GRDM_1SDH_20191121T024404_20191121T024503_030003_036CC6_5EF5.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 17 S1B_EW_GRDM_1SDH_20191121T033136_20191121T033236_019020_023E43_1BFC.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 18 S1B_EW_GRDM_1SDH_20191121T033236_20191121T033336_019020_023E43_B9B0.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 19 S1B_EW_GRDM_1SDH_20191122T023425_20191122T023525_019034_023EBB_CB09.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 20 S1B_EW_GRDM_1SDH_20191122T023525_20191122T023601_019034_023EBB_3759.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 21 S1A_EW_GRDM_1SDH_20191122T032414_20191122T032514_030018_036D53_C668.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 22 S1A_EW_GRDM_1SDH_20191122T032514_20191122T032614_030018_036D53_3922.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 23 S1B_EW_GRDM_1SDH_20191123T031516_20191123T031616_019049_023F28_F343.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 24 S1B_EW_GRDM_1SDH_20191123T031616_20191123T031707_019049_023F28_E53F.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 25 S1A_EW_GRDM_1SDH_20191125T034854_20191125T034954_030062_036EE2_A7DA.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 26 S1A_EW_GRDM_1SDH_20191125T034954_20191125T035054_030062_036EE2_ED80.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 27 S1A_EW_GRDM_1SDH_20191126T025219_20191126T025317_030076_036F58_DC7F.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 28 S1B_EW_GRDM_1SDH_20191126T033947_20191126T034047_019093_024083_D94F.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 29 S1B_EW_GRDM_1SDH_20191126T034047_20191126T034147_019093_024083_5D71.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 30 S1A_EW_GRDM_1SDH_20191127T033228_20191127T033328_030091_036FE6_A27C.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 31 S1A_EW_GRDM_1SDH_20191127T033328_20191127T033428_030091_036FE6_8033.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 32 S1A_EW_GRDM_1SDH_20191128T023550_20191128T023648_030105_037063_3571.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 33 S1B_EW_GRDM_1SDH_20191129T022613_20191129T022713_019136_0241DF_CCC3.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 34 S1B_EW_GRDM_1SDH_20191129T022713_20191129T022746_019136_0241DF_13F6.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 35 S1A_EW_GRDM_1SDH_20191129T031559_20191129T031659_030120_0370EF_B1FB.zip
0....10....20....30....40....50....60....70....80....90....100 - done.

 36 S1A_EW_GRDM_1SDH_20191129T031659_20191129T031759_030120_0370EF_D07E.zip
0....10....20....30....40....50....60....70....80....90....100 - done.
```
