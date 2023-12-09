import heapq

from collections import OrderedDict
from dataclasses import dataclass
from typing import List

from django.db import models
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet


@dataclass
class CompatableObject:
    db_name: str
    order_by: List[str]
    instance: models.Model

    def __lt__(self, other):
        for field in self.order_by:
            first_value = getattr(self.instance, field)
            second_value = getattr(other.instance, field)
            if first_value is None:
                if second_value is None:
                    continue
                else:
                    return True
            return first_value < second_value
        return self.instance.pk < other.instance.pk


class MultiQueryset:

    def __init__(self, model, order_fields=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.query_dict = OrderedDict()
        self.order_fields = order_fields

    def __iter__(self):
        if not self.order_fields:
            for query in self.query_dict.values():
                for i in query:
                    yield i
            return
        result_candidates = []
        queryset_iterations = {
            db_name: iter(query)
            for db_name, query in self.query_dict.items()
        }
        for db_name, iter_obj in queryset_iterations.items():
            result_candidates.append(
                CompatableObject(
                    db_name=db_name,
                    order_by=self.order_fields,
                    instance=next(iter_obj),
                )
            )
        heapq.heapify(result_candidates)
        while result_candidates:
            result: CompatableObject
            result = heapq.heappop(result_candidates)
            try:
                next_candidate = next(queryset_iterations[result.db_name])
                heapq.heappush(
                    result_candidates,
                    CompatableObject(
                        result.db_name,
                        result.order_by,
                        next_candidate,
                    )
                )
            except StopIteration:
                pass
            yield result.instance

    def compare_function(self, a, b):
        for field in self.order_by:
            if getattr(a, field) > getattr(b, field):
                return True
            if getattr(a, field) < getattr(b, field):
                return False
        return True

    def filter(self, *args, **kwargs):
        result = MultiQueryset(model=self.model)
        for db_name, query in self.query_dict.items():
            result.query_dict[db_name] = query.filter(*args, **kwargs)
        return result

    def count(self, *args, **kwargs):
        result = 0
        for query in self.query_dict.values():
            result += query.count()
        return result

    def order_by(self, *field_names):
        self.order_fields = field_names
        result = MultiQueryset(model=self.model,
                               order_fields=field_names)
        for db_name, query in self.query_dict.items():
            result.query_dict[db_name] = query.order_by(*field_names)
        return result

    def using(self, using: str):
        return self.query_dict[using]

    def get(self, *args, **kwargs):
        results = []
        for db_name, query in self.query_dict.items():
            try:
                instance = query.get(*args, **kwargs)
            except self.model.DoesNotExist:
                continue
            except self.model.MultipleObjectsReturned:
                raise
            results.append(instance)
        if len(results) == 1:
            return results[0]
        raise self.model.MultipleObjectsReturned


class MultiDataBaseManager(BaseManager.from_queryset(QuerySet)):

    def get_queryset(self) -> List[QuerySet]:
        queryset = MultiQueryset(model=self.model)
        for db_name in self.model.DATABASES:
            queryset.query_dict[db_name] = super().get_queryset().using(db_name)
        return queryset


class MultiDataBaseModel(models.Model):
    DATABASES = ["default"]
    objects = MultiDataBaseManager()

    class Meta:
        abstract = True
