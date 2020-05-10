# WarSampo Entity Linking

General entity linking processes used in the WarSampo data transformation pipeline.

Person record linkage used with death records and prisoner records found in *warsa_linkers/person_record_linkage.py*, employing [Dedupe](https://github.com/dedupeio/dedupe).

Places, people, and military units in WarSampo events and photographs are linked using https://github.com/SemanticComputing/python-arpa-linker .

## Tests 
`nosetests --with-doctest`
