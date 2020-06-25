# desiperf
Tools for monitoring DESI Instrument Performance

## Directory structure for (most) modules in desihub

  * **bin/**: executable scripts; should be added to `$PATH`
  * **py/desiperf/**: for modules that one would import; `py/` should be added to `$PYTHONPATH`
    to enable python `import desiperf` to find the desiperf directory
  * **doc/**: documentation
  * **etc/**: for small config files or other things that don't fit elsewhere

## To run InstPerfApp on local machine (temporary)
  * **cd py/desiperf/**
  * **bokeh serve --show instperfapp**
  * output will be found at **http://localhost:5006/instperfapp**
