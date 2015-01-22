package info.riemannhypothesis.dixit.server.objects;

import java.util.ArrayList;
import java.util.List;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public class Player {

    private long       id;

    private String     name;
    private String     email;

    private List<Long> matchIds;

    public Player() {
        this.id = (long) (Math.random() * Long.MAX_VALUE);
        this.matchIds = new ArrayList<Long>();
    }

    public Player(String email, String name) {
        this();
        this.name = name;
        this.email = email;
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

    public List<Long> getMatchIds() {
        return matchIds;
    }

    public void setMatchIds(List<Long> matches) {
        this.matchIds = matches;
    }

    public void addMatch(Match match) {
        matchIds.add(match.getId());
    }

    public void addMatch(long matchId) {
        matchIds.add(matchId);
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
        return this.id == that.id;
    }

}
