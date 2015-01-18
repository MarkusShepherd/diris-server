package info.riemannhypothesis.dixit.server;

import java.util.Collection;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public class Player {

    private long              id;

    private String            name;
    private String            email;

    private Collection<Match> matches;

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

    public Collection<Match> getMatches() {
        return matches;
    }

    public void setMatches(Collection<Match> matches) {
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
