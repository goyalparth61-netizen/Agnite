# India populated-place dataset

Source: GeoNames India country export https://download.geonames.org/export/dump/IN.zip
Administrative names: https://download.geonames.org/export/dump/admin1CodesASCII.txt
Publisher: GeoNames https://www.geonames.org/
License: Creative Commons Attribution 4.0 https://creativecommons.org/licenses/by/4.0/

Downloaded 2026-09-13. Attribution applies to the geography dataset, independently of the app MIT license. GeoNames data is supplied without a guarantee of accuracy or completeness.

Changes: retained feature class P (populated places), excluding PPLH, PPLQ, PPLW and PPLCH; selected ID, ASCII name, mapped administrative region, latitude, longitude, source population, feature code and alternate names; sorted by source population, name and ID; encoded as compressed JSON tuples. Source coverage includes cities, towns and villages. Unmapped administrative names are labeled Unspecified region. No coordinates or population estimates were invented.

549,021 records. 36 named Indian states/UTs plus unspecified-region records. The source's geographic assignments are preserved. This is not an official census city list or boundary reference. Source population records are not current population estimates.

Thermal values, hotspot offsets, classifications, confidence, FRP and risk are generated separately by the app and are not provided or endorsed by GeoNames.

Reproduce: python scripts/import-india-places.py
