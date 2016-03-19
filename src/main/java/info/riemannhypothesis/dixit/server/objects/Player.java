package info.riemannhypothesis.dixit.server.objects;

import info.riemannhypothesis.dixit.server.Application;
import info.riemannhypothesis.dixit.server.util.Utils;

import java.text.ParseException;
import java.util.ArrayList;
import java.util.Date;
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
    private String    externalID;

    @Persistent
    private String    name;

    @Persistent
    private String    email;

    @Persistent
    private String    avatarURL;

    @Persistent
    private List<Key> matchKeys;

    @Persistent
    private String    created;
    @Persistent
    private String    lastModified;

    public Player() {
        this.matchKeys = new ArrayList<Key>();
        final String now = Utils.now();
        created = now;
        lastModified = now;
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

    public Date getCreatedDate() {
        try {
            return Application.DATE_FORMATTER.parse(created);
        } catch (ParseException e) {
            e.printStackTrace(System.err);
            return null;
        }
    }

    public Date getLastModifiedDate() {
        try {
            return Application.DATE_FORMATTER.parse(lastModified);
        } catch (ParseException e) {
            e.printStackTrace(System.err);
            return null;
        }
    }
}
