/**
 * 
 */
package info.riemannhypothesis.dixit.server.repository;

import info.riemannhypothesis.dixit.server.objects.Player;

import java.util.Collection;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public interface PlayerRepository {

    public boolean addPlayer(Player player);

    public Collection<Player> getPlayers();

    public Player getPlayer(long id);

}
