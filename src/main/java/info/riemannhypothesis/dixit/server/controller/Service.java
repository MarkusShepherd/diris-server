package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.client.ServiceApi;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;
import info.riemannhypothesis.dixit.server.repository.MatchRepository;
import info.riemannhypothesis.dixit.server.repository.PlayerRepository;

import java.util.Collection;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Controller
public class Service implements ServiceApi {

    @Autowired
    private PlayerRepository playerRepo;
    @Autowired
    private MatchRepository  matchRepo;

    @Override
    @RequestMapping(value = PLAYER_SVC_PATH, method = RequestMethod.GET)
    public @ResponseBody Collection<Player> getPlayerList() {
        return playerRepo.getPlayers();
    }

    @Override
    @RequestMapping(value = PLAYER_SVC_PATH + "/{id}", method = RequestMethod.GET)
    public @ResponseBody Player getPlayer(@PathVariable("id") long id) {
        return playerRepo.getPlayer(id);
    }

    @Override
    @RequestMapping(value = PLAYER_SVC_PATH, method = RequestMethod.POST)
    public @ResponseBody boolean addPlayer(@RequestBody Player player) {
        return playerRepo.addPlayer(player);
    }

    @Override
    @RequestMapping(value = MATCH_SVC_PATH, method = RequestMethod.GET)
    public @ResponseBody Collection<Match> getMatchList() {
        return matchRepo.getMatches();
    }

    @Override
    @RequestMapping(value = MATCH_SVC_PATH + "/{id}", method = RequestMethod.GET)
    public @ResponseBody Match getMatch(@PathVariable("id") long id) {
        return matchRepo.getMatch(id);
    }

    @Override
    @RequestMapping(value = MATCH_SVC_PATH, method = RequestMethod.POST)
    public @ResponseBody long addMatch(@RequestBody long[] ids) {
        Player[] players = new Player[ids.length];
        for (int i = 0; i < players.length; i++) {
            players[i] = playerRepo.getPlayer(ids[i]);
        }
        Match match = new Match(players);
        matchRepo.addMatch(match);
        return match.getId();
    }
}
