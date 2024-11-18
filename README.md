Aiogram markups
===============

THIS PACKAGE REQUIRES LEGACY AIOGRAM.

PLEASE, DO NOT USE IT IN PRODUCTION.

This package helps you declaratively define and use inline or text markups.


Simple usage
------------

Let's start with example

```python

from aiogram_markups import Markup, Button

class MainMenu(Markup):
    settings = Button('Settings')
    help = Button('Help')

```

So, you can define markups via inheriting
from class `Markup`.  Then, you can
construct the markup and reply the user 
with this markup.


```python

bot = Bot(TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_handler(message):
    await message.answer(
        "Hi, im message with keyboard powered on aiogram_markups",
        reply_markup=MainMenu.get_markup()
    )
```

As you statically defined several buttons in the markup, you
can explicitly reference one of its buttons below the code,
and, for example, bind handler, that will trigger on message,
produced via pressing on button from your markup.  Just get
the button filter via Button.filter() and set the handler:


```python

@dp.message_handler(MainMenu.settings.filter())
async def settings_handler(message):
    await message.answer("I know you pressed on settings button!")


```

If you need an inline keyboard markup rather 
than text one, all that you need if to call
`get_inline_markup` instead of `get_markup`.
Note, that handler, bounded to button trigger,
will trigger on both of button representations:
text and inline.

As you do not state callback data, that
must be assigned to your inline buttons, 
callback data if generated automatically. It
is consists from a prefix and MD5 hash of 
button text. Default prefix is `::keyboard::`
(in Button.CALLBACK_ROOT). You can change prefix, but
it must exactly end with colon. 

Package also provides high-level API for altering
behavior of your bot.  To enable this framework,
you must set up the aiogram markups in the following way:

```python

from aiogram_markups import setup_aiogram_keyboards


setup_aiogram_keyboards(dp)

```

This will impact on markup defined above.  Now,
framework will check all incoming updates
if an update matches any button of defined markups.
If it is, the current state of dialog will 
be cleared.  So plainly defined markups is 
supposed to be globally accessible.

The ability of a button to interrupt current
state is defined by its flag `ignore_state`.
(True by default).  You can define this flag during
button assignation or provide default value for 
all buttons in markup by setting class-level variable
`__ignore_state__`.


Data keyboards
--------------

You can make keyboards with data in buttons.
Look at the following example:

```python

class DataKeyboardEx(Markup):
    __ignore_state__ = False
    
    hour = Button('Hour', data='h')
    minute = Button('Minute', data='m')
    second = Button('Second', data='s')

```

If you want to use inline markup, within handler,
data will be accessible in `call.data`. If you use 
text markup, data will be accessible in `message.text`.
Framework's middleware overrides them for you.
As mentioned before, the field `__ignore_state__` is
default value of ignore_state's for all buttons in the
markup. In data keyboards, if you use states, it must be 
set to False.

> Note: you can make complete messages from markups.
> Just write into field `__text__` the message text and
> call method `Markup.process`.  Unfortunately, design 
> of this feature is not thought out enough, so I not
> recommend to use it.


Inheritance
-----------

You can merge two markups via inheritance. For example,
you can have one undo keyboard and many data keyboards,
which must contain the undo button.

```python

from aiogram_markups import Orientation


class CancelKeyboard(Markup):
    __orientation__ = Orientation.BOTTOM
    
    cancel = Button('Cancel')


class DataKeyboardEx(CancelKeyboard):
    __ignore_state__ = False
    
    hour = Button('Hour', data='h')
    minute = Button('Minute', data='m')
    second = Button('Second', data='s')

```

In code above, field `__orientation__` with value
`Orientation.BOTTOM` means that this markup must be
at the bottom if joins to another. Like in state ignoring,
`__orientation__` is default one-off value for Button
fields `orientation`, that can be set explicitly.

> Note: you can bind your markups/buttons so
> one can process another.  Use method `bind`
> or operator `>>`. For example 
> `CancelKeyboard.cancel >> MainMenuKeyboard` binds 
> that cancel button must process MainMenuKeyboard.
> This feature must be assumed the same as 
> processing of the markups: its design 
> is not thought out enough.
