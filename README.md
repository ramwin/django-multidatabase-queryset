# django-multidatabase-queryset
Use multi database as one.  
It's a common scenario that you want to  
store hot data in the default database (using SSD) and   
store cold data in the db_cold database (using HDD).  
You want to use it like normal queryset without considering it.

[![PyPI - Version](https://img.shields.io/pypi/v/django-multidatabase-queryset.svg)](https://pypi.org/project/django-multidatabase-queryset)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-multidatabase-queryset.svg)](https://pypi.org/project/django-multidatabase-queryset)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Usage
```
# add django_multidatabase_queryset to your project apps
INSTALLED_APPS = [
    ...
    "django_multidatabase_queryset",
]

# inherit the django_multidatabase_queryset.models.MultiDataBaseModel, set the database used
class UserAction(MultiDataBaseModel):
    DATABASES = ["default", "db_cold"]
    type = models.TextField(default="")
    detail = models.JSONField(default=dict)

# Use the objects as normal objects
data1 = UserAction(id=1, type="type4")
data1.save(using="default")
data2 = UserAction(id=2, type="type3")
data2.save(using="db_cold")
data3 = UserAction(id=3, type="type1")
data3.save(using="db_cold")
order_qs = UserAction.objects.order_by(
    "type", "pk")
data = list(order_qs)
LOGGER.info(data)
self.assertEqual(data[0].type, "type1")
self.assertEqual(data[1].type, "type3")
self.assertEqual(data[2].type, "type4")
self.assertEqual(order_qs.count(), 3)
```

## Installation

```console
pip install django-multidatabase-queryset
```

## License

`django-multidatabase-queryset` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
