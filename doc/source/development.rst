===========
Development
===========

These are some notes on developing and extending AxoPy.


Messaging
---------

The messaging system consists of emitter and receiver decorators, which can be
applied to any function or method. We currently follow the `PyQt
<http://pyqt.sourceforge.net/Docs/PyQt4/new_style_signals_slots.html>`_
convention fairly closely in that emitters are similar to pyqtSignal objects
(the decorator replaces the function/method with an "emitter" object) and
receivers are essentially functions/methods with `connect` and `disconnect`
methods to make the system a bit more symmetric.

The decorators themselves are specified in `axopy/messaging/decorators.py`. The
emitter decorator relies completely on the backend implementation to return the
object that takes the place of the function/method decorated by `@emitter`. The
receiver decorator is very simple and simply adds `connect` and `disconnect`
methods to what is otherwise a normal function/method. This is currently not
extendable.

The backend for the emitter is specified using the `settings` module. This can
either be a string (either 'qt' or 'py' to use built-in backends) or a base
emitter that replaces the function/method decorated by `@emitter`. Since you're
here in the development docs, you are probably interested in adding a backend
that is not currently built in. In that case, you can inherit from
`BaseEmitter` and implement just three methods: `connect`, `disconnect`, and
`emit`. `emit` is the key method that actually provides the connected receivers
with data. `connect` and `disconnect` control which receivers are actually
given data (called) when the emitter emits. The 'py' emitter backend is a very
simple but clear example of a fully specified emitter backend.

**TODO** document the data format
