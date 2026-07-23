# German Car Dealership Dataset

A sample dataset of 500 real-world car dealership locations across all 16 German federal states.

## Files

- `data/car_dealerships_germany_500.csv` — UTF-8 CSV with 500 records.
- `data/car_dealerships_germany_500.xlsx` — formatted Excel workbook with filters, frozen headers, source notes, and a federal-state summary.

Both files contain the same records. Fields include dealership name, address, website where available, brands, coordinates, OpenStreetMap object identifiers, a row-level source URL, and the retrieval date.

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

The database files are distributed under ODbL 1.0. Attribution and share-alike obligations apply to public reuse and derivative databases. See [LICENSE](LICENSE) for the applicable notice and links to the full legal terms.
