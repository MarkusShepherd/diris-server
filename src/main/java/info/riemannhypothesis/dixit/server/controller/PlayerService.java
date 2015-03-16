package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.client.PlayerServiceApi;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;
import info.riemannhypothesis.dixit.server.repository.MatchRepository;
import info.riemannhypothesis.dixit.server.repository.PlayerRepository;

import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedList;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;

import com.google.appengine.api.datastore.KeyFactory;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Controller
public class PlayerService implements PlayerServiceApi {

    @Autowired
    private PlayerRepository players;
    @Autowired
    private MatchRepository  matches;

    @Override
    @RequestMapping(value = PATH, method = RequestMethod.POST, produces = "application/json")
    public @ResponseBody Player addPlayer(@RequestBody Player player) {
        return players.save(player);
    }

    @Override
    @RequestMapping(value = PATH, method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody List<Player> getPlayerList() {
        return players.findAll();
    }

    @Override
    @RequestMapping(value = PATH + "/id/{id}", method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody Player getPlayerById(@PathVariable("id") long id) {
        return players.findById(KeyFactory.createKey("Player", id));
    }

    @Override
    @RequestMapping(value = PATH + "/email/{email}", method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody Player getPlayerByEmail(
            @PathVariable("email") String email) {
        final List<Player> list = players.findByField("email", email);
        if (list.size() > 0)
            return list.get(0);
        else
            return null;
    }

    @Override
    @RequestMapping(value = PATH + "/name/{name}", method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody List<Player> getPlayerByName(
            @PathVariable("name") String name) {
        return players.findByField("name", name);
    }

    @Override
    @RequestMapping(value = PATH + "/id/{id}/matches", method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody List<Match> getPlayerMatches(
            @PathVariable("id") long id) {
        Player player = getPlayerById(id);
        if (player == null)
            return new LinkedList<Match>();
        Collection<Match> m = matches.findByIds(player.getMatchKeys());
        return new ArrayList<Match>(m);
    }

    private List<Match> getPlayerMatchesByStatus(long id, Match.Status status) {
        // TODO use query filter instead
        List<Match> list = getPlayerMatches(id);
        List<Match> result = new ArrayList<Match>(list.size());

        for (Match match : list) {
            if (match.getStatus() == status)
                result.add(match);
        }

        return result;
    }

    @Override
    @RequestMapping(value = PATH + "/id/{id}/matches/{status}", method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody List<Match> getPlayerMatches(
            @PathVariable("id") long id, @PathVariable("status") String status) {
        if ("waiting".equals(status))
            return getPlayerMatchesByStatus(id, Match.Status.WAITING);
        else if ("inprogress".equals(status))
            return getPlayerMatchesByStatus(id, Match.Status.IN_PROGRESS);
        else if ("finished".equals(status))
            return getPlayerMatchesByStatus(id, Match.Status.FINISHED);
        else
            throw new IllegalArgumentException("Unknown status: " + status);
    }

}
