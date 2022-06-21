from .delete import DeleteView
from .imports import ImportView
from .nodes import NodesView
from .sales import SalesView
from .statistic import StatisticView
from .test_handler import TestView

HANDLERS = (ImportView, DeleteView, NodesView, SalesView, StatisticView, TestView)
