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

#http://www.nbcnews.com/id/34622365
#-------------------------------------------------------------------------------
URL = "http://scores.nbcsports.msnbc.com" + \
        "/ticker/data/gamesMSNBC.js.asp?jsonp=true&sport=%s&period=%s"
#-------------------------------------------------------------------------------
def GameDay(league, yyyymmdd=None):
    '''GameDay(league, targetDate [yyyymmdd format)])'''
    if None==yyyymmdd:
        #yyyymmdd = int(datetime.datetime.now(\
        #        pytz.timezone(env_settings.LOCAL_TZ)).strftime("%Y%m%d"))
        yyyymmdd = datetime.datetime.now(pytz.timezone(env_settings.LOCAL_TZ)).strftime('%Y%m%d')
    games = []
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            target_url = URL % (league, yyyymmdd)
            f = urllib2.urlopen(target_url)
            logging.debug("Data Source:  %s" % (target_url))
            jsonp = f.read()
            f.close()
            json_str = jsonp.replace(\
                    'shsMSNBCTicker.loadGamesData(', '').replace(');', '')
                    
            # kind of tricky here, its XML inside JSON
            json_parsed = json.loads(json_str)
            
            for game_str in json_parsed.get('games', []):
                game_tree = ET.XML(game_str)
                logging.debug(game_str)

                # get all the Game Info data                
                gamestate_tree = game_tree.find('gamestate')
                gameStatus = gamestate_tree.get('status')
                gameTV = gamestate_tree.get('tv')
                gameStatus = gamestate_tree.get('status')
                gameStatus1 = gamestate_tree.get('display_status1')
                gameStatus2 = gamestate_tree.get('display_status2')
                gameDate = gamestate_tree.get('gamedate')
                gt = gamestate_tree.get('gametime')
                struct_time = time.strptime(gt,'%I:%M %p')
                gameTime = strftime('%H:%M %z', struct_time)
                gameHref = gamestate_tree.get('href')
                
                # get all the Visiting Team data                
                visiting_tree = game_tree.find('visiting-team')
                awayScore = visiting_tree.get('score')
                awayAlias = visiting_tree.get('alias').strip("#1234567890 ")
                awayNickname = visiting_tree.get('nickname')
                awayDisplayName = visiting_tree.get('display_name')
                awayConference = visiting_tree.get('conference')
                awayDivision = visiting_tree.get('division')
                # get real-time data if not pregame
                if "Pre-Game" != gameStatus:
                    pass

                # get all the Home Team data                
                home_tree = game_tree.find('home-team')
                homeScore = home_tree.get('score')
                homeAlias = home_tree.get('alias').strip("#1234567890 ")
                homeNickname = home_tree.get('nickname')
                homeDisplayName = home_tree.get('display_name')
                homeConference = home_tree.get('conference')
                homeDivision = home_tree.get('division')
                # get real-time data if not pregame
                if "Pre-Game" != gameStatus:
                    pass
                
                # write XML data for later reference
                ofile = "xml\\%s_%s_at_%s_%s.xml" % (league, awayAlias, homeAlias, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
                open(ofile,"w").write(game_str)

                game_start = int(time.mktime(time.strptime(\
                        '%s %s' % (gamestate_tree.get('gametime'), yyyymmdd),\
                        '%I:%M %p %Y%m%d')))
                start = datetime.datetime.fromtimestamp(\
                        game_start,
                        pytz.timezone('US/Pacific')).strftime('%I:%M %p')
                        
                start = utils.localize_game_time(start, env_settings.LOCAL_TZ)

                start = gameTime
                
                game = { 'league': league.rstrip(),
                         'start': start.rstrip(),
                         'home': homeAlias.rstrip(),
                         'away': awayAlias.rstrip(),
                         'home-score': homeScore.rstrip(),
                         'away-score': awayScore.rstrip(),
                         'status': gameStatus.rstrip(),
                         'tv': gameTV.rstrip(),
                         'clock': gameStatus1.rstrip(),
                         'clock-section': gameStatus2.rstrip()
                    }
                games.append(game)
                logging.debug(game)
        except Exception, e:
            print e
            logging.exception(e)
            time.sleep(5)
            continue
        break

    return games
#-------------------------------------------------------------------------------
def main():
    for league in ['NFL', 'MLB', 'NBA', 'NHL', 'CBK', 'CFB']:
        todays_games = GameDay(league)
        for gameInfo in todays_games:
            game = Game(info=gameInfo)
            print game.toString()
            utils.session.add(game)
            utils.session.commit()
        time.sleep(5)
#-------------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(filename='get_scores.log', level=logging.DEBUG)
    logging.info('Started')
    main()
    logging.info('Normal Termination')
#===============================================================================
