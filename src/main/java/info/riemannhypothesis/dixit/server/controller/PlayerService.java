package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.client.PlayerServiceApi;
import info.riemannhypothesis.dixit.server.objects.Player;
import info.riemannhypothesis.dixit.server.repository.PlayerRepository;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;

import com.google.appengine.api.datastore.Key;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Controller
public class PlayerService implements PlayerServiceApi {

    @Autowired
    private PlayerRepository players;

    @Override
    @RequestMapping(value = PATH, method = RequestMethod.POST)
    public @ResponseBody Player addPlayer(@RequestBody Player player) {
        return players.save(player);
    }

    @Override
    @RequestMapping(value = PATH, method = RequestMethod.GET)
    public @ResponseBody Iterable<Player> getPlayerList() {
        return players.findAll();
    }

    @Override
    @RequestMapping(value = PATH + "/{key}", method = RequestMethod.GET)
    public @ResponseBody Player getPlayer(@PathVariable("key") Key key) {
        return players.findOne(key);
    }

}
