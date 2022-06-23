from .delete import DeleteView
from .deleteall import DeleteAllView
from .imports import ImportView
from .listview import ListView
from .nodes import NodesView
from .sales import SalesView
from .statistic import StatisticView

HANDLERS = (ImportView, DeleteView, NodesView, SalesView, StatisticView, ListView, DeleteAllView)
