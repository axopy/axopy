"""Base classes for pipelines and pipeline blocks."""


class PipelineBlock(object):
    """Base class for all blocks.

    Notes
    -----
    Blocks should take their parameters in ``__init__`` and provide at least
    the ``process`` method for taking in data and returning some result.
    """

    def __init__(self, name=None, hooks=None):
        self._name = name
        if name is None:
            self._name = self.__class__.__name__

        self._hooks = hooks
        if hooks is None:
            self._hooks = []

    def __call__(self, *args, **kwargs):
        return self.process(*args, **kwargs)

    def process(self, data):
        """Process input data and produce a result.

        Subclasses must implement this method, otherwise it shouldn't really be
        a ``PipelineBlock``.
        """
        raise NotImplementedError

    def clear(self):
        """Clear the state of the block.

        Some blocks don't keep stateful attributes, so ``clear`` does nothing
        by default.
        """
        pass

    @property
    def name(self):
        return self._name

    @property
    def hooks(self):
        return self._hooks

    def __repr__(self):
        return "%s.%s()" % (
            self.__class__.__module__,
            self.__class__.__name__
        )


class Pipeline(PipelineBlock):
    """Feedforward arrangement of blocks for processing data.

    A :class:`Pipeline` contains a set of :class:`PipelineBlock` objects which
    operate on data to produce a final output.

    To create a pipeline, the following two rules are needed: blocks in a list
    processed in series, and blocks in a tuple are processed in parallel.

    Blocks that are arranged to take multiple inputs should expect to take the
    corresponding number of inputs in the order they are given. It is up to the
    user constructing the pipeline to make sure that the arrangement of blocks
    makes sense.

    Parameters
    ----------
    blocks : container
        The blocks in the pipline, with lists processed in series and tuples
        processed in parallel.

    Attributes
    ----------
    named_blocks : dict
        Dictionary of blocks in the pipeline. Keys are the names given to the
        blocks in the pipeline and values are the block objects.
    """

    def __init__(self, blocks, name=None):
        super(Pipeline, self).__init__(name=name)
        self.blocks = blocks
        self.named_blocks = {}

        # traverse the block structure to fill named_blocks
        self._call_block('name', self.blocks)

    def process(self, data):
        """
        Calls the ``process`` method of each block in the pipeline, passing the
        outputs around as specified in the block structure.

        Parameters
        ----------
        data : object
            The input to the first block(s) in the pipeline. The type/format
            doesn't matter, as long as the blocks you define accept it.

        Returns
        -------
        out : object
            The data output by the ``process`` method of the last block(s) in
            the pipeline.
        """
        out = self._call_block('process', self.blocks, data)
        return out

    def clear(self):
        """
        Calls the ``clear`` method on each block in the pipeline. The effect
        depends on the blocks themselves.
        """
        self._call_block('clear', self.blocks)

    def _call_block(self, fname, block, data=None):
        if isinstance(block, list):
            out = self._call_list(fname, block, data)
        elif isinstance(block, tuple):
            out = self._call_tuple(fname, block, data)
        else:
            if fname == 'name':
                self.named_blocks[block.name] = block
                return

            f = getattr(block, fname)
            if data is not None:
                out = f(data)
            else:
                out = f()

            if hasattr(block, 'hooks') and fname == 'process':
                for hook in block.hooks:
                    hook(out)

        return out

    def _call_list(self, fname, block, data=None):
        out = data
        for b in block:
            out = self._call_block(fname, b, out)

        return out

    def _call_tuple(self, fname, block, data=None):
        out = []
        for b in block:
            out.append(self._call_block(fname, b, data))

        return out


class PassthroughPipeline(Pipeline):
    """Convenience block for passing input along to output.

    A passthrough pipeline block is useful when you want to process some data
    then provide both the processed output as well as the original input to
    another block downstream.
    """

    def __init__(self, blocks, expand_output=True, name=None):
        super(PassthroughPipeline, self).__init__(blocks, name=name)
        self.expand_output = expand_output

    def process(self, data):
        out = super(PassthroughPipeline, self).process(data)
        if self.expand_output:
            ldata = [data]
            ldata.extend(out)
            return ldata
        else:
            return data, out


class CallablePipelineBlock(PipelineBlock):
    """A `PipelineBlock` that does not require persistent attributes.

    Many `PipelineBlock` implementations don't require attributes to update
    on successive calls to the `process` method, but instead are essentially a
    function that can be called repeatedly. This class is for conveniently
    creating such a block.

    If the function you want to use takes additional arguments, such as a
    keyword argument that

    Note: if you use an anonymous function as the `func` argument, (e.g.
    ``lambda x: 2*x``), it is recommended to explicitly give the block a
    meaningful name.

    Parameters
    ----------
    func : callable(data)
        Function that gets called when the block's `process` method is called.
        Should take a single input and return output which is compatible with
        whatever is connected to the block.
    func_args : list, optional
        List (or tuple) of additional arguments to pass to `func` when calling
        it for processing. If None (default), no arguments are used.
    func_kwargs : dict
        Keyword argument name/value pairs to pass to `func` when calling it for
        processing. If None (default), no keyword arguments are used.
    name : str, optional, default=None
        Name of the block. By default, the name of the `processor` function is
        used.
    hooks : list, optional, default=None
        List of callables (callbacks) to run when after the block's `process`
        method is called.
    """

    def __init__(self, func, func_args=None, func_kwargs=None, name=None,
                 hooks=None):
        if name is None:
            name = func.__name__
        super(CallablePipelineBlock, self).__init__(name=name, hooks=hooks)
        self.func = func
        self.func_args = func_args if func_args is not None else []
        self.func_kwargs = func_kwargs if func_kwargs is not None else {}

    def process(self, data):
        return self.func(data, *self.func_args, **self.func_kwargs)
