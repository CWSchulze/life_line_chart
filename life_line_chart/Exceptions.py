

class LifeLineChartCannotMoveIndividual(Exception):
   def __init__(self, *args):
      self.args = args


class LifeLineChartCollisionDetected(Exception):
   def __init__(self, *args):
      self.args = args


class LifeLineChartNotEnoughInformationToDisplay(Exception):
   def __init__(self, *args):
      self.args = args
