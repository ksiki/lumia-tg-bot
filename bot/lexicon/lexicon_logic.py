import logging
from logging import Logger
from typing import Final, LiteralString, cast


LOG: Final[Logger] = logging.getLogger(__name__)


class LexiconCore:
    """
    Allows you to receive a text from the dictionary immediately, rather than the value of the field.

    Example:
        START_MESSAGE = "welcome_key"
        BaseLexicon.START_MESSAGE             # Will return the field value
        BaseLexicon.START_MESSAGE.text        # Will return the text from the dictionary
        BaseLexicon.START_MESSAGE.format()    # Will return the text from the dictionary
        f"{BaseLexicon.START_MESSAGE}"        # Will return the text from the dictionary
    
    How it works:
    The inheritor class must inherit from LexiconCore, str, Enum and define the __lexicon_data attribute.

    Example:
    class Inheritor(LexiconCore, str, Enum):
        __lexicon_data: dict[str, Any] = data
    """

    __data_ref: dict[str, str] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        data = getattr(cls, f"_{cls.__name__}__lexicon_data", None)
        if data is None:
            raise TypeError(f"The class {cls.__name__} must contain the __lexicon_data attribute")
        cls.__data_ref = data

    @property
    def text(self) -> str:
        text = self.__data_ref.get(self.value, None)

        if text is None:
            LOG.error(f"The KEY:{self.value} is missing in the {self.__class__.__name__}")
            return f"Error: {self.value} not found"
        
        return text
    
    def __str__(self) -> str:
        return self.text
    
    def format(self, *args, **kwargs) -> LiteralString:
        return cast(LiteralString, self.text.format(*args, **kwargs))