package info.riemannhypothesis.dixit.server.repository;

import info.riemannhypothesis.dixit.server.objects.Match;

import org.springframework.stereotype.Service;

import com.google.appengine.api.datastore.Key;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Service
public class MatchRepository extends JDOCrudRepository<Match, Key> {

    public MatchRepository() {
        super(Match.class);
    }

}
