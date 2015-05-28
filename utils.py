#===============================================================================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Integer, String
import sys
import MySQLdb
import warnings 
import env_settings
from datetime import datetime
from pytz import timezone
import pytz
import dateutil.parser as dparser
#-------------------------------------------------------------------------------
warnings.filterwarnings( 
        action="ignore", 
        category=MySQLdb.Warning) 

host = env_settings.MYSQL_HOST
user = env_settings.MYSQL_USER
port = env_settings.MYSQL_PORT
password = env_settings.MYSQL_PASS
db_name = env_settings.MYSQL_DB
db_path = "mysql://%s:%s@%s:%s" % (user, password, host, port)

#-------------------------------------------------------------------------------

engine = create_engine(db_path, echo=False)
engine.execute("CREATE DATABASE IF NOT EXISTS %s" % db_name)
engine.execute("USE %s" % db_name)
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

#-------------------------------------------------------------------------------
class Game(Base):
    __tablename__ = 'NBCSportsGames'
    id = Column(Integer, primary_key=True)
    league = Column(String(16))
    gameCode = Column(Integer)
    gameStatus = Column(String(32))
    #gameStartTime = Column(String(50))
    #gameStartDate = Column(String(50))
    gameStartDateTime = Column(DateTime)    # ALWAYS EDT in Database!!
    gameStatus = Column(String(64))
    gameStatus1 = Column(String(64))
    gameStatus2 = Column(String(64))
    gameTV = Column(String(16))
    gameHref = Column(String(128))
    awayAlias = Column(String(16))
    awayScore = Column(Integer)
    homeAlias = Column(String(16))
    homeScore = Column(Integer)

    def __init__(self, *args, **kwargs):
        if kwargs:
            info  = kwargs.get('info')

            self.league = info['league'].upper()
            self.gameCode = info['gameCode']
            self.gameStatus = info['gameStatus']
            self.gameStartTime = info['gameStartTime'].replace('Eastern Daylight Time', 'EDT')
            self.gameStartDate = info['gameStartDate']
            self.gameStatus = info['gameStatus']
            self.gameStatus1 = info['gameStatus1']
            self.gameStatus2 = info['gameStatus2']
            self.gameReason = info['gameReason']    # only when Status == Delayed
            
            year = datetime.today().year
            month = int(self.gameStartDate.split('/')[0])
            day = int(self.gameStartDate.split('/')[1])
            hour = int(self.gameStartTime[0:2])
            minute = int(self.gameStartTime[3:5])
            self.gameStartDateTime = datetime(year, month, day, hour, minute)
            self.gameTV = info['gameTV']
            self.gameHref =  info['gameHref']

            self.homeAlias = info['homeAlias'].upper()
            if ''==info['homeScore']:
                self.homeScore = 0
            else:
                self.homeScore = info['homeScore']
                
            self.awayAlias = info['awayAlias'].upper()
            if ''==info['awayScore']:
                self.awayScore = 0
            else:
                self.awayScore = info['awayScore']
        return

    def toString(self):
            # this works for MLB ... othere ?? we'll try
            if   'Pre-Game'==self.gameStatus:
                status='%s @ %s' % (self.gameStartDate, self.gameStartTime)
            elif 'Final'==self.gameStatus:
                status=self.gameStatus1
            elif 'Delayed'==self.gameStatus:
                status=self.gameReason
            else:
                try:
                    # see if gameStatus == 'today()'
                    month, day = self.gameStatus1.split('/')
                except:
                    # if split() fails, force it to the else clause
                    month=0; day=0
                
                if int(month)==datetime.today().month and \
                    int(day)==datetime.today().day:
                    status='@ %s' % (self.gameStatus2)
                else:
                    status='%s %s' % (self.gameStatus1, self.gameStatus2)
                
            buf='%s, %11s, %17s, %3s(%3s) @ %3s(%3s) on %s' % ( self.league,
                                                                self.gameStatus,
                                                                status,
                                                                self.awayAlias,
                                                                self.awayScore,
                                                                self.homeAlias,
                                                                self.homeScore,
                                                                self.gameTV)
            return buf
        
#-------------------------------------------------------------------------------
Base.metadata.create_all(engine)
#-------------------------------------------------------------------------------
def localize_game_time(game_time, local_tz):
    game_tz = timezone(env_settings.GAME_TZ)

    # Get current UTC time
    current_date_format='%m/%d/%Y %H:%M:%S %Z'
    current_date_utc = datetime.now(tz=pytz.utc)

    # Convert current UTC to TZ game info is based off (Eastern)
    current_date_eastern = current_date_utc.astimezone(game_tz)

    # Tweak current Eastern time to use the hour & minute game is at
    # This is to assure we have every other part of the datetime obj correct
    game_date_eastern_str= "%s/%s/%s %s" % (
            current_date_eastern.month,
            current_date_eastern.day,
            current_date_eastern.year,
            game_time)

    game_date_eastern = game_tz.localize(dparser.parse(game_date_eastern_str))

    # Convert Eastern game time to the local TZ specified
    game_date_local = game_date_eastern.astimezone(timezone(local_tz))

    # Return hour:minute am/pm as we dont need rest of date info
    game_date_short_format = '%I:%M %p'
    game_date_local_short = game_date_local.strftime(game_date_short_format)

    return game_date_local_short
#===============================================================================
