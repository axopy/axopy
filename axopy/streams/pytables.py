import tables
import numpy


class PyTablesSink(object):

    def __init__(self, f, table_name, data_format):
        self.f = f
        self.table_name = table_name
        self.data_format = data_format

        self.description = format_to_description(self.data_format)
        self.table = self.f.create_table('/', self.table_name,
                                         self.description)

    def __call__(self, *args):
        row = self.table.row
        for arg, (colname, coltype) in zip(args, self.data_format):
            row[colname] = arg
        row.append()
        self.table.flush()


def format_to_description(data_format):
    """Converts a data format specification to a PyTables description.

    The data format is a list of 2-tuples with `(var_name, var_dtype)` pairs,
    where `var_name` is a string and `var_dtype` is the data type for the
    column. If `var_dtype` is a regular Python type (e.g. `float`, `int`,
    etc.), it is converted to a numpy dtype via `numpy.dtype`. If it is a numpy
    dtype, it is just passed along to PyTables `Col.from_dtype` to create the
    column.

    The output is a PyTables `Description` object that can be used to create a
    table.
    """
    desc = {}
    for i, (colname, coltype) in enumerate(data_format):
        if isinstance(coltype, numpy.dtype):
            dtype = coltype
        else:
            dtype = numpy.dtype(coltype)

        desc[colname] = tables.Col.from_dtype(dtype, pos=i)

    return desc
