from typing import Optional, TypeAlias


Error: TypeAlias = str | Exception


class UnwrapError(Exception):
    pass


class Result[T]:
    _data: Optional[T]
    _err: Optional[Error]

    def __init__(self, data: Optional[T] = None, err: Optional[Error] = None):
        if data is None and err is None:
            raise TypeError("Expects either data or an error")
        self._data = data
        self._err = err

    @staticmethod
    def ok[U](data: U) -> Result[U]:
        return Result(data=data)

    @staticmethod
    def error(err: Error) -> Result:
        return Result(err=err)

    def is_err(self) -> bool:
        return self._err is not None

    def is_ok(self) -> bool:
        return self._err is None

    @property
    def data(self) -> T:
        if self._data is None:
            if isinstance(self._err, str):
                raise UnwrapError(f"Trying to unwrap Result with error: {self._err}")
            else:
                raise UnwrapError("Trying to unwrap Result with error") from self._err
        return self._data

    @property
    def err(self) -> Error:
        if self._err is None:
            raise AttributeError("Trying to get Error on successful Result")
        return self._err

    def err_msg(self) -> str:
        if self._err is None:
            raise AttributeError("Trying to get error message on successful Result")
        return str(self._err)
