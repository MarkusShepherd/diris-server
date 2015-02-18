package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.client.MatchServiceApi;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;
import info.riemannhypothesis.dixit.server.repository.JDOCrudRepository.Callback;
import info.riemannhypothesis.dixit.server.repository.MatchRepository;
import info.riemannhypothesis.dixit.server.repository.PlayerRepository;

import java.util.HashSet;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;

import com.google.appengine.api.datastore.Key;
import com.google.appengine.api.datastore.KeyFactory;

/**
 * @author Markus Schepke
 * @date 16 Feb 2015
 */
@Controller
public class MatchService implements MatchServiceApi {

    @Autowired
    private MatchRepository  matches;
    @Autowired
    private PlayerRepository players;

    @Override
    @RequestMapping(value = PATH, method = RequestMethod.POST, produces = "application/json")
    public @ResponseBody Match addMatch(@RequestBody Set<Long> pIds) {
        Set<Key> pKeys = new HashSet<Key>();

        for (long pId : pIds) {
            pKeys.add(KeyFactory.createKey("Player", pId));
        }

        Match match = new Match(pKeys);
        match = matches.save(match);

        final Key mKey = match.getKey();
        final Callback<Player> callback = new Callback<Player>() {
            @Override
            public void apply(Player player) {
                player.addMatch(mKey);
            }
        };

        for (Key pKey : pKeys) {
            players.update(pKey, callback);
        }

        return match;
    }

    @Override
    @RequestMapping(value = PATH, method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody Iterable<Match> getMatchList() {
        return matches.findAll();
    }

    @Override
    @RequestMapping(value = PATH + "/{id}", method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody Match getMatch(@PathVariable("id") long id) {
        return matches.findOne(KeyFactory.createKey("Match", id));
    }

}
