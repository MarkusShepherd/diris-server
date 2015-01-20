package info.riemannhypothesis.dixit.server.repository;

import info.riemannhypothesis.dixit.server.objects.Match;

import java.util.Collection;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public class MatchRepositoryImpl implements MatchRepository {

    private final Map<Long, Match> matches;

    public MatchRepositoryImpl() {
        matches = new ConcurrentHashMap<Long, Match>();
    }

    @Override
    public boolean addMatch(Match match) {
        return matches.put(match.getId(), match) == null;
    }

    @Override
    public Collection<Match> getMatches() {
        return matches.values();
    }

    @Override
    public Match getMatch(long id) {
        return matches.get(id);
    }

}
