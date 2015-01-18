/**
 * 
 */
package info.riemannhypothesis.dixit.server.repository;

import info.riemannhypothesis.dixit.server.Player;

import java.util.Collection;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public interface PlayerRepository {

    // Add a video
    public boolean addPlayer(Player player);

    // Get the videos that have been added so far
    public Collection<Player> getPlayers();

    public Player getPlayer(long id);

}
