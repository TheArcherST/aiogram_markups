class MarkupType:
    TEXT = 'TEXT'
    INLINE = 'INLINE'
    UNDEFINED = f'{TEXT}+{INLINE}'


class Orientation:
    TOP = -1
    UNDEFINED = 0
    BOTTOM = 1


class MarkupScope:
    MESSAGE = 'm'
    CALLBACK_QUERY = 'c'
    UNDEFINED = f'{MESSAGE}+{CALLBACK_QUERY}'

    @classmethod
    def cast_to_type(cls, scope: str, ignore_error: bool = False):
        lib = {
            cls.MESSAGE: MarkupType.TEXT,
            cls.CALLBACK_QUERY: MarkupType.INLINE,
            cls.UNDEFINED: MarkupType.UNDEFINED
        }

        try:
            markup_type = lib[scope]
        except KeyError as e:
            if not ignore_error:
                raise e
            else:
                markup_type = scope
        else:
            pass

        return markup_type
