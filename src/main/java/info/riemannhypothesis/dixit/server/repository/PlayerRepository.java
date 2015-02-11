package info.riemannhypothesis.dixit.server.repository;

import info.riemannhypothesis.dixit.server.objects.Player;

import java.util.Collection;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Service;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Service
public class PlayerRepository {

    private final Map<Long, Player> players;

    public PlayerRepository() {
        players = new ConcurrentHashMap<Long, Player>();
    }

    public boolean addPlayer(Player player) {
        return players.put(player.getId(), player) == null;
    }

    public Collection<Player> getPlayers() {
        return players.values();
    }

    public Player getPlayer(long id) {
        return players.get(id);
    }

}
