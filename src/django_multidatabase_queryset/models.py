"""
queryset support multi database
"""


import heapq

from collections import OrderedDict
from dataclasses import dataclass
from typing import List

from django.db import models
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet


@dataclass
class CompatableObject:
    """
    use order_by fields to compare two model instance
    """
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
                return True
            return first_value < second_value
        return self.instance.pk < other.instance.pk


class MultiQueryset:
    """
    queryset that support multi database, all the interface should work like a normal queryset

    work same as
        django.db.models.query.QuerySet
    """

    def __init__(self, model,
                 *args,
                 order_fields=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.query_dict = OrderedDict()
        self.order_fields = order_fields or []

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
            try:
                instance = next(iter_obj)
                result_candidates.append(
                    CompatableObject(
                        db_name=db_name,
                        order_by=self.order_fields,
                        instance=instance,
                    )
                )
            except StopIteration:
                continue
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
                queryset_iterations.pop(result.db_name)
            yield result.instance

    def _clone(self):
        c = self.__class__(
                model=self.model,
                order_fields=self.order_fields,
        )
        c.query_dict = self.query_dict.copy()
        return c

    def run_function_for_all_query(self, function, *args, **kwargs):
        clone = self._clone()
        for db_name, query in clone.query_dict.items():
            query = getattr(query, function)(*args, **kwargs)
            clone.query_dict[db_name] = query
        return clone

    def exclude(self, *args, **kwargs):
        return self.run_function_for_all_query(
                "exclude", *args, **kwargs
        )

    def filter(self, *args, **kwargs):
        """work same as queryset.filter"""
        return self.run_function_for_all_query(
                "filter", *args, **kwargs
        )

    def count(self, *args, **kwargs):
        """work same as queryset.count"""
        result = 0
        for query in self.query_dict.values():
            result += query.count()
        return result

    def order_by(self, *field_names):
        """work same as queryset.order_by"""
        self.order_fields = field_names
        new_query = self.run_function_for_all_query(
                "order_by", *field_names
        )
        new_query.order_fields = field_names
        return new_query

    def using(self, using: str):
        """work same as queryset.using"""
        return self.query_dict[using]

    def get(self, *args, **kwargs):
        """work same as queryset.get"""
        results = []
        for query in self.query_dict.values():
            try:
                instance = query.get(*args, **kwargs)
            except self.model.DoesNotExist:
                continue
            # if MultipleObjectsReturned raised, just raise it
            results.append(instance)
        if len(results) == 1:
            return results[0]
        raise self.model.MultipleObjectsReturned

    def exists(self):
        for query in self.query_dict.values():
            if query.exists():
                return True
        return False

    def first(self):
        for i in self:
            return i

    def create(self, *args, **kwargs):
        if "default" in self.query_dict:
            return self.query_dict["default"].create(*args, **kwargs)
        else:
            return self.query_dict.values()[0].create(*args, **kwargs)


class MultiDataBaseManager(BaseManager.from_queryset(QuerySet)):
    # pylint: disable=too-few-public-methods
    """
    This Manager will iter all the DATABASES of model
    """

    def get_queryset(self) -> MultiQueryset:
        """
        iter all the databases and return a MultiQueryset
        """
        queryset = MultiQueryset(model=self.model)
        for db_name in self.model.DATABASES:
            queryset.query_dict[db_name] = super().get_queryset().using(db_name)
        return queryset


class MultiDataBaseModel(models.Model):
    """
    MultiDataBaseModel can be used when you have multidatabase and want to use these database as one
    """
    DATABASES = ["default"]
    objects = MultiDataBaseManager()

    class Meta:
        abstract = True
