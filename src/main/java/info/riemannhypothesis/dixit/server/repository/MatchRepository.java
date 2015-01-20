/**
 * 
 */
package info.riemannhypothesis.dixit.server.repository;

import info.riemannhypothesis.dixit.server.objects.Match;

import java.util.Collection;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public interface MatchRepository {

    public boolean addMatch(Match match);

    public Collection<Match> getMatches();

    public Match getMatch(long id);

}
