package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.client.PlayerServiceApi;
import info.riemannhypothesis.dixit.server.objects.Player;
import info.riemannhypothesis.dixit.server.repository.PlayerRepository;

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

    @Override
    @RequestMapping(value = PATH, method = RequestMethod.POST, produces = "application/json")
    public @ResponseBody Player addPlayer(@RequestBody Player player) {
        return players.save(player);
    }

    @Override
    @RequestMapping(value = PATH, method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody Iterable<Player> getPlayerList() {
        return players.findAll();
    }

    @Override
    @RequestMapping(value = PATH + "/id/{id}", method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody Player getPlayer(@PathVariable("id") long id) {
        return players.findOne(KeyFactory.createKey("Player", id));
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

}
