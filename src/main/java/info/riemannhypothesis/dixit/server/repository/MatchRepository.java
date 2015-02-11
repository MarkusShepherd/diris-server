package info.riemannhypothesis.dixit.server.repository;

import info.riemannhypothesis.dixit.server.objects.Match;

import java.util.Collection;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Service;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Service
public class MatchRepository {

    private final Map<Long, Match> matches;

    public MatchRepository() {
        matches = new ConcurrentHashMap<Long, Match>();
    }

    public boolean addMatch(Match match) {
        return matches.put(match.getId(), match) == null;
    }

    public Collection<Match> getMatches() {
        return matches.values();
    }

    public Match getMatch(long id) {
        return matches.get(id);
    }

}
