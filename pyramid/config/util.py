import functools
from hashlib import md5
import traceback
from zope.interface import implementer

from pyramid.compat import (
    bytes_,
    is_nonstr_iter
)
from pyramid.interfaces import IActionInfo

from pyramid.exceptions import ConfigurationError
from pyramid.predicates import Notted
from pyramid.registry import predvalseq
from pyramid.util import (
    TopologicalSorter,
    takes_one_arg,
)

TopologicalSorter = TopologicalSorter  # support bw-compat imports
takes_one_arg = takes_one_arg  # support bw-compat imports

@implementer(IActionInfo)
class ActionInfo(object):
    def __init__(self, file, line, function, src):
        self.file = file
        self.line = line
        self.function = function
        self.src = src

    def __str__(self):
        srclines = self.src.split('\n')
        src = '\n'.join('    %s' % x for x in srclines)
        return 'Line %s of file %s:\n%s' % (self.line, self.file, src)

def action_method(wrapped):
    """ Wrapper to provide the right conflict info report data when a method
    that calls Configurator.action calls another that does the same.  Not a
    documented API but used by some external systems."""
    def wrapper(self, *arg, **kw):
        if self._ainfo is None:
            self._ainfo = []
        info = kw.pop('_info', None)
        # backframes for outer decorators to actionmethods
        backframes = kw.pop('_backframes', 0) + 2
        if is_nonstr_iter(info) and len(info) == 4:
            # _info permitted as extract_stack tuple
            info = ActionInfo(*info)
        if info is None:
            try:
                f = traceback.extract_stack(limit=4)

                # Work around a Python 3.5 issue whereby it would insert an
                # extra stack frame. This should no longer be necessary in
                # Python 3.5.1
                last_frame = ActionInfo(*f[-1])
                if last_frame.function == 'extract_stack': # pragma: no cover
                    f.pop()
                info = ActionInfo(*f[-backframes])
            except Exception: # pragma: no cover
                info = ActionInfo(None, 0, '', '')
        self._ainfo.append(info)
        try:
            result = wrapped(self, *arg, **kw)
        finally:
            self._ainfo.pop()
        return result

    if hasattr(wrapped, '__name__'):
        functools.update_wrapper(wrapper, wrapped)
    wrapper.__docobj__ = wrapped
    return wrapper


MAX_ORDER = 1 << 30
DEFAULT_PHASH = md5().hexdigest()


class not_(object):
    """

    You can invert the meaning of any predicate value by wrapping it in a call
    to :class:`pyramid.config.not_`.

    .. code-block:: python
       :linenos:

       from pyramid.config import not_

       config.add_view(
           'mypackage.views.my_view',
           route_name='ok',
           request_method=not_('POST')
           )

    The above example will ensure that the view is called if the request method
    is *not* ``POST``, at least if no other view is more specific.

    This technique of wrapping a predicate value in ``not_`` can be used
    anywhere predicate values are accepted:

    - :meth:`pyramid.config.Configurator.add_view`

    - :meth:`pyramid.config.Configurator.add_route`

    - :meth:`pyramid.config.Configurator.add_subscriber`

    - :meth:`pyramid.view.view_config`

    - :meth:`pyramid.events.subscriber`

    .. versionadded:: 1.5
    """
    def __init__(self, value):
        self.value = value


# under = after
# over = before

class PredicateList(object):

    def __init__(self):
        self.sorter = TopologicalSorter()
        self.last_added = None

    def add(self, name, factory, weighs_more_than=None, weighs_less_than=None):
        # Predicates should be added to a predicate list in (presumed)
        # computation expense order.
        ## if weighs_more_than is None and weighs_less_than is None:
        ##     weighs_more_than = self.last_added or FIRST
        ##     weighs_less_than = LAST
        self.last_added = name
        self.sorter.add(
            name,
            factory,
            after=weighs_more_than,
            before=weighs_less_than,
            )

    def names(self):
        # Return the list of valid predicate names.
        return self.sorter.names

    def make(self, config, **kw):
        # Given a configurator and a list of keywords, a predicate list is
        # computed.  Elsewhere in the code, we evaluate predicates using a
        # generator expression.  All predicates associated with a view or
        # route must evaluate true for the view or route to "match" during a
        # request.  The fastest predicate should be evaluated first, then the
        # next fastest, and so on, as if one returns false, the remainder of
        # the predicates won't need to be evaluated.
        #
        # While we compute predicates, we also compute a predicate hash (aka
        # phash) that can be used by a caller to identify identical predicate
        # lists.
        ordered = self.sorter.sorted()
        phash = md5()
        weights = []
        preds = []
        for n, (name, predicate_factory) in enumerate(ordered):
            vals = kw.pop(name, None)
            if vals is None: # XXX should this be a sentinel other than None?
                continue
            if not isinstance(vals, predvalseq):
                vals = (vals,)
            for val in vals:
                realval = val
                notted = False
                if isinstance(val, not_):
                    realval = val.value
                    notted = True
                pred = predicate_factory(realval, config)
                if notted:
                    pred = Notted(pred)
                hashes = pred.phash()
                if not is_nonstr_iter(hashes):
                    hashes = [hashes]
                for h in hashes:
                    phash.update(bytes_(h))
                weights.append(1 << n + 1)
                preds.append(pred)
        if kw:
            from difflib import get_close_matches
            closest = []
            names = [ name for name, _ in ordered ]
            for name in kw:
                closest.extend(get_close_matches(name, names, 3))

            raise ConfigurationError(
                'Unknown predicate values: %r (did you mean %s)'
                % (kw, ','.join(closest))
            )
        # A "order" is computed for the predicate list.  An order is
        # a scoring.
        #
        # Each predicate is associated with a weight value.  The weight of a
        # predicate symbolizes the relative potential "importance" of the
        # predicate to all other predicates.  A larger weight indicates
        # greater importance.
        #
        # All weights for a given predicate list are bitwise ORed together
        # to create a "score"; this score is then subtracted from
        # MAX_ORDER and divided by an integer representing the number of
        # predicates+1 to determine the order.
        #
        # For views, the order represents the ordering in which a "multiview"
        # ( a collection of views that share the same context/request/name
        # triad but differ in other ways via predicates) will attempt to call
        # its set of views.  Views with lower orders will be tried first.
        # The intent is to a) ensure that views with more predicates are
        # always evaluated before views with fewer predicates and b) to
        # ensure a stable call ordering of views that share the same number
        # of predicates.  Views which do not have any predicates get an order
        # of MAX_ORDER, meaning that they will be tried very last.
        score = 0
        for bit in weights:
            score = score | bit
        order = (MAX_ORDER - score) / (len(preds) + 1)
        return order, preds, phash.hexdigest()
