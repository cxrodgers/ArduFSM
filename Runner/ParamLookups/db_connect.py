from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound
import os.path as path
import sys



#Heroku Postgres credentials that should be stored on disk
this_directory = path.dirname(path.abspath(__file__))
credentials = open(path.join(this_directory,"db_credentials"), "r").read().strip()

engine = create_engine(credentials, echo=False)
Base = declarative_base(engine)


class Boards(Base):
  __tablename__ = 'runner_board'
  __table_args__ = {'autoload' : True}


class Boxes(Base):
  __tablename__ = 'runner_box'
  __table_args__ = {'autoload' : True}

  @property
  def video_window_position(self):
      return (self.video_window_position_x, self.video_window_position_y)

  @property
  def gui_window_position(self):
      return (self.gui_window_position_x, self.gui_window_position_y)

  @property
  def window_position_IR_plot(self):
      return (self.window_position_IR_plot_x, self.window_position_IR_plot_y)        
  
  @property
  def mean_water_consumed(self):
      """Return mean water consumed over last N sessions"""
      return self.session_list[0].name



class Mouses(Base):
  __tablename__ = 'runner_mouse'
  __table_args__ = {'autoload' : True}

def getByName(table, name, session):
  try:
    return session.query(table).filter(table.name == name).one()
  except NoResultFound:
    print "'%s' not found in %s" % (name, table.__name__)
    sys.exit(1)
  except MultipleResultsFound:
    print "'%s' found more than once in %s" % (name, table.__name__)
    sys.exit(1)



def loadSession():
  """ Begin session """
  metadata = Base.metadata
  Session = sessionmaker(bind=engine)
  session = Session()
  return session
