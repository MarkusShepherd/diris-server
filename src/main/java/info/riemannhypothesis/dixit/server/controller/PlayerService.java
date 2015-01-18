package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.client.PlayerServiceApi;
import info.riemannhypothesis.dixit.server.objects.Player;
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
public class PlayerService implements PlayerServiceApi {

    @Autowired
    private PlayerRepository players;

    @Override
    @RequestMapping(value = PlayerServiceApi.PLAYER_SVC_PATH, method = RequestMethod.GET)
    public @ResponseBody Collection<Player> getPlayerList() {
        return players.getPlayers();
    }

    @Override
    @RequestMapping(value = PlayerServiceApi.PLAYER_SVC_PATH + "/{id}", method = RequestMethod.GET)
    public @ResponseBody Player getPlayer(@PathVariable("id") long id) {
        return players.getPlayer(id);
    }

    @Override
    @RequestMapping(value = PlayerServiceApi.PLAYER_SVC_PATH, method = RequestMethod.POST)
    public @ResponseBody boolean addPlayer(@RequestBody Player player) {
        return players.addPlayer(player);
    }

}
