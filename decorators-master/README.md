# Venidera's Decorators #

![GitHub Release](https://img.shields.io/badge/release-v1.0.17-blue.svg)
![GitHub license](https://img.shields.io/badge/license-GPLv3-yellow.svg)

This repo stores the decorators used on Tornado's web server based apps. The main goal is to standardize code over tornado apps developed.

## Requirements

* python 3+ => the version used in the package development and also testing.

## Installation

### Using PIP

We present here an installation with a **virtualenv** (requires ssh keys configured in the Github user profile):

```
$ /usr/bin/python3.8 -m venv --prompt=" <decorators> " venv
$ source venv/bin/activate
( <Data Models> ) $ pip install --upgrade setuptools pip wheel
( <Data Models> ) $ python setup.py install
( <Data Models> ) $ pip list
vdecorators (1.0.17)
pip (9.0.1)
schematics (2.0.1)
setuptools (36.6.0)
wheel (0.30.0)
```

### For Development

In order to install the Data Models application, please type:

```
$ git clone git@github.com:venidera/decorators.git
```

## Decorators available

* `prepare_json`: this decorator check JSON data sent by POST and PUT, process it and create the input_data structure.

## Using

Example:

```

from vdecorators import prepare_json

class BaseHandler(RequestHandler):

    @prepare_json
    def prepare(self):
        pass

```

## Contributing

Please file a Github issue to [report a bug](https://github.com/venidera/decorators/issues?status=new&status=open).

## Maintainers

* **Marcos Leone Filho** from [Venidera Research and Development](http://portal.venidera.com).
* **Makoto Kadowaki** from [Venidera Research and Development](http://portal.venidera.com).
* **Jonatas Trabuco Belotti** from [Venidera Research and Development](http://portal.venidera.com).
* **Lucas Vinícius de Souza** from [Venidera Research and Development](http://portal.venidera.com).
* **João Borsoi** from [Venidera Research and Development](http://portal.venidera.com).

## License

This package is released and distributed under the license [GNU GPL Version 3, 29 June 2007](https://www.gnu.org/licenses/gpl-3.0.html).
