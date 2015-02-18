package info.riemannhypothesis.dixit.server.objects;

import java.util.ArrayList;
import java.util.List;

import javax.jdo.annotations.IdGeneratorStrategy;
import javax.jdo.annotations.PersistenceCapable;
import javax.jdo.annotations.Persistent;
import javax.jdo.annotations.PrimaryKey;

import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.Setter;

import com.google.appengine.api.datastore.Key;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Getter
@Setter
@EqualsAndHashCode(of = { "key" })
@PersistenceCapable
public class Player {

    @PrimaryKey
    @Persistent(valueStrategy = IdGeneratorStrategy.IDENTITY)
    private Key       key;

    @Persistent
    private String    name;

    @Persistent
    private String    email;

    @Persistent
    private List<Key> matchKeys;

    public Player() {
        this.matchKeys = new ArrayList<Key>();
    }

    public Player(String email, String name) {
        this();
        this.name = name;
        this.email = email;
    }

    public void addMatch(Match match) {
        matchKeys.add(match.getKey());
    }

    public void addMatch(Key mKey) {
        matchKeys.add(mKey);
    }

}
