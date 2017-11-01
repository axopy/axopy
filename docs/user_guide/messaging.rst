.. _messaging:

=========
Messaging
=========

.. currentmodule:: axopy.messaging

Since AxoPy is an event-driven framework, a messaging system is critical for
setting up communication between components of the application. If you're
unfamiliar with this style of programming, the basic idea is that you write
code specifying what a small piece of the application *does*, then you set up
connections between the pieces so they run at the appropriate times. This might
sound like an odd way to do things at first, but it enables and encourages
composability.

As a simple example, imagine you have a :class:`Task` in which incoming data
from a sensor is used to update the position of a cursor on screen. scenario in
which you have a function that processes some data, and you want the processed
data to 
