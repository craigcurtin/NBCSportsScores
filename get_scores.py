# 
# very heavily gouged from:
# https://gist.github.com/criccomini/3805436
# https://github.com/metral/scores/blob/master/get_scores.py

#===============================================================================
import pytz
import datetime
import time
import urllib2
import json
import os
import xml.etree.ElementTree as ET
import utils
from utils import Game
import env_settings
import logging
from time import gmtime, strftime
#import timedelta

#http://www.nbcnews.com/id/34622365
#-------------------------------------------------------------------------------
URL = "http://scores.nbcsports.msnbc.com" + \
        "/ticker/data/gamesMSNBC.js.asp?jsonp=true&sport=%s&period=%s"
#-------------------------------------------------------------------------------
class DailyGames():
    '''DailyGames() - Get Games for a specified League on a specific day'''

    def __init__(self, league, yyyymmdd=None):
        '''GameDay(league, targetDate [yyyymmdd format)])'''
        if None==yyyymmdd:
            #yyyymmdd = int(datetime.datetime.now(\
            #        pytz.timezone(env_settings.LOCAL_TZ)).strftime("%Y%m%d"))
            yyyymmdd = datetime.datetime.now(pytz.timezone(env_settings.LOCAL_TZ)).strftime('%Y%m%d')
        self.yyyymmdd = yyyymmdd
        self.league = league
        return
    def GetAndProcessData(self):
        games = []
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                target_url = URL % (self.league, self.yyyymmdd)
                f = urllib2.urlopen(target_url)
                logging.debug("Data Source:  %s" % (target_url))
                jsonp = f.read()
                f.close()
                json_str = jsonp.replace(\
                        'shsMSNBCTicker.loadGamesData(', '').replace(');', '')
                    
                # kind of tricky here, data is XML inside JSON
                json_parsed = json.loads(json_str)
            
                for game_str in json_parsed.get('games', []):
                    game_tree = ET.XML(game_str)
                    #logging.debug(game_str)

                    game = {}
                    game['league'] = self.league.strip()
                    game['gameCode'] = game_tree.get('gamecode')
                
                    self._getGameInfo(game_tree, game)
                    self._getAwayInfo(game_tree, game)
                    self._getHomeInfo(game_tree, game)
                    
                    # write XML data for later reference
                    debugXMLfile = "xml\\%s_%s_at_%s_%s.xml" % (game['league'], game['awayAlias'], game['homeAlias'], datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
                    open(debugXMLfile,"w").write(game_str)
                    logging.debug('firefox.exe %s\\%s' % (os.getcwd(), debugXMLfile) )
                
                    games.append(game)
                    #logging.debug(game)
            except Exception, e:
                print e
                logging.exception(e)
                time.sleep(5)
                continue
            break
        return games
    
    def _getGameInfo(self, game_tree, game):
        '''getGameInfo( XMLtree, gameDictionary)'''
        # get all the Game Info data                
        gamestate_tree = game_tree.find('gamestate')
        game['gameStatus'] = gamestate_tree.get('status')
        game['gameTV'] = gamestate_tree.get('tv')
        game['gameStatus'] = gamestate_tree.get('status')
        game['gameStatus1'] = gamestate_tree.get('display_status1')
        game['gameStatus2'] = gamestate_tree.get('display_status2')
        game['gameStartDate'] = gamestate_tree.get('gamedate')
        gt = gamestate_tree.get('gametime')
        struct_time = time.strptime(gt,'%I:%M %p')
        game['gameStartTime'] = strftime('%H:%M %z', struct_time)
        game['gameHref'] = gamestate_tree.get('href')
        try:
            game['gameReason'] = gamestate_tree.get('reason')
        except AttributeError:
            game['gameReason'] = 'unknown'
        
        return
        
    def _getAwayInfo(self, game_tree, game):
        # get all the Visiting Team data                
        visiting_tree = game_tree.find('visiting-team')
        game['awayScore'] = visiting_tree.get('score')
        game['awayAlias'] = visiting_tree.get('alias').strip("#1234567890 ")
        game['awayNickname'] = visiting_tree.get('nickname')
        game['awayDisplayName'] = visiting_tree.get('display_name')
        game['awayConference'] = visiting_tree.get('conference')
        game['awayDivision'] = visiting_tree.get('division')
        # get real-time data if not pregame
        if "Pre-Game" != game['gameStatus']:
            pass
        return
        
    def _getHomeInfo(self, game_tree, game):
        # get all the Home Team data                
        home_tree = game_tree.find('home-team')
        game['homeScore'] = home_tree.get('score')
        game['homeAlias'] = home_tree.get('alias').strip("#1234567890 ")
        game['homeNickname'] = home_tree.get('nickname')
        game['homeDisplayName'] = home_tree.get('display_name')
        game['homeConference'] = home_tree.get('conference')
        game['homeDivision'] = home_tree.get('division')
        # get real-time data if not pregame
        if "Pre-Game" != game['gameStatus']:
            pass
        
#-------------------------------------------------------------------------------
def main():

    untilDates = []
    SUNDAY=0
    nextDay=datetime.datetime.today()
    
    # build a List of dates we want Games for 
    while(SUNDAY != nextDay.weekday()):
        untilDates.append(nextDay.strftime('%Y%m%d'))
        nextDay += datetime.timedelta(1)
        
    for targetDate in untilDates:
        for league in ['NFL', 'MLB', 'NBA', 'NHL', 'CBK', 'CFB']:
            gd = DailyGames(league, targetDate)
            todays_games = gd.GetAndProcessData()
            for gameInfo in todays_games:
                game = Game(info=gameInfo)
                print game.toString()
                utils.session.add(game)
                utils.session.commit()
            #time.sleep(2)
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(filename='get_scores.log', level=logging.DEBUG)
    logging.info('Started')
    main()
    logging.info('Normal Termination')
#===============================================================================
