package info.riemannhypothesis.dixit.server.repository;

import info.riemannhypothesis.dixit.server.objects.Player;

import java.util.Collection;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public class PlayerRepositoryImpl implements PlayerRepository {

    private final Map<Long, Player> players;

    public PlayerRepositoryImpl() {
        players = new ConcurrentHashMap<Long, Player>();
    }

    @Override
    public boolean addPlayer(Player player) {
        return players.put(player.getId(), player) == null;
    }

    @Override
    public Collection<Player> getPlayers() {
        return players.values();
    }

    @Override
    public Player getPlayer(long id) {
        return players.get(id);
    }

}
