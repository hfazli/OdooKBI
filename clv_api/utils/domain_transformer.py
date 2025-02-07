from typing import List, Tuple, Callable, Any

from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class DomainTransformer:

    def __init__(self, transformations: dict):
        self._transformations = transformations

    def transform(self, env: OdooEnvWrapper, domain: list) -> list:
        result = []
        if not domain:
            return result

        if not env:
            raise RuntimeError()

        for element in domain:
            transformed_element = [element]
            if isinstance(element, tuple):
                field_name = element[0]
                if field_name in self._transformations:
                    transformed_element = self._transformations[field_name](env, element)

            result.extend(transformed_element)

        return result


class DomainTransformerBuilder:

    def __init__(self):
        self._transformations = {}

    def add_transformation_for_field(
            self,
            field_name: str,
            transformation: Callable[[OdooEnvWrapper, Tuple[str, str, Any]], list]
    ):
        self._transformations[field_name.lower()] = transformation
        return self

    def build(self) -> DomainTransformer:
        return DomainTransformer(self._transformations)


class Transformations:

    @staticmethod
    def existent_string_field_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
        field_name, operator, value = domain_element
        if value is None or value == '':
            return [(field_name, operator, False)]

        return [domain_element]

    @staticmethod
    def nonexistent_field_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
        _, operator, value = domain_element
        new_operator = '=' if not ((operator == '=') ^ bool(value)) else '!='
        return [('id', new_operator, False)]
