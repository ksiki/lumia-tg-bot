def inherit_doc(cls):
    """
    A decorator for inheriting documentation by an inheritor class
    """

    for base in cls.__mro__[1:]:
        if base.__doc__:
            cls.__doc__ = base.__doc__
            break
    return cls
