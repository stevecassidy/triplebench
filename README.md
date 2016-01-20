# triplebench

This code is intended to benchmark the upload performance of RDF triple stores. In the first
instance to evaluate a Sesame triplestore.  

Copy config.ini.dist to config.ini and change any required settings.  

Run an upload test:

python upload_graphs.py testdata

output is written to benchmark.csv
