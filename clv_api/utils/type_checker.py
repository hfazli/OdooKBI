from datetime import datetime
from dateutil.parser import parse, ParserError
from typing import Any


class TypeChecker:
    """
    A utility class for type-safe conversions, providing methods to convert various types.
    """

    @staticmethod
    def get_as_bool(value: Any) -> bool:
        """
        Convert a given value to a boolean. Returns True for "true" string (case-insensitive),
        boolean True, and False for "false" (case-insensitive), boolean False, or None.
        @raise RuntimeError: If the value is neither a recognized boolean type nor the strings "true" or "false".
        @param value: The value to be converted to a boolean.
        @return: The converted boolean value.
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() == 'true':
                return True
            if value.lower() == 'false':
                return False

        raise RuntimeError("The value '{}' cannot be converted to boolean".format(value))

    @staticmethod
    def get_as_int(value: Any) -> int:
        """
        Convert a given value to an integer. If the value is a float, it is rounded and converted.
        Returns 0 for None.
        @raise RuntimeError: If the value cannot be converted to an integer.
        @param value: The value to be converted to an integer.
        @return: The converted integer value.
        """
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(round(value))
        try:
            return int(value)
        except (ValueError, TypeError):
            raise RuntimeError("The value '{}' cannot be converted to integer".format(value))

    @staticmethod
    def get_as_float(value: Any) -> float:
        """
        Convert a given value to a float. If the value is an integer, it is converted to float.
        Returns 0.0 for None.
        @raise RuntimeError: If the value cannot be converted to a float.
        @param value: The value to be converted to a float.
        @return: The converted float value.
        """
        if value is None:
            return 0.0
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        try:
            return float(value)
        except (ValueError, TypeError):
            raise RuntimeError("The value '{}' cannot be converted to float".format(value))

    @staticmethod
    def get_as_str(value: Any) -> str:
        """
        Convert a given value to a string. Returns an empty string for None,
        or the string representation of the value for other types.
        @param value: The value to be converted to a string.
        @return: The converted string value.
        """
        if value is None:
            return ''
        if isinstance(value, str):
            return value
        return str(value)

    @staticmethod
    def get_as_datetime(value: Any) -> datetime:
        """
        Convert a given value to a datetime.
        @raise RuntimeError: If the value cannot be converted to a datetime.
        @param value: The value to be converted to a datetime.
        @return: The converted datetime value.
        """
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return parse(value)
            except ParserError:
                pass
        raise RuntimeError("The value '{}' cannot be converted to datetime".format(value))
