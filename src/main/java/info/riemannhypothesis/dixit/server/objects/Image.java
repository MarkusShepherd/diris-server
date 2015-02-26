package info.riemannhypothesis.dixit.server.objects;

import info.riemannhypothesis.dixit.server.Application;
import info.riemannhypothesis.dixit.server.util.Utils;

import java.net.URL;
import java.text.ParseException;
import java.util.Date;

import javax.jdo.annotations.IdGeneratorStrategy;
import javax.jdo.annotations.PersistenceCapable;
import javax.jdo.annotations.Persistent;
import javax.jdo.annotations.PrimaryKey;

import lombok.Getter;
import lombok.Setter;

import com.google.appengine.api.datastore.Key;
import com.google.appengine.api.datastore.KeyFactory;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Getter
@Setter
@PersistenceCapable
public class Image {

    @PrimaryKey
    @Persistent(valueStrategy = IdGeneratorStrategy.IDENTITY)
    private Key    key;

    @Persistent
    private Key    playerKey;

    @Persistent
    private URL    url;

    @Persistent
    private String created;
    @Persistent
    private String lastModified;

    public Image() {
        final String now = Utils.now();
        created = now;
        lastModified = now;
    }

    public Image(URL url) {
        this();
        this.url = url;
    }

    public Image(Key playerKey) {
        this();
        this.playerKey = playerKey;
    }

    public Image(long playerId) {
        this(KeyFactory.createKey("Player", playerId));
    }

    public Image(URL url, Key playerKey) {
        this(playerKey);
        this.url = url;
    }

    public Image(URL url, long playerId) {
        this(playerId);
        this.url = url;
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
