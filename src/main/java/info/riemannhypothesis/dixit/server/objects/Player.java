package info.riemannhypothesis.dixit.server.objects;

import java.util.ArrayList;
import java.util.List;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public class Player {

    private long        id;

    private String      name;
    private String      email;

    private List<Match> matches;

    public Player() {
        //this.id = (long) (Math.random() * Long.MAX_VALUE);
        //this.matches = new ArrayList<Match>();
    }

    public Player(String email, String name) {
        this.id = (long) (Math.random() * Long.MAX_VALUE);
        this.name = name;
        this.email = email;
        this.matches = new ArrayList<Match>();
    }

    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email.toLowerCase();
    }

    public List<Match> getMatches() {
        return matches;
    }

    public void setMatches(List<Match> matches) {
        this.matches = matches;
    }

    @Override
    public int hashCode() {
        return email.hashCode();
    }

    @Override
    public final boolean equals(Object obj) {
        if (!(obj instanceof Player)) {
            return false;
        }
        Player that = (Player) obj;
        return this.email.equalsIgnoreCase(that.email);
    }

}
