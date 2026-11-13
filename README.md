# German Car Dealership Dataset

A sample dataset of 500 real-world car dealership locations across all 16 German federal states, with smaller subsets of 250, 100, 50 and 10 locations for quick tests.

## Files

| Locations | CSV | Excel | Federal states |
| --: | --- | --- | --: |
| 500 | [`car_dealerships_germany_500.csv`](data/car_dealerships_germany_500.csv) | [`car_dealerships_germany_500.xlsx`](data/car_dealerships_germany_500.xlsx) | 16 |
| 250 | [`car_dealerships_germany_250.csv`](data/car_dealerships_germany_250.csv) | [`car_dealerships_germany_250.xlsx`](data/car_dealerships_germany_250.xlsx) | 16 |
| 100 | [`car_dealerships_germany_100.csv`](data/car_dealerships_germany_100.csv) | [`car_dealerships_germany_100.xlsx`](data/car_dealerships_germany_100.xlsx) | 16 |
| 50 | [`car_dealerships_germany_50.csv`](data/car_dealerships_germany_50.csv) | [`car_dealerships_germany_50.xlsx`](data/car_dealerships_germany_50.xlsx) | 16 |
| 10 | [`car_dealerships_germany_10.csv`](data/car_dealerships_germany_10.csv) | [`car_dealerships_germany_10.xlsx`](data/car_dealerships_germany_10.xlsx) | 8 |

- CSV: UTF-8 with BOM, every field quoted.
- Excel: formatted workbook with a filterable table, source notes and a federal-state summary.

The CSV and Excel file of one size contain the same records. Fields include dealership name, address, website where available, brands, coordinates, OpenStreetMap object identifiers, a row-level source URL, and the retrieval date.

## Subsets

The smaller files are drawn from the 500-record file by [`scripts/make_subsets.py`](scripts/make_subsets.py) (Python 3, standard library only):

- **Proportional per federal state.** Each state's quota follows its share of the 500 records (largest remainder method); from 50 records up every state has at least one record. The 10-record set covers the eight largest states.
- **Deterministic.** Within a state, records are ranked by the SHA-256 hash of their OSM object (`node/<id>`), so the selection is reproducible and independent of row order.
- **Nested.** 10 ⊂ 50 ⊂ 100 ⊂ 250 ⊂ 500: a result for a small set is part of every larger one.
- **Same IDs.** Rows keep the `ID` of the 500-record file, so every subset can be joined back to it.

| Federal state | 500 | 250 | 100 | 50 | 10 |
| --- | --: | --: | --: | --: | --: |
| Nordrhein-Westfalen | 95 | 48 | 19 | 9 | 2 |
| Bayern | 78 | 39 | 16 | 8 | 2 |
| Baden-Württemberg | 65 | 33 | 13 | 6 | 1 |
| Niedersachsen | 48 | 24 | 10 | 5 | 1 |
| Hessen | 37 | 19 | 7 | 4 | 1 |
| Rheinland-Pfalz | 26 | 13 | 5 | 3 | 1 |
| Sachsen | 24 | 12 | 5 | 2 | 1 |
| Berlin | 20 | 10 | 4 | 2 | 1 |
| Schleswig-Holstein | 18 | 9 | 4 | 2 | 0 |
| Brandenburg | 18 | 9 | 4 | 2 | 0 |
| Sachsen-Anhalt | 16 | 8 | 3 | 2 | 0 |
| Thüringen | 15 | 7 | 3 | 1 | 0 |
| Hamburg | 14 | 7 | 3 | 1 | 0 |
| Mecklenburg-Vorpommern | 12 | 6 | 2 | 1 | 0 |
| Saarland | 7 | 3 | 1 | 1 | 0 |
| Bremen | 7 | 3 | 1 | 1 | 0 |

Regenerate or verify the subsets:

```bash
python3 scripts/make_subsets.py          # rewrite data/*_{250,100,50,10}.*
python3 scripts/make_subsets.py --check  # exit code 1 if a file differs
```

## Use as test data

The files import directly into [Dealership Risk Mapping](https://github.com/JanisKre/DealerShipRiskMappingApp): name, street, house number, postal code, city, coordinates and website are recognised automatically. They contain no portfolio terms (insured value, business type, limit, deductible); those fields stay empty, while vehicle counts, on-site exposure and the hail EAL are computed as usual. Start with the 10-record file for a quick run.

## Data source and attribution

Contains information from [OpenStreetMap](https://www.openstreetmap.org/copyright), made available under the [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/).

Data © OpenStreetMap contributors.

Every record includes a direct OpenStreetMap object URL for traceability. Federal-state assignment used boundary geometry from [isellsoap/deutschlandGeoJSON](https://github.com/isellsoap/deutschlandGeoJSON), which is published under the Unlicense; that geometry is not redistributed here.

## Quality notice

- Retrieved on 2026-07-23.
- Records are public OpenStreetMap points of interest tagged `shop=car`.
- Business existence and profile details were not individually verified against dealership websites or commercial registers.
- Available attributes may be incomplete or outdated.
- This dataset is intended for examples, analysis, testing, and prototyping—not as an authoritative business registry.

The federal-state values retain their official German names.

## License

The database files, including the subsets, are distributed under ODbL 1.0. Attribution and share-alike obligations apply to public reuse and derivative databases. See [LICENSE](LICENSE) for the applicable notice and links to the full legal terms.
