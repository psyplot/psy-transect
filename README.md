<!--
SPDX-FileCopyrightText: 2021-2024 Helmholtz-Zentrum hereon GmbH

SPDX-License-Identifier: CC-BY-4.0
-->

# psy-transect

[![CI](https://codebase.helmholtz.cloud/psyplot/psy-transect/badges/main/pipeline.svg)](https://codebase.helmholtz.cloud/psyplot/psy-transect/-/pipelines?page=1&scope=all&ref=main)
[![Code coverage](https://codebase.helmholtz.cloud/psyplot/psy-transect/badges/main/coverage.svg)](https://codebase.helmholtz.cloud/psyplot/psy-transect/-/graphs/main/charts)
[![Latest Release](https://codebase.helmholtz.cloud/psyplot/psy-transect/-/badges/release.svg)](https://codebase.helmholtz.cloud/psyplot/psy-transect)
<!-- TODO: uncomment the following line when the package is published at https://pypi.org -->
<!-- [![PyPI version](https://img.shields.io/pypi/v/psy-transect.svg)](https://pypi.python.org/pypi/psy-transect/) -->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
<!-- TODO: uncomment the following line when the package is registered at https://api.reuse.software -->
<!-- [![REUSE status](https://api.reuse.software/badge/codebase.helmholtz.cloud/psyplot/psy-transect)](https://api.reuse.software/info/codebase.helmholtz.cloud/psyplot/psy-transect) -->


Psyplot plugin for visualizing data along a transect for exploratory data analysis

## Installation

Install this package in a dedicated python environment via

```bash
python -m venv venv
source venv/bin/activate
pip install psy-transect
```

To use this in a development setup, clone the [source code][source code] from
gitlab, start the development server and make your changes::

```bash
git clone https://codebase.helmholtz.cloud/psyplot/psy-transect
cd psy-transect
python -m venv venv
source venv/bin/activate
make dev-install
```

More detailed installation and usage instructions may be found in the [docs][docs].


[source code]: https://codebase.helmholtz.cloud/psyplot/psy-transect
[docs]: https://psyplot.github.io/psy-transect/installation.html

## Technical note

This package has been generated from the template
https://codebase.helmholtz.cloud/psyplot/psyplot-plugin-template.git.

See the template repository for instructions on how to update the skeleton for
this package.


## License information

Copyright © 2021-2024 Helmholtz-Zentrum hereon GmbH


Code files in this repository are licensed under the
LGPL-3.0-only, if not stated otherwise
in the file.

Documentation files in this repository are licensed under CC-BY-4.0, if not stated otherwise in the file.

Supplementary and configuration files in this repository are licensed
under CC0-1.0, if not stated otherwise
in the file.

Please check the header of the individual files for more detailed
information.



### License management

License management is handled with [``reuse``](https://reuse.readthedocs.io/).
If you have any questions on this, please have a look into the
[contributing guide][contributing] or contact the maintainers of
`psy-transect`.

[contributing]: https://psyplot.github.io/psy-transect/contributing.html
